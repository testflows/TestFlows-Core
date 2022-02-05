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
import os
import sys
import uuid
import types
import atexit
import inspect
import traceback
import threading

from typing import Optional

from testflows._core.contrib import cloudpickle

from testflows._core.contrib.aiomsg import Socket
from testflows._core.exceptions import exception as get_exception

from .asyncio import asyncio

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
        self.loop = loop or asyncio.get_running_loop()
        self.in_socket = Socket(loop=self.loop)
        self.out_socket = Socket(loop=self.loop)
        self.address = address if address is not None else ("127.0.0.1", 0)
        self.connections = {}
        self.request_tasks = []
        self.serve_tasks = []
        self.reply_events = {}
        self.objects = {}
        self.open = False
        self.lock = asyncio.Lock(loop=self.loop)

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

    def register(self, obj, sync=None):
        """Register object with the service to be
        by remote services.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _async_register(sync: bool=False):
            async with self.lock:
                if not self.open:
                    raise ServiceError("service is not running")
                
                _id = id(obj)

                if _id not in self.objects:
                    self.objects[_id] = obj

                if sync:
                    return ServiceObject(obj, address=self.address)
                return AsyncServiceObject(obj, address=self.address)

        if loop is None:
             return asyncio.run_coroutine_threadsafe(_async_register(sync=True), loop=self.loop).result()
        elif loop is not self.loop:
            return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_async_register(sync=sync), loop=self.loop))
        else:
            return _async_register(sync=sync)

    async def unregister(self, obj):
        """Unregister object from the service to stop
        providing object to remote services.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _async_unregister():
            async with self.lock:
                _id = id(obj)

                if _id in self.objects:
                    del self.objects[id(obj)]
        
        if loop is None:
            return asyncio.run_coroutine_threadsafe(_async_unregister(), loop=self.loop).result()
        elif loop is not self.loop:
            return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_async_unregister(), loop=self.loop))
        else:
            return _async_unregister()

    async def _connect(self, service_object):
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
   
    def __enter__(self):
        """Sync context manager enter.
        """
        return asyncio.run_coroutine_threadsafe(self.__aenter__(), loop=self.loop).result()

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Sync context manager exit.
        """
        return asyncio.run_coroutine_threadsafe(self.__aexit__(exc_type, exc_value, exc_tb), loop=self.loop).result()

    async def __aenter__(self):
        """Async context manager enter.
        """
        async with self.lock:
            await self.in_socket.bind(hostname=self.hostname, port=self.port)
            self.address = self.in_socket.bind_address
            self.loop.create_task(self._serve_forever())
            self.open = True
            return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Async context manager exit.
        """
        async with self.lock:
            try:
                while self.request_tasks:
                    task = self.request_tasks.pop()
                    await task
                while self.serve_tasks:
                    task = self.serve_tasks.pop()
                    task.cancel()
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
                def r():
                    return getattr(self.objects[oid], fn)(*args, **kwargs)
                if fn == "__getattribute__":
                    r = getattr(self.objects[oid], *args)
                elif fn == "__setattribute__":
                    r = setattr(self.objects[oid], *args)
                else:
                    r = await self.loop.run_in_executor(None, r)
                if asyncio.iscoroutine(r):
                    r = await r
            except BaseException as e:
                msg_type = self.MsgTypes.REPLY_EXCEPTION
                exc_type, exc_value, exc_tb = sys.exc_info()
                r = exc_type(str(exc_value) + "\n\nService Traceback (most recent call last):\n" + "".join(traceback.format_tb(exc_tb)).rstrip())
            try:
                await self.in_socket.send_pickle((msg_type, rid, r), identity=identity)
            except TypeError as e:
                _r = await self.register(r, sync=True)
                await self.in_socket.send_pickle((msg_type, rid, _r), identity=identity)

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

        self.serve_tasks.append(
                self.in_socket.loop.create_task(_serve_requests())
            )
        self.serve_tasks.append(
                self.out_socket.loop.create_task(_serve_replies())
            )


# global process wide service
_process_service = None


def process_service(**kwargs):
    """Get or create global process wide object service.
    """
    global _process_service

    if _process_service is None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = kwargs.pop("loop", None)

            if loop is None:
                loop = asyncio.new_event_loop()

                def run_event_loop():
                    asyncio.set_event_loop(loop)
                    loop.run_forever()

                thread = threading.Thread(target=run_event_loop, daemon=True)

                def stop_event_loop():
                    loop.call_soon_threadsafe(loop.stop)
                    thread.join()

                thread.start()
                atexit.register(stop_event_loop)

            kwargs["loop"] = loop

        kwargs["name"] = kwargs.get("name", f"process-service-{os.getpid()}")

        _process_service = Service(**kwargs)

    return _process_service


