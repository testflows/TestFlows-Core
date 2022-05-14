"""

aiomsg
======

 (Servers)

Broadly 3 kinds of transmission (ends):

- receive-only
- send-only
- duplex

Broadly 2 kinds of distribution patterns:

- other ends receive all messages
- other ends get round-robin

Broadly 2 kinds of receiving patterns (this is minor):

- keep receiving from a client while there is data
- force switch after each message

Broadly 2 kinds of health/heartbeat patterns:

- for send-only+receive-only: receiver reconnects on timeout
- for duplex: connector sends a ping, binder sends pong. Connector must
  reconnect on a pong timeout

Run tests with watchmedo (available after ``pip install Watchdog`` ):

.. code-block:: bash

    watchmedo shell-command -W -D -R \\
        -c 'clear && py.test -s --durations=10 -vv' \\
        -p '*.py'

"""
import math
import uuid
import json
import time
import socket
import random
import asyncio

import testflows._core.tracing as tracing

from enum import Enum, auto
from asyncio import CancelledError, StreamReader, StreamWriter
from collections import UserDict
from itertools import cycle
from weakref import WeakSet
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
    Union,
    List,
    AsyncGenerator,
    Callable,
    MutableMapping,
    Awaitable,
    Sequence,
)
import  testflows._core.contrib.cloudpickle as cloudpickle

from . import header
from . import msgproto

__all__ = ["Socket", "SendMode", "DeliveryGuarantee"]

tracer = tracing.getLogger(__name__)

SEND_MODES = ["round_robin", "publish"]
JSONCompatible = Union[str, int, float, bool, List, Dict, None]

class NoConnectionsAvailableError(Exception):
    pass

class DisconnectError(ConnectionError):
    """Disconnect message received from the connected host."""
    pass

class IdentityError(ConnectionError):
    """Identity of the connected host did not match the expected."""
    pass

class SendMode(Enum):
    PUBLISH = auto()
    ROUNDROBIN = auto()


class ConnectionEnd(Enum):
    BINDER = auto()
    CONNECTOR = auto()


class DeliveryGuarantee(Enum):
    AT_MOST_ONCE = auto()
    AT_LEAST_ONCE = auto()


