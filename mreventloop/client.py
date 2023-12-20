# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import zmq
import zmq.asyncio
import json
from jsonrpcclient import request, parse_json, Ok, Error
from mreventloop.names import eventToRequestName
from mreventloop.events import Events
from mreventloop.attr import getEvent
from mreventloop.decorators import emits, slot
from mreventloop.event_loop import has_event_loop
import logging

logger = logging.getLogger(__name__)

@emits('events', [])
@has_event_loop('event_loop')
class Client:
  def __init__(self, socket_path, event_names):
    self.socket_path = socket_path
    self.events = Events(event_names)
    self.ctx = zmq.asyncio.Context()
    self.socket = self.ctx.socket(zmq.REQ)

    for event_name, request_name \
    in zip(event_names, [ eventToRequestName(event_name) for event_name in event_names ]):
      setattr(
        self,
        request_name,
        lambda *args, event_name=event_name, **kwargs: \
          self.requestFromServer(event_name, *args, **kwargs)
      )

  @slot
  async def requestFromServer(self, event_name, *args, **kwargs):
    message = request(event_name, params = tuple(args))
    logger.debug(f'sending request: {message}')
    await self.socket.send_string(json.dumps(message))
    response = parse_json(await self.socket.recv_string())
    match response:
      case Ok(result, id):
        getEvent(self, event_name)(result)
      case Error(code, message, data, id):
        logging.error(message)

  async def __aenter__(self):
    await self.event_loop.__aenter__()
    self.socket.connect(self.socket_path)
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    self.socket.close()
    return await self.event_loop.__aexit__(exc_type, exc_value, traceback)
