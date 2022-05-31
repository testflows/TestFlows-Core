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
import concurrent.futures
import testflows.settings as settings
import testflows._core.tracing as tracing

from collections import namedtuple
from multiprocessing.util import Finalize, is_exiting

from testflows._core.contrib import cloudpickle
from testflows._core.contrib.aiomsg import Socket

from .asyncio import asyncio, is_running_in_event_loop, OptionalFuture, CancelledError
from .asyncio import TimeoutError as AsyncTimeoutError
from .executor.thread import SharedThreadPoolExecutor

Address = namedtuple("address", "hostname port", defaults=(None,))

TimeoutError = (asyncio.exceptions.TimeoutError, concurrent.futures._base.TimeoutError)

tracer = tracing.getLogger(__name__)

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
        self.identity = self.in_socket.identity
        self.serve_tasks = []
        self.reply_futures = {}
        self.objects = {}
        self.executor = SharedThreadPoolExecutor(sys.maxsize, join_on_shutdown=False)
        self.open = False
        self.lock = asyncio.Lock(loop=self.loop)
        self.init_tracer = tracing.EventAdapter(tracer, None, source=str(self))
        self.tracer = tracing.EventAdapter(tracer, None, source=str(self))

    def __str__(self):
        return f"Service(pid={os.getpid()},name={self.name},identity={self.identity.hex()},address={self.address},in_socket={self.in_socket},out_socket={self.out_socket})@0x{id(self):x}"

    def register(self, obj, sync=None, expose=None, awaited=True):
        """Register object with the service to be by remote services.
        """
        event_tracer = tracing.EventAdapter(self.tracer, name=f"register({obj},sync={sync},expose={expose},awaited={awaited}")
        event_tracer.debug("registration started", extra={"event_action":tracing.Action.START})
  
        if isinstance(obj, BaseServiceObject):
            raise ValueError(f"registering service objects not allowed")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        def _register(sync: bool=False):
            if not self.open:
                raise ServiceNotRunningError("service is not running")

            _id = id(obj)

            if _id not in self.objects:
                self.objects[_id] = Service.ObjectItem(obj)

            try:
                if sync:
                    return ServiceObject(obj, identity=self.identity, address=self.address, expose=expose)
                return AsyncServiceObject(obj, identity=self.identity, address=self.address, expose=expose)
            finally:
                event_tracer.debug("registration complete", extra={"event_action": tracing.Action.END})

        async def _async_register(sync: bool=False):
            return _register(sync=sync)

        if loop is self.loop and not awaited:
            return _register(sync=sync)

        if loop is None or not awaited:
            return asyncio.run_coroutine_threadsafe(_async_register(sync=True), loop=self.loop).result()
        elif loop is not self.loop:
            return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_async_register(sync=sync), loop=self.loop))
        else:
            return _async_register(sync=sync)

    async def unregister(self, obj):
        """Unregister object from the service to stop
        providing object to remote services.
        """
        event_tracer = tracing.EventAdapter(self.tracer, name=f"unregister({obj}@0x{id(self):x})")
        event_tracer.debug("unregistration started", extra={"event_action":tracing.Action.START})
  
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _async_unregister():
            _id = id(obj)

            if _id in self.objects:
                del self.objects[_id]

            event_tracer.debug("unregistration complete", extra={"event_action":tracing.Action.END})
        
        if loop is None:
            return asyncio.run_coroutine_threadsafe(_async_unregister(), loop=self.loop).result()
        elif loop is not self.loop:
            return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_async_unregister(), loop=self.loop))
        else:
            return _async_unregister()

    async def _connect(self, rid, identity, address, timeout=None):
        """Connect to the remote service that provides
        access to the remote object.
        """
        event_tracer = tracing.EventAdapter(self.tracer, name=f"_connect(rid={rid},identity={identity.hex()},address={address})")      
        event_tracer.debug("connecting", extra={"event_action": tracing.Action.START})

        try:
            async def local_send(rid, oid, fn, args, kwargs, reply=True, timeout=None):
                """Send service object request to the local service.
                """
                try:
                    with tracing.Event(event_tracer,
                                    name=f"local_send(oid=0x{oid:x},fn={fn},args={args},kwargs={kwargs},"
                                        f"reply={reply},timeout={timeout})") as local_send_tracer:
                        try:
                            msg_type, msg_body = await self._exec(oid, fn, args, kwargs)

                            if reply:
                                future = OptionalFuture()
                                future.set_result((msg_type, msg_body))
                                return future
                        except BaseException as exc:
                            raise
                        else:
                            local_send_tracer.debug("reply={msg_body}")
                finally:
                    event_tracer.debug(f"complete", extra={"event_action": tracing.Action.END})

            async def send(rid, oid, fn, args, kwargs, reply=True, timeout=None):
                """Send service object request to remote service.
                """
                try:
                    with tracing.Event(event_tracer,
                                       name=f"send(oid=0x{oid:x},fn={fn},args={args},kwargs={kwargs},"
                                        f"reply={reply},timeout={timeout})") as send_tracer:
                        try:
                            try:
                                await asyncio.wait_for(self.out_socket.send_pickle(
                                        obj=(self.MsgTypes.REQUEST, rid, (oid, fn, args, kwargs)),
                                        identity=identity
                                    ), timeout=timeout)
                                send_tracer.debug("sent request")
                            except TypeError:
                                send_tracer.debug("failed to send due to TypeError, creating service objects for args")
                                # convert any unpicklable objects to service objects
                                pickler = self.out_socket.pickler

                                args = list(args)
                                for i in range(len(args)):
                                    arg = args[i]
                                    try:
                                        pickler.dumps(arg)
                                    except TypeError:
                                        send_tracer.debug(f"registering {arg}, sync=True")
                                        args[i] = await self.register(arg, sync=True)
                                
                                for k in kwargs:
                                    arg = kwargs[k]
                                    try:
                                        pickler.dumps(arg)
                                    except TypeError:
                                        send_tracer.debug(f"registering {arg}, sync=True")
                                        kwargs[k] = await self.register(arg, sync=True)

                                send_tracer.debug("trying again to send after TypeError")
                                await asyncio.wait_for(self.out_socket.send_pickle(
                                        obj=(self.MsgTypes.REQUEST, rid, (oid, fn, args, kwargs)),
                                        identity=identity
                                    ), timeout=timeout)
                                send_tracer.debug("sent request after TypeError")

                            if reply:
                                future = OptionalFuture()
                                self.reply_futures[rid] = future
                                send_tracer.debug(f"returning reply future")
                                return future
                            else:
                                event_tracer.debug(f"send without reply complete")

                        except BaseException as exc:
                            raise 
                finally:
                    event_tracer.debug("complete", extra={"event_action": tracing.Action.END})

            if not self.open:
                raise ServiceNotRunningError("service is not running")
                
            if address == self.address:
                event_tracer.debug("using local_send")
                return local_send

            async with self.lock:
                event_tracer.debug("got service lock")
                if not identity in self.out_socket._connections:
                    event_tracer.debug(f"connecting to identity={identity.hex()},address={address}")
                    future = OptionalFuture()

                    await self.out_socket.connect(
                        address.hostname,
                        address.port,
                        future=future,
                        expected_identity=identity,
                        reconnection_delay=Socket.exponential_backoff(min_delay=0.1, max_delay=2),
                        timeout=timeout,
                        permanent=False
                        )

                    event_tracer.debug("wating for connection")
                    await asyncio.wait_for(future, timeout=timeout)
                    event_tracer.debug("got connection")

                    if not identity in self.out_socket._connections:
                        raise RuntimeError(f"connecting to address={address} didn't result in connection to identity={identity.hex()}")

            event_tracer.debug("using non-local send")
            return send

        except BaseException as exc:
            event_tracer.exception(exc, extra={"event_action": tracing.Action.END})
            raise

    def __enter__(self):
        """Sync context manager enter.
        """
        self.init_tracer.debug("__enter__", extra={"event_action": tracing.Action.START})
        return asyncio.run_coroutine_threadsafe(self.__aenter__(), loop=self.loop).result()

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Sync context manager exit.
        """
        try:
            return asyncio.run_coroutine_threadsafe(self.__aexit__(exc_type, exc_value, exc_tb), loop=self.loop).result()
        finally:
            self.init_tracer.debug("__exit__", extra={"event_action": tracing.Action.END})

    async def __aenter__(self):
        """Async context manager enter.
        """
        with tracing.Event(self.init_tracer, name="__aenter__") as event_tracer:
            async with self.lock:
                event_tracer.debug("got lock")
                self.executor.__enter__()
                await self.in_socket.bind(hostname=self.address.hostname, port=self.address.port)
                self.address = Address(*self.in_socket.bind_address)
                self.tracer = tracing.EventAdapter(tracer, None, source=str(self))
                self.loop.create_task(self._serve_forever())
                self.open = True
                return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Async context manager exit.
        """
        self.init_tracer.info(f"closing {self} with sockets {self.out_socket} and {self.in_socket}")

        with tracing.Event(self.init_tracer, name="__aexit__") as event_tracer:
            async with self.lock:
                event_tracer.debug("got lock")
                try:
                    self.objects = {}
                   
                    for task in self.serve_tasks:
                        task.cancel()
                    await asyncio.gather(*self.serve_tasks, return_exceptions=True)

                    try:
                        try:
                            await self.out_socket.close()
                        finally:
                            await self.in_socket.close()
                    finally:
                        self.executor.__exit__(None, None, None)
                finally:
                    self.open = False

    def __incref__(self, oid, obj_item=None):
        """Increment object reference count.
        """
        with tracing.Event(self.tracer, f"__incref__(oid=0x{oid:x},obj_item={obj_item})") as event_tracer:
            if not obj_item:
                try:
                    obj_item = self.objects[oid]
                except KeyError:
                    raise ServiceObjectNotFoundError(f"0x{oid}x not found")

            obj_item.refcount += 1
            event_tracer.debug(f"new refcount {obj_item.refcount}")

    def __decref__(self, oid, obj_item=None):
        """Decrement object reference count.
        """
        with tracing.Event(self.tracer, f"__decref__(oid=0x{oid:x},obj_item={obj_item})") as event_tracer:
            if not obj_item:
                try:
                    obj_item = self.objects[oid]
                except KeyError:
                    raise ServiceObjectNotFoundError(f"0x{oid:x} not found")
            
            if obj_item.refcount < 0:
                raise ValueError(f"0x{oid:x} for {obj_item.obj} has invalid refcount {obj_item.refcount}")
            obj_item.refcount -= 1
            
            event_tracer.debug(f"new refcount {obj_item.refcount}")

            if obj_item.refcount <= 0:
                del self.objects[oid]
                event_tracer.debug(f"deleted")

    async def _exec(self, oid, fn, args, kwargs):
        """Execute fn request on a service object specified
        by the object id.
        """
        with tracing.Event(self.tracer, f"_exec(oid=0x{oid:x},fn={fn},args={args},kwargs={kwargs})") as event_tracer:     
            msg_type = self.MsgTypes.REPLY_RESULT

            try:
                try:
                    obj_item = self.objects[oid]
                except KeyError:
                    raise ServiceObjectNotFoundError(f"0x{oid:x} not found")

                def r():
                    try:
                        return getattr(obj_item.obj, fn)(*args, **kwargs)
                    except BaseException as exc:
                        event_tracer.exception(exc)
                        raise
                    finally:
                        event_tracer.debug("executed")

                if fn == "__getattribute__":
                    with tracing.Event(event_tracer, f"getattr"):
                        r = getattr(obj_item.obj, *args)
                elif fn == "__setattribute__":
                    with tracing.Event(event_tracer, f"setattr"):
                        r = setattr(obj_item.obj, *args)
                elif fn == "__incref__":
                    with tracing.Event(event_tracer, f"__incref__"):
                        r = self.__incref__(oid, obj_item)
                elif fn == "__decref__":
                    with tracing.Event(event_tracer, f"__decref__"):
                        r = self.__decref__(oid, obj_item)
                else:
                    with tracing.Event(event_tracer, f"run_in_executor({self.executor})"):
                        r = await self.loop.run_in_executor(self.executor, r)

                if asyncio.iscoroutine(r):
                    with tracing.Event(event_tracer, "result is coroutine"):
                        r = await r

            except BaseException as e:
                event_tracer.exception("executed, got exception={e}")
                msg_type = self.MsgTypes.REPLY_EXCEPTION
                exc_type, exc_value, exc_tb = sys.exc_info()
                r = exc_type(str(exc_value) + "\n\nService Traceback (most recent call last):\n" + "".join(traceback.format_tb(exc_tb)).rstrip())
            
            event_tracer.debug(f"executed, result={r}")
            return msg_type, r

    async def _process_message(self, identity, message):
        """Process received message.
        """
        with tracing.Event(self.tracer, f"_process_message(identity={identity.hex()}),message={message}") as event_tracer:
            msg_type, rid, msg_body = cloudpickle.loads(message)

            if msg_type == self.MsgTypes.REQUEST:
                # process request
                oid, fn, args, kwargs = msg_body
                with tracing.Event(event_tracer, f"request:rid={rid},oid=0x{oid:x},fn={fn},args={args},kwargs={kwargs}"):
                    msg_type, r = await self._exec(oid, fn, args, kwargs)
                    try:
                        await self.in_socket.send_pickle((msg_type, rid, r), identity=identity)
                    except TypeError as e:
                        _r = await self.register(r, sync=True)
                        await self.in_socket.send_pickle((msg_type, rid, _r), identity=identity)
            else:
                with tracing.Event(event_tracer, f"reply:rid={rid},message={msg_body}"):
                    # process reply
                    reply_future = self.reply_futures.pop(rid)
                    reply_future.set_result((msg_type, msg_body))

    async def _serve_forever(self):
        """Start service until coroutine is cancelled.
        """
        with tracing.Event(self.tracer, "_serve_forever") as event_tracer:
            async def _serve_requests():
                with tracing.Event(event_tracer, "_serve_requests") as requests_tracer:
                    while True:
                        try:
                            requests_tracer.debug("waiting for request")
                            identity, message = await asyncio.wait_for(self.in_socket.recv_identity(), timeout=1) 
                        except AsyncTimeoutError:
                            continue
                        self.in_socket.loop.create_task(self._process_message(identity, message))

            async def _serve_replies():
                with tracing.Event(event_tracer, "_serve_replies") as replies_tracer:
                    while True:
                        try:
                            replies_tracer.debug("waiting for replies")
                            identity, message = await asyncio.wait_for(self.out_socket.recv_identity(), timeout=1)
                        except AsyncTimeoutError:
                            continue
                        self.out_socket.loop.create_task(self._process_message(identity, message))

            self.serve_tasks.append(
                    self.in_socket.loop.create_task(_serve_requests())
                )
            event_tracer.debug("created _serve_requests task")

            self.serve_tasks.append(
                    self.out_socket.loop.create_task(_serve_replies())
                )
            event_tracer.debug("created _serve_replies task")


