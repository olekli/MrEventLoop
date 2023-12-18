# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import logging
import traceback
from mreventloop.decorators import emits
from mreventloop.attr import setEventLoopAttr, setEventLoop
from mreventloop.slot_call import SlotCall

logger = logging.getLogger(__name__)

def has_asyncio_event_loop():
  try:
    asyncio.get_event_loop_policy().get_event_loop()
    return True
  except RuntimeError:
    return False

@emits('events', [ 'active', 'idle' ])
class EventLoop:
  def __init__(self, exit_on_exception = True):
    self.exit_on_exception = exit_on_exception
    self.queue = None
    self.asyncio_event_loop = None
    self.main = None
    self.closed = False

  def enqueue(self, target, *args, **kwargs):
    assert self.queue
    assert self.asyncio_event_loop
    assert has_asyncio_event_loop()
    assert asyncio.get_event_loop() is self.asyncio_event_loop
    slot_call = SlotCall(target, args, kwargs)
    self.queue.put_nowait(slot_call)
    return slot_call

  async def __aenter__(self):
    self.asyncio_event_loop = asyncio.get_event_loop()
    self.queue = asyncio.Queue()
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
      slot_call = await self.queue.get()
      if slot_call == None:
        continue
      self.events.active()
      try:
        await slot_call._run()
      except Exception as e:
        logger.error(traceback.format_exc())
        if self.exit_on_exception:
          return
      self.events.idle()

def has_event_loop(event_loop_attr):
  def has_event_loop_(cls):
    setEventLoopAttr(cls, event_loop_attr)
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
      setEventLoop(self, EventLoop())
      original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls
  return has_event_loop_
