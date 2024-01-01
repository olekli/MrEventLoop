# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
import traceback
from types import SimpleNamespace
from jsonrpcserver import Success, Error, dispatch
from jsonrpcclient import request
from mreventloop.decorators import emits, slot
from mreventloop.event_loop import has_event_loop
from mreventloop.attr import setEvents
from mreventloop.events import Events
from mreventloop.worker import Worker
import logging

logger = logging.getLogger(__name__)

def methodWrapper(method, *args, **kwargs):
  try:
    method(*args, **kwargs)
    return Success(None)
  except Exception as e:
    logger.error(traceback.format_exc())
    return Error(None)

@emits('events', [])
@has_event_loop('event_loop')
class Server(Worker):
  def __init__(self, socket_path, req_event_names, pub_event_names):
    super().__init__()

    self.req_socket_path = f'{socket_path}.req'
    self.pub_socket_path = f'{socket_path}.pub'
    self.ctx = zmq.asyncio.Context()
    self.req_socket = self.ctx.socket(zmq.REP)
    self.pub_socket = self.ctx.socket(zmq.PUB)

    setEvents(self, Events(req_event_names))
    self.methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        methodWrapper(getattr(self.events, event_name), *args, **kwargs)
      for event_name in req_event_names
    }
    self.publish = SimpleNamespace()
    for event_name in pub_event_names:
      setattr(
        self.publish,
        event_name,
        lambda *args, event_name=event_name, **kwargs: \
          self.doPublish(event_name, *args, **kwargs)
      )

  @slot
  async def doPublish(self, event_name, *args, **kwargs):
    message = request(event_name, params = tuple(args))
    logger.debug(f'publishing: {message}')
    await self.pub_socket.send_string(json.dumps(message))

  async def run(self):
    try:
      request = await asyncio.wait_for(self.req_socket.recv_string(), timeout = 0.1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'received request: {request}')
    response = dispatch(
      request,
      methods = self.methods,
      validator = lambda _: None
    )
    logger.debug(f'replying with: {response}')
    await self.req_socket.send_string(response)

  async def __aenter__(self):
    self.req_socket.bind(self.req_socket_path)
    self.pub_socket.bind(self.pub_socket_path)
    self.main = asyncio.create_task(self.run())
    await self.event_loop.__aenter__()
    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await super().__aexit__(exc_type, exc_value, traceback)
    await self.event_loop.__aexit__(exc_type, exc_value, traceback)
    self.req_socket.close()
    self.pub_socket.close()
