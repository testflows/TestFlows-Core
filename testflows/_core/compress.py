# Copyright 2020 Katteli Inc.
# TestFlows Test Framework (http://testflows.com)
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
import lzma
import builtins
import _compression

class TrailingDecompressReader(_compression.DecompressReader):
    def read(self, size=-1):
        if size < 0:
            return self.readall()

        if not size or self._eof:
            return b""
        data = None  # Default if EOF is encountered
        # Depending on the input data, our call to the decompressor may not
        # return any data. In this case, try again after reading another block.
        while True:
            if self._decompressor.eof:
                rawblock = (self._decompressor.unused_data or
                            self._fp.read(_compression.BUFFER_SIZE))
                if not rawblock:
                    continue
                # Continue to next stream.
                self._decompressor = self._decomp_factory(
                    **self._decomp_args)
                try:
                    data = self._decompressor.decompress(rawblock, size)
                except self._trailing_error:
                    # Trailing data isn't a valid compressed stream; ignore it.
                    break
            else:
                if self._decompressor.needs_input:
                    rawblock = self._fp.read(_compression.BUFFER_SIZE)
                    if not rawblock:
                        continue
                else:
                    rawblock = b""
                data = self._decompressor.decompress(rawblock, size)
            if data:
                break
        if not data:
            self._eof = True
            self._size = self._pos
            return b""
        self._pos += len(data)
        return data


class LogFileReader(lzma.LZMAFile):
    def __init__(self, filename=None, mode="r", *,
            format=None, check=-1, preset=None, filters=None):
        self._fp = None
        self._closefp = False
        self._mode = lzma._MODE_CLOSED

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

        if isinstance(filename, (str, bytes, os.PathLike)):
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
            raw = TrailingDecompressReader(self._fp, lzma.LZMADecompressor,
                trailing_error=lzma.LZMAError, format=format, filters=filters)
            self._buffer = io.BufferedReader(raw)

    def readline(self, size=-1):
        return super(LogFileReader, self).readline(size=size).decode("utf-8")
