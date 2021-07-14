# Copyright 2020 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import io
import os
import sys
import time
import lzma
import builtins
import _compression

from lzma import compress, decompress

Compressor = lzma.LZMACompressor
Decompressor = lzma.LZMADecompressor

class TailingDecompressReader(_compression.DecompressReader):

    def __init__(self, *args, **kwargs):
        self._tail = kwargs.pop("tail", True)
        self._tail_sleep = float(kwargs.pop("tail_sleep", 0.15))
        # default compressed file marker '.7zXZ'
        self._COMPRESSED_FILE_MARKER = b"\xfd\x37\x7a\x58\x5a"
        # default uncompressed file marker is start of the message
        self._UNCOMPRESSED_FILE_MARKER = "{\"message_keyword\"".encode("utf-8")

        super(TailingDecompressReader, self).__init__(*args, **kwargs)

    def read(self, size=-1, _tail_sleep=0.15):
        if size < 0:
            return self.readall()

        if not size or self._eof:
            return b""
        data = None  # Default if EOF is encountered
        # Depending on the input data, our call to the decompressor may not
        # return any data. In this case, try again after reading another block.
        while True:
            if self._decompressor.eof:
                self.rawblock = (self._decompressor.unused_data or
                            self._fp.read1(_compression.BUFFER_SIZE))
                if not self.rawblock:
                    if not self._tail:
                        break
                    time.sleep(self._tail_sleep)
                    continue
                # Continue to next stream.
                self._decompressor = self._decomp_factory(
                    **self._decomp_args)
                try:
                    data = self._decompressor.decompress(self.rawblock, size)
                except self._trailing_error:
                    # Trailing data isn't a valid compressed stream; ignore it.
                    break
            else:
                if self._decompressor.needs_input:
                    self.rawblock = self._fp.read1(_compression.BUFFER_SIZE)
                    if not self.rawblock:
                        if not self._tail:
                            break
                        time.sleep(self._tail_sleep)
                        continue
                else:
                    self.rawblock = b""
                try:
                    data = self._decompressor.decompress(self.rawblock, size)
                except lzma.LZMAError as e:
                    # try to find valid compressed block by looking for the compressed file marker
                    # or determine that file is not compressed by finding uncompressed file marker
                    if "Input format not supported by decoder" in str(e):
                        while True:
                            raw_data = self._fp.read1(65536)
                            # abort on EOF if not tailing
                            if not raw_data:
                                if not self._tail:
                                    raise
                            self.rawblock += raw_data
                            # try to find compressed file marker
                            compressed_file_marker_idx = self.rawblock.find(self._COMPRESSED_FILE_MARKER)
                            if compressed_file_marker_idx >= 0:
                                self.rawblock = self.rawblock[compressed_file_marker_idx:]
                                break
                            # try to find uncompressed file marker
                            uncompressed_file_marker_idx = self.rawblock.find(self._UNCOMPRESSED_FILE_MARKER)
                            if uncompressed_file_marker_idx >= 0:
                                self.rawblock = self.rawblock[uncompressed_file_marker_idx:]
                                raise
                        # decompress compressed raw block that we found
                        self._decompressor = self._decomp_factory(**self._decomp_args)
                        return self._decompressor.decompress(self.rawblock, size)
            if data:
                break

        if not data:
            self._eof = True
            self._size = self._pos
            return b""
        self._pos += len(data)
        return data


class CompressedFile(lzma.LZMAFile):
    def __init__(self, filename=None, mode="r", *,
            format=None, check=-1, preset=None, filters=None, tail=False):
        self._fp = None
        self._closefp = False
        self._mode = lzma._MODE_CLOSED
        self._raw_mode = False
        self._tail = tail

        if mode in ("r", "rb"):
            if check != -1:
                raise ValueError("Cannot specify an integrity check "
                                 "when opening a file for reading")
            if preset is not None:
                raise ValueError("Cannot specify a preset compression "
                                 "level when opening a file for reading")
            if format is None:
                format = lzma.FORMAT_AUTO
            mode_code = lzma._MODE_READ
        elif mode in ("w", "wb", "a", "ab", "x", "xb"):
            if format is None:
                format = lzma.FORMAT_XZ
            mode_code = lzma._MODE_WRITE
            self._compressor = lzma.LZMACompressor(format=format, check=check,
                preset=preset, filters=filters)
            self._pos = 0
        else:
            raise ValueError("Invalid mode: {!r}".format(mode))

        if filename is sys.stdin.buffer:
            self._fp = filename
            self._closefp = False
            self._mode = mode_code
        elif isinstance(filename, (str, bytes, os.PathLike)):
            if "b" not in mode:
                mode += "b"
            self._fp = builtins.open(filename, mode)
            self._closefp = True
            self._mode = mode_code
        elif hasattr(filename, "read") or hasattr(filename, "write"):
            self._fp = filename
            self._mode = mode_code
        else:
            raise TypeError("filename must be a str, bytes, file or PathLike object")

        if self._mode == lzma._MODE_READ:
            self.raw = TailingDecompressReader(self._fp, lzma.LZMADecompressor,
                trailing_error=lzma.LZMAError, format=format, filters=filters, tail=self._tail)
            self._buffer = io.BufferedReader(self.raw)

    @property
    def name(self):
        return getattr(self._fp, "name", None)

    def read(self, size=-1):
        self._check_can_read()
        if self._raw_mode:
            return self._fp.read(size)
        try:
            return self._buffer.read(size)
        except lzma.LZMAError as e:
            # fall back to raw mode if we can't decompress data
            if "Input format not supported by decoder" in str(e):
                self._raw_mode = True
                return self.raw.rawblock
            raise

    def read1(self, size=-1):
        self._check_can_read()
        if size < 0:
            size = io.DEFAULT_BUFFER_SIZE
        if self._raw_mode:
            return self._fp.read1(size)
        try:
            return self._buffer.read1(size)
        except lzma.LZMAError as e:
            # fall back to raw mode if we can't decompress data
            if "Input format not supported by decoder" in str(e):
                self._raw_mode = True
                return self.raw.rawblock
            raise