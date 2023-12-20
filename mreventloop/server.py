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
import logging

logger = logging.getLogger(__name__)

async def successWrapper(result):
  return Success(await make_awaitable(result))

@emits_bilaterally('events', [])
@has_event_loop('event_loop')
class Server:
  def __init__(self, socket_path, event_names):
    self.socket_path = socket_path
    setEvents(self, BilateralEvents(event_names))
    self.methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        successWrapper(getattr(self.events, event_name)(*args, **kwargs))
      for event_name in event_names
    }
    self.context = zmq.asyncio.Context()
    self.socket = self.context.socket(zmq.REP)
    self.stop_event = None
    self.main = None

  @slot
  def stop(self):
    assert self.stop_event
    self.stop_event.set()

  async def run(self):
    await self.event_loop.__aenter__()
    try:
      self.stop_event = asyncio.Event()
      self.socket.bind(self.socket_path)
      while not self.stop_event.is_set():
        try:
          request = await asyncio.wait_for(self.socket.recv_string(), timeout = 1)
        except asyncio.TimeoutError:
          continue
        logger.debug(f'received request: {request}')
        response = await async_dispatch(
          request,
          methods = self.methods,
          validator = lambda _: None
        )
        logger.debug(f'replying with: {response}')
        await self.socket.send_string(response)
    except Exception as e:
      logger.error(traceback.format_exc())
    self.socket.close()
    await self.event_loop.__aexit__(None, None, None)

  async def __aenter__(self):
    self.main = asyncio.create_task(self.run())
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    self.stop()
    await self.main

  def __await__(self):
    yield from self.main.__await__()
