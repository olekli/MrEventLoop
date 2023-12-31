# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
import traceback
from jsonrpcserver import Success, async_dispatch
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
  def __init__(self, socket_path, event_names):
    super().__init__()

    self.socket_path = socket_path
    setEvents(self, BilateralEvents(event_names))
    self.methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        successWrapper(getattr(self.events, event_name)(*args, **kwargs))
      for event_name in event_names
    }
    self.context = zmq.asyncio.Context()
    self.socket = self.context.socket(zmq.REP)

  async def run(self):
    try:
      request = await asyncio.wait_for(self.socket.recv_string(), timeout = 1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'received request: {request}')
    response = await async_dispatch(
      request,
      methods = self.methods,
      validator = lambda _: None
    )
    logger.debug(f'replying with: {response}')
    await self.socket.send_string(response)

  async def __aenter__(self):
    await self.event_loop.__aenter__()
    self.socket.bind(self.socket_path)
    self.main = asyncio.create_task(self.run())
    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.event_loop.__aexit__(exc_type, exc_value, traceback)
    return await super().__aexit__(exc_type, exc_value, traceback)
    self.socket.close()
