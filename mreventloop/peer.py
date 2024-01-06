# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
import traceback
from types import SimpleNamespace
from jsonrpcserver import Success, dispatch
from jsonrpcclient import request
from mreventloop.decorators import emits, slot
from mreventloop.event_loop import has_event_loop
from mreventloop.attr import setEvents
from mreventloop.events import Events
from mreventloop.worker import Worker
import logging

logger = logging.getLogger(__name__)

@emits('events', [])
@has_event_loop('event_loop')
class Peer(Worker):
  def __init__(self, in_socket_path, out_socket_path, sub_event_names, pub_event_names):
    super().__init__()

    self._in_socket_path = in_socket_path
    self._out_socket_path = out_socket_path
    self._ctx = zmq.asyncio.Context()
    self._in_socket = self._ctx.socket(zmq.SUB)
    self._out_socket = self._ctx.socket(zmq.PUB)

    self._in_socket_connected = asyncio.Event()
    self._out_socket_connected = asyncio.Event()

    self.events = Events(sub_event_names)

    self._methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        Success(getattr(self.events, event_name)(*args, **kwargs))
      for event_name in sub_event_names
    }

    self.publish = SimpleNamespace()
    for event_name in pub_event_names:
      setattr(
        self.publish,
        event_name,
        lambda *args, event_name=event_name: \
          self._publish(event_name, *args)
      )

  @slot
  async def _publish(self, event_name, *args):
    message = request(event_name, params = tuple(args))
    await self._out_socket.send_string(json.dumps(message))
    logger.debug(f'published: {message}')

  async def _run(self):
    try:
      request = await asyncio.wait_for(self._in_socket.recv_string(), timeout = 0.1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'received message: {request}')
    dispatch(
      request,
      methods = self._methods,
      validator = lambda _: None
    )

  async def _waitForEvent(self, monitor, event):
    await monitor.recv()
    event.set()

  async def __aenter__(self):
    asyncio.create_task(self._waitForEvent(
      self._in_socket.get_monitor_socket(zmq.Event.CONNECTED),
      self._in_socket_connected
    ))
    asyncio.create_task(self._waitForEvent(
      self._out_socket.get_monitor_socket(zmq.Event.CONNECTED),
      self._out_socket_connected
    ))

    self._in_socket.connect(self._in_socket_path)
    self._in_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    self._out_socket.connect(self._out_socket_path)

    await self._in_socket_connected.wait()
    await self._out_socket_connected.wait()

    self._in_socket.disable_monitor()
    self._out_socket.disable_monitor()

    await self.event_loop.__aenter__()
    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await super().__aexit__(exc_type, exc_value, traceback)
    await self.event_loop.__aexit__(exc_type, exc_value, traceback)
    self._in_socket.close()
    self._out_socket.close()