class ConnectionsDict(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cycle = None
        self.update_cycle()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.update_cycle()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.update_cycle()

    def update_cycle(self):
        self.cycle = cycle(self.data)

    def __next__(self):
        try:
            return next(self.cycle)
        except StopIteration:
            raise NoConnectionsAvailableError


# noinspection NonAsciiCharacters
class Søcket:
    def __init__(
        self,
        send_mode: SendMode = SendMode.ROUNDROBIN,
        delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_MOST_ONCE,
        receiver_channel: Optional[str] = None,
        identity: Optional[bytes] = None,
        loop=None,
        reconnection_delay: Callable[[], float] = lambda count: (random.random() % 0.1) + 0.2,
        pickler = cloudpickle,
        recv_queue_maxsize=0
    ):
        """
        :param reconnection_delay: In large microservices
            architectures, an outage in one service will result in all the
            dependant services trying to connect over and over again (and
            sending their buffered data immediately). This parameter lets you
            provide a means of staggering the reconnections to avoid
            overwhelming the service that comes back into action after an
            outage. For example, you could stagger all your dependent
            microservices by providing:

                lambda: random.random(10)

            which means that the reconnection delay for a specific socket
            will be a random number of seconds between 0 and 10. This will
            spread out all the reconnecting services over a 10 second
            window.
        """
        self._tasks = WeakSet()
        self.send_mode = send_mode
        self.delivery_guarantee = delivery_guarantee
        self.receiver_channel = receiver_channel
        self.identity = identity or uuid.uuid1().bytes
        self.loop = loop or asyncio.get_event_loop()
        self.pickler = pickler

        self._queue_recv = asyncio.Queue(maxsize=recv_queue_maxsize, loop=self.loop)
        self._connections: MutableMapping[bytes, Connection] = ConnectionsDict()
        self._user_send_queue = asyncio.Queue(loop=self.loop)

        self.server = None
        self.socket_type: Optional[ConnectionEnd] = None
        self.closed = False
        self.at_least_one_connection = asyncio.Event(loop=self.loop)

        self.waiting_for_acks: Dict[uuid.UUID, asyncio.Handle] = {}
        self.reconnection_delay = reconnection_delay

        self.tracer = tracing.EventAdapter(tracer, None, source=str(self))

        self.tracer.debug("Starting the sender task")

        # Note this task is started before any connections have been made.
        self.sender_task = self.loop.create_task(self._sender_main())
        self.connect_with_retry_tasks = []
        if send_mode is SendMode.PUBLISH:
            self.sender_handler = self._sender_publish
        elif send_mode is SendMode.ROUNDROBIN:
            self.sender_handler = self._sender_robin
        else:  # pragma: no cover
            raise Exception("Unknown send mode")

    @staticmethod
    def exponential_backoff(min_delay=0.1, max_delay=1):
        """Exponential backoff delay function that can be used
        to set reconnection_delay function.

        :return: reconnection_delay function that takes retry count 
        """
        return lambda count: min(max_delay, max(min_delay, math.exp(0.1 * count) - 1))

    def __str__(self):
        return f"Socket(identity={self.idstr()},address={self.bind_address})"

    def idstr(self) -> str:
        return self.identity.hex()

    @property
    def bind_address(self) -> Optional[Tuple[str, Optional[int]]]:
        """Return (addr, port) tuple for bound socket or `None`.

        Use this method to retrieve bounded port after calling
        bind method with port set to `0` which let's OS pick
        a random available port.

        Supportted socket families: AF_INET, AF_INET6, AF_UNIX.

        For AF_UNIX returns (path, None)
        """
        if self.server is None:
            return None

        sock = self.server.sockets[0]

        if sock.family in (socket.AF_INET, socket.AF_INET6):
            return sock.getsockname()[:2]
        elif sock.family == socket.AF_UNIX:
            return (sock.getsockname(), None)
        else:
            raise NotImplementedError(f"{sock.family} type is not supported")

    async def bind(
        self,
        hostname: Optional[Union[str, Sequence[str]]] = "127.0.0.1",
        port: int = 25000,
        ssl_context=None,
        **kwargs,
    ):
        """
        :param hostname: Hostname to bind. This can be a few different types,
            see the documentation for `asyncio.start_server()`.
        :param port: See documentation for `asyncio.start_server()`.
        :param ssl_context: See documentation for `asyncio.start_server()`.
        :param kwargs: All extra kwargs are passed through to
            `asyncio.start_server`. See the asyncio documentation for
            details.
        """
        self.check_socket_type()

        try:
            with tracing.Event(self.tracer, name=f"bind(hostname={hostname},port={port},ssl_context={ssl_context},kwargs={kwargs})") as event_tracer:
                event_tracer.info(f"Binding socket to {hostname}:{port}")
                self.server = await asyncio.start_server(
                    self._connection,
                    hostname,
                    port,
                    ssl=ssl_context,
                    reuse_address=True,
                    **kwargs,
                )
                event_tracer.info("Server started")
                return self
        finally:
            # re-initialize tracer to contain full bind address
            self.tracer = tracing.EventAdapter(tracer, None, source=str(self), event_id=self.tracer.extra.get("event_id"))

    async def connect(
        self,
        hostname: str = "127.0.0.1",
        port: int = 25000,
        ssl_context=None,
        connect_timeout: float = 1.0,
        future: Optional[asyncio.Future] = None,
        reconnection_delay=None,
        timeout=None,
        permanent=True,
        expected_identity=None
    ):
        retry_count = 0
        retry_start_time = 0

        if reconnection_delay is None:
            reconnection_delay = self.reconnection_delay
  
        self.check_socket_type()

        async def new_connection(future: Optional[asyncio.Future]):
            """Called each time a new connection is attempted. This
            suspend while the connection is up."""
            nonlocal retry_count, retry_start_time
            retry_count += 1
            retry_start_time = time.time()
            writer = None

            with tracing.Event(self.tracer,
                    name=f"connect(hostname={hostname},port={port},"
                    "ssl_context={ssl_context},connect_timeout={connect_timeout})@new_connection") as event_tracer:
                try:
                    event_tracer.warning(f"Attempting to open connection {hostname}:{port}")
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(
                            hostname, port, loop=self.loop, ssl=ssl_context
                        ),
                        timeout=connect_timeout,
                    )
                    event_tracer.info(f"Connected")
                    # reset retry count
                    retry_count = 0
                    retry_start_time = 0
                    await self._connection(reader, writer, future=future, client_connection=False, expected_identity=expected_identity)
                except asyncio.TimeoutError:
                    # Make timeouts look like socket connection errors
                    raise OSError
                finally:
                    event_tracer.info(f"Disconnected")
                    # NOTE: the writer is closed inside _connection.
                    pass

        async def connect_with_retry(future: Optional[asyncio.Future]):
            """This is a long-running task that is intended to run
            for the life of the Socket object. It will continually
            try to connect."""
            async def _reconnection_delay():
                await asyncio.sleep(reconnection_delay(retry_count))

            with tracing.Event(self.tracer,
                    name=f"connect(hostname={hostname},port={port},"
                    "ssl_context={ssl_context},connect_timeout={connect_timeout})@connect_with_retry") as event_tracer:
                try:
                    while not self.closed:
                        try:
                            if not permanent and timeout and (time.time() - retry_start_time >= timeout):
                                event_tracer.info(f"Connection retries timeout after {timeout} sec, closing connection...")
                                if future is not None:
                                    future.set_exception(TimeoutError(f"Connection retries timeout after {timeout} sec"))
                                break
                            await new_connection(future)
                            if self.closed:
                                break
                        except CancelledError:
                            break
                        except IdentityError as e:
                            if future is not None:
                                future.set_exception(e)
                            break
                        except OSError as e:
                            if self.closed:
                                break
                            else:
                                if isinstance(e, DisconnectError):
                                    if not permanent:
                                        event_tracer.info("Connection host sent disconnect message, closing connection...")
                                        break
                                event_tracer.warning(f"Connection error {e}, reconnecting...")
                                try:
                                    await self.loop.create_task(_reconnection_delay())
                                except CancelledError:
                                    break
                                continue
                        except Exception as e:
                            event_tracer.exception(f"Unexpected error {e}, reconnecting...")
                except Exception as e:
                    event_tracer.exception(f"Unexpected error {e}, closing connection...")
                finally:
                    event_tracer.info(f"Connection to {hostname}:{port}, closed")

        self.connect_with_retry_tasks.append(self.loop.create_task(connect_with_retry(future)))

        return self

    async def messages(self) -> AsyncGenerator[bytes, None]:
        """Convenience method to make it a little easier to get started
        with basic, reactive sockets. This method is intended to be
        consumed with ``async for``, like this:

        .. code-block: python3

            import asyncio
            from aiomsg import SmartSock

            async def main(addr: str):
                async for msg in SmartSock().bind(addr).messages():
                    print(f'Got a message: {msg}')

            asyncio.run(main('localhost:8080'))

        (This is a complete program btw!)
        """
        async for source, msg in self.identity_messages():
            yield msg

    async def identity_messages(self) -> AsyncGenerator[Tuple[bytes, bytes], None]:
        """This is like the ``.messages`` asynchronous generator, but it
        returns a tuple of (identity, message) rather than only the message.

        Example:

        .. code-block: python3

            import asyncio
            from aiomsg import SmartSock

            async def main(addr: str):
                async for src, msg in SmartSock().bind(addr).messages():
                    print(f'Got a message from {src.hex()}: {msg}')

            asyncio.run(main('localhost:8080'))

        """
        while True:
            yield await self.recv_identity()

    async def _connection(self, reader: StreamReader, writer: StreamWriter, future: Optional[asyncio.Future]=None, client_connection: bool=True, expected_identity: bytes=None):
        """Each new connection will create a task with this coroutine."""
        with tracing.Event(self.tracer, name=f"_connection()") as event_tracer:
            event_tracer.debug("Creating new connection")

            # Swap identities
            event_tracer.debug(f"Sending my identity {self.idstr()}")
            await msgproto.send_msg(writer, self.identity)
            identity = await msgproto.read_msg(reader)
            if not identity:
                return

            event_tracer.debug(f"Received identity {identity.hex()}")
            
            if expected_identity and identity != expected_identity:
                raise IdentityError(f"expected identity {expected_identity.hex()} did not match {identity.hex()}")
            
            if identity in self._connections:
                event_tracer.error(
                    f"Socket with identity {identity.hex()} is already "
                    f"connected. This connection will not be created."
                )
                return

            # Create the connection object. These objects are kept in a
            # collection that is used for message distribution.
            connection = Connection(
                identity=identity, reader=reader, writer=writer, recv_event=self.raw_recv, client_connection=client_connection
            )
            if len(self._connections) == 0:
                event_tracer.warning("First connection made")
                self.at_least_one_connection.set()
            self._connections[connection.identity] = connection
            
            # Set connection future and identity of the server to
            # which we have established the connection 
            if future is not None:
                future.set_result(connection.identity)

            try:
                await connection.run()
            except asyncio.CancelledError:
                event_tracer.error(f"Connection {identity.hex()} cancelled")
            except DisconnectError:
                event_tracer.info(f"Connection {identity.hex()} signaled disconnect")
                if not client_connection:
                    raise
            except Exception:
                event_tracer.exception(f"Unhandled exception inside _connection")
                raise
            finally:
                event_tracer.debug("connection closed")
                if connection.identity in self._connections:
                    del self._connections[connection.identity]

                try:
                    try:
                        if writer.can_write_eof():
                            writer.write_eof()
                    finally:
                        writer.close()
                        await writer.wait_closed()
                except BaseException:
                    event_tracer.exception(f"Exception while trying to close writer stream")

                if not self._connections:
                    event_tracer.warning("No connections!")
                    self.at_least_one_connection.clear()

    async def _close(self):
        with tracing.Event(self.tracer, name=f"_close()") as event_tracer:
            event_tracer.info(f"Closing {self.idstr()}")
            self.closed = True

            # send disconnect message to all connected hosts
            for identity, c in self._connections.items():
                if not c.client_connection:
                    continue
                event_tracer.debug(f"Sending disconnect message to {identity.hex()}")
                try:
                    await c.send_wait(c.disconnect_message)
                except Exception as e:
                    event_tracer.exception(f"Exception while sending disconnect message to {identity.hex()}: {e}")

            if self.connect_with_retry_tasks:
                for connect_with_retry_task in self.connect_with_retry_tasks:
                    connect_with_retry_task.cancel()
                await asyncio.gather(*self.connect_with_retry_tasks, return_exceptions=True)

            # REP dict, close all events waiting to fire
            for msg_id, handle in self.waiting_for_acks.items():
                event_tracer.debug(f"Cancelling pending resend event for msg_id {msg_id}")
                handle.cancel()

            if self.server:
                # Stop new connections from being accepted.
                self.server.close()
                await self.server.wait_closed()

            self.sender_task.cancel()
            await self.sender_task

            await asyncio.gather(
                *(c.close() for c in self._connections.values()), return_exceptions=True
            )

            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)

            event_tracer.info(f"Closed {self.idstr()}")

    async def close(self, timeout=10):
        with tracing.Event(self.tracer, name=f"close(timeout={timeout})") as event_tracer:
            try:
                await asyncio.wait_for(self._close(), timeout)
                assert self.sender_task.done()
            except asyncio.TimeoutError:
                event_tracer.exception("Timed out during close:")

    def raw_recv(self, identity: bytes, message: bytes):
        """Called when *any* active connection receives a message."""
        with tracing.Event(self.tracer, name=f"raw_recv(identity={identity.hex()},message={message})") as event_tracer:
            parts = header.parse_header(message)
            event_tracer.debug(f"{parts}")
            if not parts.has_header:
                # Simple case. No request-reply handling, just pass it onto the
                # application as-is.
                event_tracer.debug(
                    f"Incoming message has no header, supply as-is: {message}"
                )
                self._queue_recv.put_nowait((identity, message))
                return

            ######################################################################
            # The incoming message has a header.
            #
            # There are two cases. Let's deal with case 1 first: the received
            # message is a NEW message (with a header). We must send a reply
            # back, and pass on the received data to the application.
            # There is a small catch. We must send the reply back to the
            # specific connection that sent us this request. No biggie, we
            # have a method for that.
            if parts.msg_type == "REQ":
                reply_parts = header.MessageParts(
                    msg_id=parts.msg_id, msg_type="REP", payload=b""
                )

                # Make the received data available to the application.
                event_tracer.debug(f"Writing payload for msg_id: {parts.msg_id} to app: {parts.payload}")
                self._queue_recv.put_nowait((identity, parts.payload))
                event_tracer.debug(f"after self._queue_recv for msg_id: {parts.msg_id}")

                # Send acknowledgement of receipt back to the sender

                def notify_rep():
                    event_tracer.debug(f"Got an REQ, sending back an REP msg_id: {parts.msg_id}")
                    self._user_send_queue.put_nowait(
                        # BECAUSE the identity is specified here, we are sure to
                        # send the reply to the specific connection we got the REQ
                        # from.
                        (identity, header.make_message(reply_parts))
                    )

                # By deferring this slightly, we hope that the parts.payload
                # will be made available to the application before the REP is
                # sent. Otherwise, there's a race condition where we send the
                # REP *before* parts.payload has been given to the app, and the
                # app shuts down before being able to do anything with
                # parts.payload
                self.loop.call_later(0.02, notify_rep)  # 20 ms
                return

            # Now we get to the second case. the message we're received here is
            # a REPLY to a previously sent message. A good thing! All we do is
            # a little bookkeeping to remove the message id from the "waiting for
            # acks" dict, and as before, give the received data to the application.
            event_tracer.debug(f"Got an REP for msg_id: {parts.msg_id} with parts: {parts}")
            assert parts.msg_type == "REP"  # Nothing else should be possible.
            handle: asyncio.Handle = self.waiting_for_acks.pop(parts.msg_id, None)
            event_tracer.debug(f"Looked up call_later handle for msg_id: {parts.msg_id} handle: {handle}")
            if handle:
                event_tracer.debug(f"Cancelling handle...for msg_id: {parts.msg_id}")
                handle.cancel()
                # Nothing further to do. The REP does not go back to the application.
            ######################################################################

    async def recv_identity(self) -> Tuple[bytes, bytes]:
        with tracing.Event(self.tracer, name=f"recv_identity()") as event_tracer:
            # Some connection sent us some data
            identity, message = await self._queue_recv.get()
            event_tracer.debug(f"Received message from {identity.hex()}: {message}")

            return identity, message

    def recv_identity_nowait(self) -> Tuple[bytes, bytes]:
        with tracing.Event(self.tracer, name=f"recv_identity_nowait()") as event_tracer:
            # receive immediately available data
            identity, message = self._queue_recv.get_nowait()
            event_tracer.debug(f"Received message from {identity.hex()}: {message}")

            return identity, message

    async def recv(self) -> bytes:
        with tracing.Event(self.tracer, name=f"recv()"):
            # Just drop the identity
            _, message = await self.recv_identity()
            return message

    async def recv_string(self, **kwargs) -> str:
        """Automatically decode messages into strings.

        The ``kwargs`` are passed to the ``.decode()`` method of the
        received bytes object; for example ``encoding`` and ``errors``.
        If you wanted to override the error handler for decoding unicode,
        you might do something like the following:

        .. code-block:: python3

            msg_str = await sock.recv_string(errors='backslashreplace')

        Which will substitute unicode-invalid bytes with hexadecimal values
        formatted like ``\\xNN``.
        """
        with tracing.Event(self.tracer, name=f"recv_string(kwargs={kwargs})"):
            return (await self.recv()).decode(**kwargs)

    async def recv_json(self, **kwargs) -> JSONCompatible:
        """Automatically deserialize messages in JSON format

        The ``kwargs`` are passed to the ``json.loads()`` method.
        """
        with tracing.Event(self.tracer, name=f"recv_json(kwargs={kwargs})"):
            data = await self.recv()
            return json.loads(data, **kwargs)

    async def recv_pickle(self, pickler=None, **kwargs) -> Any:
        """Automatically deserialize messages in Pickle format

        The ``kwargs`` are passed to the ``json.loads()`` method.
        By default uses cloudpickle as the default ``pickler`` module.
        """
        with tracing.Event(self.tracer, name=f"recv_pickle(pickler={pickler},kwargs={kwargs})"):
            if pickler is None:
                pickler = self.pickler

            data = await self.recv()
            return pickler.loads(data, **kwargs)

    async def send(self, data: bytes, identity: Optional[bytes] = None, retries=None, rid=None, msg_id=None):
        if msg_id is None:
            msg_id=uuid.uuid4()

        with tracing.Event(self.tracer, name=f"send(identity={identity.hex()},rid={rid},msg_id={msg_id},data={data})") as event_tracer:
            original_data = data
            if (
                identity or self.send_mode is SendMode.ROUNDROBIN
            ) and self.delivery_guarantee is DeliveryGuarantee.AT_LEAST_ONCE:
                # Enable receipt acknowledgement
                parts = header.MessageParts(
                    msg_id=msg_id, msg_type="REQ", payload=data
                )
                rich_data = header.make_message(parts)
                # TODO: Might want to add a retry counter here somewhere, to keep
                #  track of repeated failures to send a specific message.

                def resend(retries):
                    with tracing.Event(self.tracer, name=f"resend(identity={identity.hex()},rid={rid},msg_id={msg_id},data={data})") as event_tracer:
                        if retries == 0:
                            event_tracer.error(
                                f"No more retries to send. Dropping [{original_data}]"
                            )
                            return

                        if identity:
                            event_tracer.debug(
                                f"Scheduling the resend to identity:{identity.hex()} for data {original_data}"
                            )
                        self._tasks.add(
                            self.loop.create_task(self.send(original_data, identity, rid=rid, msg_id=msg_id))
                        )
                        # After deleting this here, a new one will be created when
                        # we re-enter ``async def send()``
                        event_tracer.debug(f"Removing the acks entry")
                        del self.waiting_for_acks[parts.msg_id]

                handle: asyncio.Handle = self.loop.call_later(
                    5.0, resend, 5 if retries is None else retries - 1
                )
                # In self.raw_recv(), this handle will be cancelled if the other
                # side sends back an acknowledgement of receipt (REP)
                event_tracer.debug("Creating future resend acks entry")
                self.waiting_for_acks[parts.msg_id] = handle
                data = rich_data  # In the send further down, send the rich one.
            else:
                pass

            await self._user_send_queue.put((identity, data))

    async def send_string(self, data: str, identity: Optional[bytes] = None, **kwargs):
        """Automatically convert the string to bytes when sending.

        The ``kwargs`` are passed to the internal ``data.encode()`` method. """
        with tracing.Event(self.tracer, name=f"send_string(identity={identity.hex()},data={data},kwargs={kwargs})"):
            await self.send(data.encode(**kwargs), identity)

    async def send_json(
        self, obj: JSONCompatible, identity: Optional[bytes] = None, **kwargs
    ):
        """Automatically serialize the given ``obj`` to a JSON representation
        when sending.

        The ``kwargs`` are passed to the ``json.dumps()`` method. In particular,
        you might find the ``default`` parameter of ``dumps`` useful, since
        this can be used to automatically convert an otherwise
        JSON-incompatible attribute into something that can be represented.
        For example:

        .. code-block:: python3

            class Blah:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

                def __str__(self):
                    return f'{x},{y}'

            d = dict(text='hi', obj=Blah(1, 2))

            await sock.send_json(d, default=str)
            # The bytes that will be sent: {"text": "hi", "obj": "1,2"}

        It requires a bit more work to make a class properly serialize and
        deserialize to JSON, however. You will need to carefully study
        how to use the ``object_hook`` parameter in the ``json.loads()``
        method.
        """
        with tracing.Event(self.tracer, name=f"send_json(identity={identity.hex()},obj={obj},kwargs={kwargs})"):
            await self.send_string(json.dumps(obj, **kwargs), identity)

    async def send_pickle(
        self, obj: Any, identity: Optional[bytes] = None, pickler=None, rid=None, **kwargs
    ):
        """Automatically serialize the given ``obj`` to Pickle representation.

        The ``kwargs`` are passed to the ``pickler.dumps()`` method.
        By default uses ``cloudpickle`` as the default ``pickler`` module.
        """
        if pickler is None:
            pickler = self.pickler
        with tracing.Event(self.tracer, name=f"send_pickle(identity={identity.hex()},rid={rid},obj={obj},pickler={pickler},kwargs={kwargs})"):
            await self.send(pickler.dumps(obj, **kwargs), identity, rid=rid)

    def _sender_publish(self, message: bytes):
        with tracing.Event(self.tracer, name=f"_send_publish(message={message})") as event_tracer:
            event_tracer.debug(f"Sending message via publish")
            # TODO: implement grouping by named channels
            if not self._connections:
                raise NoConnectionsAvailableError

            for identity, c in self._connections.items():
                event_tracer.debug(f"Sending to connection: {identity.hex()}")
                try:
                    c.writer_queue.put_nowait(message)
                    event_tracer.debug("Placed message on connection writer queue")
                except asyncio.QueueFull:
                    event_tracer.error(
                        f"Dropped msg to Connection {identity.hex()}, its write queue is full"
                    )

    def _sender_robin(self, message: bytes):
        """
        Raises:

        - NoConnectionsAvailableError

        """
        with tracing.Event(self.tracer, name=f"_send_robin(message={message})") as event_tracer:
            event_tracer.debug(f"Sending message via round_robin")
            queues_full = set()
            while True:
                identity = next(self._connections)
                event_tracer.debug(f"Got connection: {identity.hex()}")
                if identity in queues_full:
                    event_tracer.warning(f"All send queues are full, dropping message")
                    return
                try:
                    connection = self._connections[identity]
                    connection.writer_queue.put_nowait(message)
                    event_tracer.debug(f"Added message to connection send queue")
                    return
                except asyncio.QueueFull:
                    event_tracer.warning(
                        "Cannot send to Connection blah, its write queue is full! "
                        "Trying a different peer..."
                    )
                    queues_full.add(identity)

    def _sender_identity(self, message: bytes, identity: bytes):
        """Send directly to a peer with a distinct identity"""
        with tracing.Event(self.tracer, name=f"_sender_identity(identity={identity.hex()},message={message})") as event_tracer:
            event_tracer.debug(
                f"Sending message, identity: {identity.hex()} message: {message}"
            )
            c = self._connections.get(identity)
            if not c:
                event_tracer.error(
                    f"Peer {identity.hex()} is not connected. Message {message} will be dropped"
                )
                return

            try:
                c.writer_queue.put_nowait(message)
                event_tracer.debug(f"Placed message on connection {identity.hex()} writer queue")
            except asyncio.QueueFull:
                event_tracer.error(f"Dropped message on connection {identity.hex()}, its write queue is full")

    async def _sender_main(self):
        with tracing.Event(self.tracer, name=f"_sender_main()") as event_tracer:
            while True:
                q_task: asyncio.Task = self.loop.create_task(self._user_send_queue.get())
                w_task: asyncio.Task = self.loop.create_task(
                    self.at_least_one_connection.wait()
                )
                try:
                    await asyncio.wait([w_task, q_task], return_when=asyncio.ALL_COMPLETED)
                except asyncio.CancelledError:
                    q_task.cancel()
                    w_task.cancel()
                    return

                identity, data = q_task.result()
                event_tracer.debug(f"Got data to send, identity: {identity.hex()} data: {data}")
                try:
                    if identity is not None:
                        self._sender_identity(data, identity)
                    else:
                        try:
                            event_tracer.debug(f"Sending msg via handler: {data}")
                            self.sender_handler(message=data)
                        except NoConnectionsAvailableError:
                            event_tracer.error("No connections available")
                            self.at_least_one_connection.clear()
                            try:
                                # Put it back onto the queue
                                self._user_send_queue.put_nowait((identity, data))
                            except asyncio.QueueFull:
                                event_tracer.error(
                                    "Send queue full when trying to recover "
                                    "from no connections being available. "
                                    "Dropping data!"
                                )
                except Exception as e:
                    event_tracer.exception(f"Unexpected error when sending a message: {e}")

    def check_socket_type(self):
        assert (
            self.socket_type is None
        ), f"Socket type has already been set: {self.socket_type}"

    async def __aenter__(self) -> "Søcket":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class Connection:
    def __init__(
        self,
        identity: bytes,
        reader: StreamReader,
        writer: StreamWriter,
        recv_event: Callable[[bytes, bytes], None],
        client_connection,
        loop=None,
        writer_queue_maxsize=0
    ):
        self.loop = loop or asyncio.get_event_loop()
        self.identity = identity
        self.reader = reader
        self.writer = writer
        self.writer_queue = asyncio.Queue(maxsize=writer_queue_maxsize)
        self.reader_event = recv_event
        self.client_connection = client_connection

        self.reader_task: Optional[asyncio.Task] = None
        self.writer_task: Optional[asyncio.Task] = None

        self.heartbeat_interval = 5
        self.heartbeat_timeout = 15
        self.heartbeat_message = b"aiomsg-heartbeat"
        self.disconnect_message = b"aiomsg-disconnect"

        self.tracer = tracing.EventAdapter(tracer, None, source=str(self))

    def __str__(self):
        return f"Connection(identity={self.identity.hex()})"

    def warn_dropping_data(self):  # pragma: no cover
        with tracing.Event(self.tracer, name=f"warn_dropping_data()") as event_tracer:
            if self.writer_queue.qsize():
                event_tracer.warning(
                    f"Closing connection {self.identity.hex()} but there is "
                    f"still data in the writer queue: {self.writer_queue.qsize()}\n"
                    f"These messages will be lost."
                )

    async def close(self):
        with tracing.Event(self.tracer, name=f"close()") as event_tracer:
            self.warn_dropping_data()
            # Kill the reader task
            self.reader_task.cancel()
            self.writer_task.cancel()
            await asyncio.gather(self.reader_task, self.writer_task, return_exceptions=True)
            self.reader_task = None
            self.writer_task = None
            # Close connection
            try:
                if self.writer.can_write_eof():
                    self.writer.write_eof()
            finally:
                event_tracer.info("closing connection writer")
                self.writer.close()
                await self.writer.wait_closed()

    async def _recv(self):
        with tracing.Event(self.tracer, name=f"_recv()") as event_tracer:
            while True:
                try:
                    event_tracer.debug("Waiting for messages in connection")
                    message = await asyncio.wait_for(
                        msgproto.read_msg(self.reader), timeout=self.heartbeat_timeout
                    )
                    event_tracer.debug(f"Got message in connection: {message}")

                except asyncio.TimeoutError:
                    event_tracer.warning("Heartbeat failed, closing connection")
                    self.writer_queue.put_nowait(None)
                    return

                except asyncio.CancelledError:
                    return

                if not message:
                    event_tracer.debug("Connection closed (recv)")
                    self.writer_queue.put_nowait(None)
                    return

                if message == self.heartbeat_message:
                    event_tracer.debug("Heartbeat received")
                    continue

                if message == self.disconnect_message:
                    event_tracer.info("Disconnect received")
                    raise DisconnectError()

                try:
                    event_tracer.debug(
                        f"Received message on connection {self.identity.hex()}: {message}"
                    )
                    self.reader_event(self.identity, message)
                except asyncio.QueueFull:
                    event_tracer.error(
                        f"Data lost on connection {self.identity.hex()} because the recv "
                        "queue is full!"
                    )
                except Exception as e:
                    event_tracer.exception(f"Unhandled error in _recv: {e}")

    async def send_wait(self, message: bytes):
        with tracing.Event(self.tracer, name=f"send_wait(message={message})"):
            await msgproto.send_msg(self.writer, message)

    @staticmethod
    async def _send(
        identity: bytes,
        send_wait: Callable[[bytes], Awaitable[None]],
        writer_queue: asyncio.Queue,
        heartbeat_interval: float,
        heartbeat_message: bytes,
        reader_task: asyncio.Task,
    ):
        with tracing.Event(tracer, name=f"_send(identity={identity.hex()},heartbeat_interval={heartbeat_interval})") as event_tracer:
            while True:
                try:
                    try:
                        message = await asyncio.wait_for(
                            writer_queue.get(), timeout=heartbeat_interval
                        )
                    except asyncio.TimeoutError:
                        event_tracer.debug("Sending a heartbeat")
                        message = heartbeat_message
                    except asyncio.CancelledError:
                        break
                    else:
                        writer_queue.task_done()

                    if not message:
                        event_tracer.info("Connection closed (send)")
                        reader_task.cancel()
                        break

                    event_tracer.debug(
                        f"Got message from connection writer queue. {message}"
                    )
                    try:
                        await send_wait(message)
                        event_tracer.debug("Sent message")
                    except OSError as e:
                        event_tracer.error(
                            f"Connection {identity.hex()} aborted, dropping "
                            f"message: {message[:50]}...{message[-50:]}\n"
                            f"error: {e}"
                        )
                        break
                    except asyncio.CancelledError:
                        # Try to still send this message.
                        # await msgproto.send_msg(self.writer, message)
                        break
                except Exception as e:
                    event_tracer.error(f"Unhandled error: {e}")

    async def run(self):
        with tracing.Event(self.tracer, name=f"run()") as event_tracer:
            event_tracer.info(f"Connection {self.identity.hex()} running")

            self.reader_task = self.loop.create_task(self._recv())
            self.writer_task = self.loop.create_task(
                self._send(
                    self.identity,
                    self.send_wait,
                    self.writer_queue,
                    self.heartbeat_interval,
                    self.heartbeat_message,
                    self.reader_task,
                )
            )

            try:
                done, pending = await asyncio.wait(
                    [self.reader_task, self.writer_task], return_when=asyncio.FIRST_EXCEPTION
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                self.warn_dropping_data()
                for task in done:
                    task.result()
            except asyncio.CancelledError:
                self.reader_task.cancel()
                self.writer_task.cancel()
                await asyncio.gather(self.reader_task, self.writer_task, return_exceptions=True)
                self.warn_dropping_data()
            except DisconnectError:
                raise
            finally:
                event_tracer.info(f"Connection {self.identity.hex()} no longer active")

# provide alternative socket class name
Socket = Søcket
