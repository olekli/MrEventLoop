# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import inspect
from mreventloop.decorators import emits

@emits('events', [ 'active', 'idle' ])
class EventLoop:
  def __init__(self):
    self.queue = asyncio.Queue()
    self.main = None
    self.closed = False

  def enqueue(self, target, *args, **kwargs):
    assert self.queue
    self.queue.put_nowait( (target, args, kwargs) )

  async def __aenter__(self):
    self.main = asyncio.create_task(self.run())
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    self.closed = True
    self.queue.put_nowait(None)
    if self.main and not self.main.done():
      await self.main

  async def run(self):
    self.events.idle()
    while not (self.closed and self.queue.empty()):
      item = await self.queue.get()
      if item == None:
        continue
      self.events.active()
      target, args, kwargs = item
      if inspect.iscoroutinefunction(target):
        await target(*args, **kwargs)
      else:
        target(*args, **kwargs)
      self.events.idle()
