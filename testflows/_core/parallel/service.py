# Copyright 2022 Katteli Inc.
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
import sys
import uuid
import asyncio
import inspect
from re import I
import threading
import traceback

from typing import Optional

from numpy import identity
from testflows._core.contrib import cloudpickle

from testflows._core.contrib.aiomsg import Socket


class ServiceError(Exception):
    """Service error.
    """
    pass


class Service:
    """Remote object service that provides remote
    access to local objects and connects to other
    remote services to access their remote objects.

    :param name: name of the service
    :param address: (optional) address of the server, default: (127.0.0.1, 0)
    :param loop: (optional) event loop ,default: None
    """
    class MsgTypes:
        REPLY_RESULT = b'0'
        REPLY_EXCEPTION = b'1'
        REQUEST = b'2'

    def __init__(self, name, address=None, loop=None):
        self.name = name
        self.loop = loop or asyncio.get_event_loop()
        self.in_socket = Socket(loop=self.loop)
        self.out_socket = Socket(loop=self.loop)
        self.address = address if address is not None else ("127.0.0.1", 0)
        self.connections = {}
        self.request_tasks = []
        self.reply_events = {}
        self.objects = {}
        self.open = False
        self.lock = asyncio.Lock()

    @property
    def hostname(self) -> str:
        """Return service hostname.
        """
        return self.address[0]

    @property
    def port(self) -> Optional[int]:
        """Retrun service port.
        """
        if len(self.address) < 2:
            return None
        return self.address[-1]

    async def register(self, obj):
        """Register object with the service to be
        by remote services.
        """
        async with self.lock:
            if not self.open:
                raise ServiceError("service is not running")
            
            _id = id(obj)

            if _id not in self.objects:
                self.objects[_id] = obj

            return ServiceObject(obj, address=self.address)

    async def unregister(self, obj):
        """Unregister object from the service to stop
        providing object to remote services.
        """
        async with self.lock:
            _id = id(obj)

            if _id in self.objects:
                del self.objects[id(obj)]

    async def connect(self, service_object):
        """Connect to the remote service that provides
        access to the remote object.
        """
        address = service_object.address
        
        async def send(rid, oid, fn, args, kwargs, resp=True):
            """Send sevice object request to remote service.
            """
            await self.connections[address].wait()
            await self.out_socket.send_pickle(
                    obj=(self.MsgTypes.REQUEST, rid, (oid, fn, args, kwargs)),
                    identity=self.connections[address].identity
                )

            if resp:
                event = asyncio.Event()
                self.reply_events[rid] = event
                return event

        async with self.lock:
            if not self.open:
                raise ServiceError("service is not running")

            if not address in self.connections:
                event = asyncio.Event()
                await self.out_socket.connect(service_object.hostname, service_object.port, event=event)
                self.connections[address] = event
        
        return send
   
    async def __aenter__(self):
        """Context manager enter.
        """
        async with self.lock:
            await self.in_socket.bind(hostname=self.hostname, port=self.port)
            self.address = self.in_socket.bind_address
            self.in_socket.loop.create_task(self._serve_forever())
            self.open = True
            return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Context manager exit.
        """
        async with self.lock:
            try:
                while self.request_tasks:
                    task = self.request_tasks.pop()
                    await task
                await self.out_socket.close()
                await self.in_socket.close()
            finally:
                self.open = False

    async def _process_message(self, identity, message):
        """Process received message.
        """
        msg_type, rid, msg_body = cloudpickle.loads(message)

        if msg_type == self.MsgTypes.REQUEST:
            # process request
            oid, fn, args, kwargs = msg_body
            msg_type = self.MsgTypes.REPLY_RESULT
            try:
                r = getattr(self.objects[oid], fn)(*args, **kwargs)
            except BaseException as e:
                msg_type = self.MsgTypes.REPLY_EXCEPTION
                exc_type, exc_value, exc_tb = sys.exc_info()
                r = exc_type(str(exc_value) + "\n\nService Traceback (most recent call last):\n" + "\n".join(traceback.format_tb(exc_tb)).rstrip())

            await self.in_socket.send_pickle((msg_type, rid, r), identity=identity)
        else:
            # process reply
            reply_event = self.reply_events.pop(rid)
            reply_event.message = msg_type, msg_body
            reply_event.set()

    async def _serve_forever(self):
        """Start service until coroutine is cancelled.
        """
        async def _serve_requests():
            while True:
                identity, message = await self.in_socket.recv_identity()
                self.in_socket.loop.create_task(self._process_message(identity, message))

        async def _serve_replies():
            while True:
                identity, message = await self.out_socket.recv_identity()
                self.out_socket.loop.create_task(self._process_message(identity, message))

        self.in_socket.loop.create_task(_serve_requests())
        self.out_socket.loop.create_task(_serve_replies())


# global process wide service
_process_service = None

def create_process_service(*args, **kwargs):
    """Create global process wide object service.
    """
    global _process_service

    if _process_service is None:
        _process_service = Service(*args, **kwargs)
    return _process_service

class BaseServiceObject:
    """Base class for all service objects.

    :param oid: object id
    :param address: address `tuple(hostname, port)`
    """
    def __init__(self, oid, address) -> None:
        self.oid = oid
        self.address = address

    def __eq__(self, other: object) -> bool:
        return other.oid == self.oid and other.address == self.address 

    @property
    def hostname(self) -> str:
        """Return remote service hostname.
        """
        return self.address[0]

    @property
    def port(self) -> Optional[int]:
        """Return remote service port.
        """
        if len(self.address) < 2:
            return None
        return self.address[-1]

    async def __proxy_call__(self, fn, args=None, kwargs=None):
        """Execute function call on the remote service.
        """
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        async def wrap(c):
            """Wrap coroutine that is running in another event loop.
            """
            if asyncio.get_event_loop() is not _process_service.loop:
                return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(c, loop=_process_service.loop))
            return await c

        send = await wrap(_process_service.connect(self))

        response = await wrap(send(uuid.uuid1().bytes, self.oid, fn, args, kwargs, resp=True))
        await wrap(response.wait())
        reply_type, reply_body = response.message

        if reply_type == Service.MsgTypes.REPLY_EXCEPTION:
            raise reply_body

        return reply_body


def ServiceObject(obj, address):
    """Make service object.
    """
    _id = id(obj)
    _attrs = {}

    for name, value in inspect.getmembers(obj):
        if name.startswith("_"):
            continue

        if callable(value):
            exec(f"async def {name}(self, *args, **kwargs):\n"
                 f"    return await self.__proxy_call__(\"{name}\", args, kwargs)",
                _attrs)
        else:
            exec(f"@property\n"
                 f"async def {name}(self):\n"
                 f"    return await self.__proxy_call__(\"__getattribute__\", \"{name}\")",
                _attrs)

    return type(f"ServiceObject[{type(obj)}@{_id}]", (BaseServiceObject,), _attrs)(oid=_id, address=address)