def reset_process_service():
    """Reset global process service.
    """
    global _process_service
    _process_service = None


class BaseServiceObject:
    """Base class for all service objects.

    :param oid: object id
    :param address: address `tuple(hostname, port)`
    """
    _exposed = None
    _typename = None

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

    async def __async_proxy_call__(self, fn, args=None, kwargs=None):
        """Execute function call on the remote service.
        """
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        process_service_loop = _process_service.loop

        async def wrap(c):
            """Wrap coroutine that is running in another event loop.
            """
            if asyncio.get_event_loop() is not process_service_loop:
                return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(c, loop=process_service_loop))
            return await c

        send = await wrap(_process_service._connect(self))

        response = await wrap(send(uuid.uuid1().bytes, self.oid, fn, args, kwargs, resp=True))

        await wrap(response.wait())
        reply_type, reply_body = response.message

        if reply_type == Service.MsgTypes.REPLY_EXCEPTION:
            if isinstance(reply_body, (SystemExit, KeyboardInterrupt)):
                reply_body = RuntimeError(f"{reply_body.__class__}: {reply_body}")
            raise reply_body

        return reply_body

    def __proxy_call__(self, fn, args=None, kwargs=None):
        """Synchronously execute function call on the remote service.
        """
        return asyncio.run_coroutine_threadsafe(self.__async_proxy_call__(fn, args, kwargs), loop=_process_service.loop).result()

    def __reduce__(self):
        """Make service object serializable.
        """
        return (RebuildServiceObject, (self._typename, self._exposed, self.oid, self.address))


class AsyncBaseServiceObject(BaseServiceObject):
    """Async base service object.
    """
    def __reduce__(self):
        """Make service object serializable.
        """
        return (RebuildAsyncServiceObject, (self._typename, self._exposed, self.oid, self.address))


def RebuildServiceObject(typename, exposed, oid, address):
    """Rebuild service object during unpickling.
    """
    return ServiceObjectType(typename, exposed)(oid=oid, address=address)


def RebuildAsyncServiceObject(typename, exposed, oid, address):
    """Rebuild async service object during unpickling.
    """
    return ServiceObjectType(typename, exposed, _async=True)(oid=oid, address=address)


def ServiceObjectType(typename, expose, _async=False):
    """Make service object type.
    """
    _attrs = {}

    for name in expose["methods"]:
        exec(f"{'async ' if _async else ''}def {name}(self, *args, **kwargs):\n"
                f"    return self.__{'async_' if _async else ''}proxy_call__(\"{name}\", args, kwargs)",
            _attrs)

    for name in expose["properties"]:
        exec(f"@property\n"
                f"{'async ' if _async else ''}def {name}(self):\n"
                f"    return self.__{'async_' if _async else ''}proxy_call__(\"__getattribute__\", [\"{name}\"])"
                f"\n"
                f"@{name}.setter\n"
                f"{'async ' if _async else ''}def {name}(self, v):\n"
                f"    return self.__{'async_' if _async else ''}proxy_call__(\"__setattribute__\", [\"{name}\", v])",
            _attrs)

    base = AsyncBaseServiceObject if _async else BaseServiceObject

    service_type = type(f"{'Async' if _async else ''}ServiceObject[{typename}]", (base,), _attrs)
    service_type._exposed = expose
    service_type._typename = typename

    return service_type


def auto_expose(obj):
    """Auto expose all public methods and properties of an object.
    """
    exposed = {
        "methods": [],
        "properties": []
    }

    for name, value in inspect.getmembers(obj):
        if name.startswith("_"):
            continue

        if type(value) in [types.MethodWrapperType, types.MethodType, types.BuiltinMethodType]:
            exposed["methods"].append(name)
        else:
            exposed["properties"].append(name)

    return exposed


def AsyncServiceObject(obj, address, expose=None):
    """Make async service object.
    """
    _id = id(obj)

    return ServiceObjectType(f"{type(obj)}@{_id}", expose or auto_expose(obj), _async=True)(oid=_id, address=address)


def ServiceObject(obj, address, expose=None):
    """Make service object.
    """
    _id = id(obj)

    return ServiceObjectType(f"{type(obj)}@{_id}", expose or auto_expose(obj))(oid=_id, address=address)
