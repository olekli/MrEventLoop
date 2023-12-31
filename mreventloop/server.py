# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
import traceback
from jsonrpcserver import Success, async_dispatch
from jsonrpcclient import request
from mreventloop.decorators import emits_bilaterally, slot
from mreventloop.event_loop import has_event_loop
from mreventloop.attr import setEvents
from mreventloop.bilateral_events import BilateralEvents
from mreventloop.make_awaitable import make_awaitable
from mreventloop.worker import Worker
import logging

logger = logging.getLogger(__name__)

async def successWrapper(result):
  return Success(await make_awaitable(result))

@emits_bilaterally('events', [])
@has_event_loop('event_loop')
class Server(Worker):
  def __init__(self, rep_socket_path, pub_socket_path, rep_event_names, pub_event_names):
    super().__init__()

    self.rep_socket_path = rep_socket_path
    self.pub_socket_path = pub_socket_path
    setEvents(self, BilateralEvents(rep_event_names))
    self.methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        successWrapper(getattr(self.events, event_name)(*args, **kwargs))
      for event_name in rep_event_names
    }
    self.context = zmq.asyncio.Context()
    self.rep_socket = self.context.socket(zmq.REP)
    self.pub_socket = self.context.socket(zmq.PUB) if self.pub_socket_path else None
    for event_name in pub_event_names:
      setattr(
        self,
        event_name,
        lambda *args, event_name=event_name, **kwargs: \
          self.publish(event_name, *args, **kwargs)
      )

  @slot
  async def publish(self, event_name, *args, **kwargs):
    message = request(event_name, params = tuple(args))
    logger.debug(f'publishing: {message}')
    await self.pub_socket.send_string(json.dumps(message))

  async def run(self):
    try:
      request = await asyncio.wait_for(self.rep_socket.recv_string(), timeout = 1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'received request: {request}')
    response = await async_dispatch(
      request,
      methods = self.methods,
      validator = lambda _: None
    )
    logger.debug(f'replying with: {response}')
    await self.rep_socket.send_string(response)

  async def __aenter__(self):
    await self.event_loop.__aenter__()
    self.rep_socket.bind(self.rep_socket_path)
    if self.pub_socket:
      self.pub_socket.bind(self.pub_socket_path)
    self.main = asyncio.create_task(self.run())
    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await super().__aexit__(exc_type, exc_value, traceback)
    await self.event_loop.__aexit__(exc_type, exc_value, traceback)
    self.rep_socket.close()
    if self.pub_socket:
      self.pub_socket.close()