# global process wide service
_process_service = None
_process_service_lock = threading.Lock()


def process_service(**kwargs):
    """Get or create global process wide object service.
    """
    global _process_service

    with _process_service_lock:
        if _process_service is None:
            loop = kwargs.pop("loop", None)

            if loop is None:
                loop = asyncio.new_event_loop()

                def run_event_loop():
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_forever()
                    finally:
                        tasks = [task for task in asyncio.all_tasks(loop=loop)]
                        for task in tasks:
                            task.cancel()
                        try:
                            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                            loop.run_until_complete(loop.shutdown_asyncgens())
                        finally:
                            loop.close()

                thread = threading.Thread(target=run_event_loop, daemon=True)

                def stop_event_loop():
                    loop.call_soon_threadsafe(loop.stop)
                    thread.join()

                thread.start()
                atexit.register(stop_event_loop)

            kwargs["loop"] = loop
            kwargs["name"] = kwargs.get("name", f"process-service-{os.getpid()}")

            _process_service = Service(**kwargs).__enter__()
            atexit.register(_stop_process_service)

    return _process_service


def _stop_process_service():
    """Stop global process service.
    """
    with tracing.Event(tracer, "_stop_process_service") as event_tracer:
        global _process_service

        with _process_service_lock:
            event_tracer.debug("got lock")
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

    def __init__(self, oid, identity, address, _incref=True):
        """Initialize service object.
        """
        self.oid = oid
        self.identity = identity
        self.address = address
        self._tracer = tracing.EventAdapter(tracer, None, source=str(self))

        if _incref:
            # increment service object reference count
            self._incref()
        # cleanup object by decrementing reference count
        # when no longer in use
        self._cleanup = Finalize(
            self, self._decref, args=(self.oid, self.address, self.identity), kwargs={"_tracer": self._tracer},
            exitpriority=1
            )

    def __str__(self):
        return f"{self.__class__.__name__}(oid=0x{self.oid:x},identity={self.identity.hex()},address={self.address})@0x{id(self):x}"

    def __repr__(self):
        return str(self)

    def _incref(self):
        """Increment service object reference count.
        """
        oid = self.oid
        address = self.address
        identity = self.identity

        with tracing.Event(self._tracer, "_incref"):
            if is_running_in_event_loop():
                if _process_service: 
                    if _process_service.loop is asyncio.get_running_loop():
                        if  _process_service.address == address:
                            _process_service.__incref__(oid)
                        else:
                            _process_service.loop.create_task(self.__async_proxy_call__(oid, address, identity, "__incref__", _tracer=self._tracer))
                        return

            self.__proxy_call__(oid, address, identity, "__incref__", _tracer=self._tracer)

    @classmethod
    def _decref(cls, oid, address, identity, _timeout_err={}, _service_not_running_err=[False], _tracer=tracer):
        """Decrement service object reference count.
        """
        if is_exiting():
            return 

        with tracing.Event(_tracer, "_decref"):
            if _service_not_running_err[0]:
                return

            if _timeout_err.get(address):
                return

            try:
                if is_running_in_event_loop():
                    async def no_errors(aws):
                        try:
                            await aws
                        except (ServiceNotRunningError, ServiceObjectNotFoundError, CancelledError):
                            pass

                    if _process_service:
                        if _process_service.loop is asyncio.get_running_loop():
                            if _process_service.address == address:  
                                _process_service.__decref__(oid)
                            else:
                                _process_service.loop.create_task(no_errors(cls.__async_proxy_call__(oid, address, identity, "__decref__", _tracer=_tracer)))
                            return

                cls.__proxy_call__(oid, address, identity, "__decref__", timeout=settings.service_timeout, _tracer=_tracer)

            except TimeoutError:
                _timeout_err[address] = True

            except ServiceNotRunningError:
                _service_not_running_err[0] = True

            except (ServiceObjectNotFoundError, CancelledError):
                pass

    def __eq__(self, other: object) -> bool:
        """Compare to service objects.
        """
        return other.oid == self.oid and other.address == self.address 

    @classmethod
    async def __async_proxy_call__(cls, oid, address, identity, fn, args=None, kwargs=None, timeout=None, rid=None, _tracer=tracer):
        """Execute function call on the remote service.
        """
        if rid is None:
            rid = uuid.uuid1().hex

        with tracing.Event(_tracer, f"__async_proxy_call__(rid={rid},oid=0x{oid:x},identity={identity.hex()}"
                                    f",address={address},fn={fn},args={args},kwargs={kwargs},timeout={timeout})"):
            if args is None:
                args = tuple()
            if kwargs is None:
                kwargs = dict()

            try:
                async def wrap(c):
                    """Wrap coroutine that is running in another event loop.
                    """
                    if asyncio.coroutines.iscoroutine(c):
                        if asyncio.get_event_loop() is not _process_service.loop:
                            return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(c, loop=_process_service.loop))
                    return await c

                send = await wrap(_process_service._connect(rid, identity, address))
                reply = await wrap(send(rid, oid, fn, args, kwargs, reply=True, timeout=timeout))

                reply_type, reply_body = await asyncio.wait_for(wrap(reply), timeout=timeout)

                if reply_type == Service.MsgTypes.REPLY_EXCEPTION:
                    if isinstance(reply_body, (SystemExit, KeyboardInterrupt)):
                        reply_body = RuntimeError(f"{reply_body.__class__}: {reply_body}")
                    raise reply_body
            except AttributeError:
                if _process_service is None:
                    raise ServiceNotRunningError("service has not been started")
                raise

            return reply_body

    @classmethod
    def __proxy_call__(cls, oid, address, identity, fn, args=None, kwargs=None, timeout=None, rid=None, _tracer=tracer):
        """Synchronously execute function call on the remote service.
        """
        if rid is None:
            rid = uuid.uuid1().hex

        with tracing.Event(_tracer, f"__proxy_call__(rid={rid},oid=0x{oid:x},identity={identity.hex()},"
                                    f"address={address},fn={fn},args={args},kwargs={kwargs},timeout={timeout})"):
            try:
                c = cls.__async_proxy_call__(oid, address, identity, fn, args, kwargs, timeout=timeout, rid=rid, _tracer=_tracer)
                try:
                    return asyncio.run_coroutine_threadsafe(c, loop=_process_service.loop).result()
                finally:
                    c.close()
            except AttributeError:
                if _process_service is None:
                    raise ServiceNotRunningError("service has not been started")
                raise

    def __reduce__(self):
        """Make service object serializable.
        """
        self._incref()
        return (RebuildServiceObject, (self._typename, self._exposed, self.oid, self.identity, self.address, False))


