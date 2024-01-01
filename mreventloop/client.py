# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
from types import SimpleNamespace
from jsonrpcclient import request, parse_json, Ok, Error
from jsonrpcserver import dispatch, Success
from mreventloop.names import eventToRequestName
from mreventloop.events import Events
from mreventloop.attr import getEvent, setEvents
from mreventloop.decorators import emits, slot
from mreventloop.event_loop import has_event_loop
from mreventloop.worker import Worker
import logging

logger = logging.getLogger(__name__)

@emits('events', [])
@has_event_loop('event_loop')
class Client(Worker):
  def __init__(self, socket_path, req_event_names, pub_event_names):
    super().__init__()

    self.req_socket_path = f'{socket_path}.req'
    self.pub_socket_path = f'{socket_path}.pub'
    self.ctx = zmq.asyncio.Context()
    self.req_socket = self.ctx.socket(zmq.REQ)
    self.pub_socket = self.ctx.socket(zmq.SUB)

    setEvents(self, Events(pub_event_names))
    self.request = SimpleNamespace()
    for event_name in req_event_names:
      setattr(
        self.request,
        event_name,
        lambda *args, event_name=event_name, **kwargs: \
          self.requestFromServer(event_name, *args, **kwargs)
      )
    self.methods = {
      event_name: lambda *args, event_name=event_name, **kwargs: \
        Success(getattr(self.events, event_name)(*args, **kwargs))
      for event_name in pub_event_names
    }

  @slot
  async def requestFromServer(self, event_name, *args, **kwargs):
    message = request(event_name, params = tuple(args))
    logger.debug(f'sending request: {message}')
    await self.req_socket.send_string(json.dumps(message))
    response = parse_json(await self.req_socket.recv_string())
    match response:
      case Ok(result, id):
        return True
      case Error(code, message, data, id):
        logging.error(message)
        return False

  async def run(self):
    try:
      message = await asyncio.wait_for(self.pub_socket.recv_string(), timeout = 0.1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'received published message: {message}')
    dispatch(
      message,
      methods = self.methods,
      validator = lambda _: None
    )

  async def __aenter__(self):
    self.req_socket.connect(self.req_socket_path)
    self.pub_socket.connect(self.pub_socket_path)
    self.pub_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    await self.event_loop.__aenter__()
    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await super().__aexit__(exc_type, exc_value, traceback)
    await self.event_loop.__aexit__(exc_type, exc_value, traceback)
    self.req_socket.close()
    self.pub_socket.close()
