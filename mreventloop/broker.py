# Copyright 2024 Ole Kliemann
# SPDX-License-Identifier: Apache-2.0

import asyncio
import zmq
import zmq.asyncio
from mreventloop.worker import Worker
import logging

logger = logging.getLogger(__name__)

class Broker(Worker):
  def __init__(self, out_socket_path, in_socket_path):
    super().__init__()

    self.in_socket_path = in_socket_path
    self.out_socket_path = out_socket_path

    self.ctx = zmq.asyncio.Context()
    self.in_socket = self.ctx.socket(zmq.SUB)
    self.out_socket = self.ctx.socket(zmq.PUB)

    self.in_socket_bound = asyncio.Event()
    self.out_socket_bound = asyncio.Event()

  async def _run(self):
    try:
      message = await asyncio.wait_for(self.in_socket.recv(), timeout = 0.1)
    except asyncio.TimeoutError:
      return
    logger.debug(f'relaying message: {message}')
    await self.out_socket.send(message)

  async def waitForBind(self, monitor, event):
    await monitor.recv()
    event.set()

  async def __aenter__(self):
    asyncio.create_task(self.waitForBind(
      self.in_socket.get_monitor_socket(zmq.Event.LISTENING),
      self.in_socket_bound
    ))
    asyncio.create_task(self.waitForBind(
      self.out_socket.get_monitor_socket(zmq.Event.LISTENING),
      self.out_socket_bound
    ))

    self.in_socket.bind(self.in_socket_path)
    self.in_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    self.out_socket.bind(self.out_socket_path)

    await self.in_socket_bound.wait()
    await self.out_socket_bound.wait()

    self.in_socket.disable_monitor()
    self.out_socket.disable_monitor()

    await super().__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await super().__aexit__(exc_type, exc_value, traceback)
    self.in_socket.close()
    self.out_socket.close()