class AsyncBaseServiceObject(BaseServiceObject):
    """Async base service object.
    """
    def __reduce__(self):
        """Make service object serializable.
        """
        self._incref()
        return (RebuildAsyncServiceObject, (self._typename, self._exposed, self.oid, self.identity, self.address, False))


def RebuildServiceObject(typename, exposed, oid, identity, address, _incref=True):
    """Rebuild service object during unpickling.
    """
    return ServiceObjectType(typename, exposed)(oid=oid, identity=identity, address=address, _incref=_incref)


def RebuildAsyncServiceObject(typename, exposed, oid, identity, address, _incref=True):
    """Rebuild async service object during unpickling.
    """
    return ServiceObjectType(typename, exposed, asynced=True)(oid=oid, identity=identity, address=address, _incref=_incref)


def make_exposed_defs(exposed, asynced):
    """Make expose class definitions.
    """
    defs = []

    for name in exposed.methods:
        defs.append(f"{'async ' if asynced else ''}def {name}(self, *args, **kwargs):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.oid, self.address, self.identity, \"{name}\", args, kwargs, _tracer=self._tracer)",
            )

    for name in exposed.properties:
        defs.append(f"@property\n"
                f"{'async ' if asynced else ''}def {name}(self):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.oid, self.address, self.identity, \"__getattribute__\", [\"{name}\"], _tracer=self._tracer)"
                f"\n"
                f"@{name}.setter\n"
                f"{'async ' if asynced else ''}def {name}(self, v):\n"
                f"    return {'await ' if asynced else ''}self.__{'async_' if asynced else ''}proxy_call__(self.oid, self.address, self.identity, \"__setattribute__\", [\"{name}\", v], _tracer=self._tracer)",
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


def AsyncServiceObject(obj, identity, address, expose=None, _incref=True):
    """Make async service object.
    """
    return ServiceObjectType(f"{str(obj)}", expose or auto_expose(obj), asynced=True)(
        oid=id(obj), identity=identity, address=address, _incref=_incref)


def ServiceObject(obj, identity, address, expose=None, _incref=True):
    """Make service object.
    """
    return ServiceObjectType(f"{str(obj)}", expose or auto_expose(obj))(
        oid=id(obj), identity=identity, address=address, _incref=_incref)
