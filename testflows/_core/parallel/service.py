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

from collections import namedtuple
from typing import Optional
from multiprocessing.util import Finalize

from testflows._core.contrib import cloudpickle
from testflows._core.contrib.aiomsg import Socket
from testflows._core.exceptions import exception as get_exception

from .asyncio import asyncio, is_running_in_event_loop, CancelledError


Address = namedtuple("address", "hostname port", defaults=(None,))

TimeoutError = asyncio.exceptions.TimeoutError


class ServiceError(Exception):
    """Service error.
    """
    pass


class ServiceNotRunningError(ServiceError):
    """Service not running error.
    """
    pass


class ServiceObjectNotFoundError(ServiceError):
    """Service object not found error.
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
        """Service protocol message types.
        """
        REPLY_RESULT = b'0'
        REPLY_EXCEPTION = b'1'
        REQUEST = b'2'


    class ObjectItem:
        """Service object item.
        """
        def __init__(self, obj, refcount=0):
            self.obj = obj
            self.refcount = refcount

    def __init__(self, name, address=None, loop=None):
        """Initialize process service.
        """
        self.name = name
        self.loop = loop or asyncio.get_running_loop()
        self.in_socket = Socket(loop=self.loop)
        self.out_socket = Socket(loop=self.loop)
        self.address = address if address is not None else Address("127.0.0.1", 0)
        self.connections = {}
        self.request_tasks = []
        self.serve_tasks = []
        self.reply_events = {}
        self.objects = {}
        self.open = False
        self.lock = asyncio.Lock(loop=self.loop)

    def register(self, obj, sync=None, expose=None):
        """Register object with the service to be by remote services.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _async_register(sync: bool=False):
            async with self.lock:
                if not self.open:
                    raise ServiceNotRunningError("service is not running")
                
                _id = id(obj)

                if _id not in self.objects:
                    self.objects[_id] = Service.ObjectItem(obj)

            if sync:
                return ServiceObject(obj, address=self.address, expose=expose)
            return AsyncServiceObject(obj, address=self.address, expose=expose)

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

    async def _connect(self, address):
        """Connect to the remote service that provides
        access to the remote object.
        """
        async def local_send(rid, oid, fn, args, kwargs, resp=True, timeout=None):
            """Send service object request to the local service.
            """
            msg_type, msg_body = await self._exec(oid, fn, args, kwargs)

            if resp:
                event = asyncio.Event()
                event.message = msg_type, msg_body
                event.set()
                return event

        async def send(rid, oid, fn, args, kwargs, resp=True, timeout=None):
            """Send sevice object request to remote service.
            """
            await asyncio.wait_for(self.connections[address].wait(), timeout=timeout)

            await asyncio.wait_for(self.out_socket.send_pickle(
                    obj=(self.MsgTypes.REQUEST, rid, (oid, fn, args, kwargs)),
                    identity=self.connections[address].identity
                ), timeout=timeout)

            if resp:
                event = asyncio.Event()
                self.reply_events[rid] = event
                return event

        async with self.lock:
            if not self.open:
                raise ServiceNotRunningError("service is not running")
            
            if address == self.address:
                return local_send

            if not address in self.connections:
                event = asyncio.Event()
                await self.out_socket.connect(address.hostname, address.port, event=event)
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
            await self.in_socket.bind(hostname=self.address.hostname, port=self.address.port)
            self.address = Address(*self.in_socket.bind_address)
            self.loop.create_task(self._serve_forever())
            self.open = True
            return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Async context manager exit.
        """
        async with self.lock:
            try:
                self.objects = {}
                while self.request_tasks:
                    task = self.request_tasks.pop()
                    await task
                while self.serve_tasks:
                    task = self.serve_tasks.pop()
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                await self.out_socket.close()
                await self.in_socket.close()
            finally:
                self.open = False

    async def _exec(self, oid, fn, args, kwargs):
        """Execute fn request on a service object specified
        by the object id.
        """
        msg_type = self.MsgTypes.REPLY_RESULT

        try:
            try:
                obj_item = self.objects[oid]
            except KeyError:
                raise ServiceObjectNotFoundError(f"{oid} not found")

            def r():
                return getattr(obj_item.obj, fn)(*args, **kwargs)

            if fn == "__getattribute__":
                r = getattr(obj_item.obj, *args)
            elif fn == "__setattribute__":
                r = setattr(obj_item.obj, *args)
            elif fn == "__incref__":
                r = None
                obj_item.refcount += 1
            elif fn == "__decref__":
                r = None
                if obj_item.refcount < 0:
                    raise ValueError(f"{oid} for {obj_item.obj} has invalid refcount {obj_item.refcount}")
                obj_item.refcount -= 1
                if obj_item.refcount <= 0:
                    del self.objects[oid]
            else:
                r = await self.loop.run_in_executor(None, r)

            if asyncio.iscoroutine(r):
                r = await r

        except BaseException as e:
            msg_type = self.MsgTypes.REPLY_EXCEPTION
            exc_type, exc_value, exc_tb = sys.exc_info()
            r = exc_type(str(exc_value) + "\n\nService Traceback (most recent call last):\n" + "".join(traceback.format_tb(exc_tb)).rstrip())
        
        return msg_type, r

    async def _process_message(self, identity, message):
        """Process received message.
        """
        msg_type, rid, msg_body = cloudpickle.loads(message)

        if msg_type == self.MsgTypes.REQUEST:
            # process request
            oid, fn, args, kwargs = msg_body
            msg_type, r = await self._exec(oid, fn, args, kwargs)

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
_process_service_lock = threading.Lock()


def process_service(**kwargs):
    """Get or create global process wide object service.
    """
    global _process_service

    running_in_loop = is_running_in_event_loop()

    async def _async_start_service(**kwargs):
        """Start process service.
        """
        global _process_service
        _process_service = await Service(**kwargs).__aenter__()
        atexit.register(_stop_process_service)
        return _process_service

    async def _async_process_service():
        """Return process service.
        """
        return _process_service

    with _process_service_lock:
        if _process_service is None:
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

            if running_in_loop:
                return _async_start_service(**kwargs)

            _process_service = Service(**kwargs).__enter__()
            atexit.register(_stop_process_service)

        if running_in_loop:
            return _async_process_service()

    return _process_service


def _stop_process_service():
    """Stop global process service.
    """
    global _process_service
 
    with _process_service_lock:
        if _process_service is not None:
            _process_service.__exit__(None, None, None)
            _process_service = None


class BaseServiceObject:
    """Base class for all service objects.

    :param oid: object id
    :param address: address `tuple(hostname, port)`
    """
    _exposed = None
    _typename = None

    def __init__(self, oid, address, _incref=True) -> None:
        """Initialize service object.
        """
        self.oid = oid
        self.address = address
        if _incref:
            # increment service object reference count
            self._incref(self.oid, self.address)
        # cleanup object by decrementing reference count
        # when no longer in use
        self._cleanup = Finalize(
            self, BaseServiceObject._decref,
            args=(self.oid, self.address),
            exitpriority=1
            )

    @staticmethod
    def _incref(oid, address):
        """Increment service object reference count.
        """
        if is_running_in_event_loop():
            asyncio.get_running_loop().create_task(BaseServiceObject.__async_proxy_call__(
                oid, address, "__incref__"))
        else:
            BaseServiceObject.__proxy_call__(oid, address, "__incref__")

    @staticmethod
    def _decref(oid, address):
        """Decrement service object reference count.
        """
        async def _async_call():
            try:
                await BaseServiceObject.__async_proxy_call__(
                    oid, address, "__decref__", timeout=0.1)
            except (TimeoutError, ServiceObjectNotFoundError, ServiceNotRunningError, CancelledError):
                pass

        def _call():
            try:
                BaseServiceObject.__proxy_call__(
                    oid, address, "__decref__", timeout=0.1)
            except (TimeoutError, ServiceObjectNotFoundError, ServiceNotRunningError, CancelledError):
                pass

        if is_running_in_event_loop():
            asyncio.get_running_loop().create_task(_async_call())
        else:
            _call()

    def __eq__(self, other: object) -> bool:
        """Compare to service objects.
        """
        return other.oid == self.oid and other.address == self.address 

    @staticmethod
    async def __async_proxy_call__(oid, address, fn, args=None, kwargs=None, timeout=None):
        """Execute function call on the remote service.
        """
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        if _process_service is None:
            raise ServiceNotRunningError("service has not been started")

        async def wrap(c):
            """Wrap coroutine that is running in another event loop.
            """
            if asyncio.get_event_loop() is not _process_service.loop:
                return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(c, loop=_process_service.loop))
            return await c

        send = await wrap(_process_service._connect(address))
        response = await wrap(send(uuid.uuid1().bytes, oid, fn, args, kwargs, resp=True, timeout=timeout))

        await asyncio.wait_for(wrap(response.wait()), timeout=timeout)
        reply_type, reply_body = response.message

        if reply_type == Service.MsgTypes.REPLY_EXCEPTION:
            if isinstance(reply_body, (SystemExit, KeyboardInterrupt)):
                reply_body = RuntimeError(f"{reply_body.__class__}: {reply_body}")
            raise reply_body

        return reply_body

    @staticmethod
    def __proxy_call__(oid, address, fn, args=None, kwargs=None, timeout=None):
        """Synchronously execute function call on the remote service.
        """
        return asyncio.run_coroutine_threadsafe(BaseServiceObject.__async_proxy_call__(oid, address, fn, args, kwargs, timeout=timeout), loop=_process_service.loop).result()

    def __reduce__(self):
        """Make service object serializable.
        """
        self._incref(self.oid, self.address)
        return (RebuildServiceObject, (self._typename, self._exposed, self.oid, self.address, False))


class AsyncBaseServiceObject(BaseServiceObject):
    """Async base service object.
    """
    def __reduce__(self):
        """Make service object serializable.
        """
        self._incref(self.oid, self.address)
        return (RebuildAsyncServiceObject, (self._typename, self._exposed, self.oid, self.address, False))


def RebuildServiceObject(typename, exposed, oid, address, _incref=True):
    """Rebuild service object during unpickling.
    """
    return ServiceObjectType(typename, exposed)(oid=oid, address=address, _incref=_incref)


def RebuildAsyncServiceObject(typename, exposed, oid, address, _incref):
    """Rebuild async service object during unpickling.
    """
    return ServiceObjectType(typename, exposed, _async=True)(oid=oid, address=address, _incref=_incref)


def make_exposed_defs(exposed, asynced):
    """Make expose class definitions.
    """
    defs = []

    for name in exposed.methods:
        defs.append(f"{'async ' if asynced else ''}def {name}(self, *args, **kwargs):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.oid, self.address, \"{name}\", args, kwargs)",
            )

    for name in exposed.properties:
        defs.append(f"@property\n"
                f"{'async ' if asynced else ''}def {name}(self):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.oid, self.address, \"__getattribute__\", [\"{name}\"])"
                f"\n"
                f"@{name}.setter\n"
                f"{'async ' if asynced else ''}def {name}(self, v):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.out, self.address, \"__setattribute__\", [\"{name}\", v])",
            )
    
    return defs


def ServiceObjectType(typename, exposed, asynced=False, _cache={}):
    """Make service object type.
    """
    try:
        return _cache[(typename, exposed, asynced)]
    except KeyError:
        pass
    
    _attrs = {}
   
    exec("\n".join(make_exposed_defs(exposed, asynced=asynced)), _attrs)

    base = AsyncBaseServiceObject if asynced else BaseServiceObject

    service_type = type(f"{'Async' if asynced else ''}ServiceObject[{typename}]", (base,), _attrs)
    service_type._exposed = exposed
    service_type._typename = typename

    _cache[(typename, exposed, asynced)] = service_type
    
    return service_type


ExposedMethodsAndProperties = namedtuple("Exposed", "methods properties", defaults=([], []))


def auto_expose(obj):
    """Auto expose all public methods and properties of an object.
    """
    methods = []
    properties = []

    for name, value in inspect.getmembers(obj):
        if name.startswith("_"):
            continue

        if type(value) in [types.MethodWrapperType, types.MethodType, types.BuiltinMethodType]:
            methods.append(name)
        else:
            properties.append(name)

    return ExposedMethodsAndProperties(tuple(methods), tuple(properties))


def AsyncServiceObject(obj, address, expose=None):
    """Make async service object.
    """
    return ServiceObjectType(f"{type(obj)}", expose or auto_expose(obj), asynced=True)(oid=id(obj), address=address)


def ServiceObject(obj, address, expose=None):
    """Make service object.
    """
    return ServiceObjectType(f"{type(obj)}", expose or auto_expose(obj))(oid=id(obj), address=address)
