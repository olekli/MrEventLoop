# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import threading
import queue
import inspect
import logging
import traceback
from mreventloop.decorators import emits

logger = logging.getLogger(__name__)

@emits('events', [ 'active', 'idle' ])
class EventLoopAsync:
  def __init__(self, exit_on_exception = True):
    self.exit_on_exception = exit_on_exception
    self.queue = queue.Queue()
    self.thread = threading.Thread(target = self.runThread)
    self.closed = threading.Event()
    self.asyncio_event_loop = None

  def enqueue(self, target, *args, **kwargs):
    self.queue.put( (target, args, kwargs) )

  def __enter__(self):
    self.thread.start()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.closed.set()
    self.queue.put(None)
    self.thread.join()

  def runThread(self):
    self.asyncio_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.asyncio_event_loop)
    asyncio.run(self.runAsyncio())

  async def runAsyncio(self):
    self.events.idle()
    while not (self.closed.is_set() and self.queue.empty()):
      item = self.queue.get()
      if item == None:
        continue
      self.events.active()
      target, args, kwargs = item
      try:
        if inspect.iscoroutinefunction(target):
          await target(*args, **kwargs)
        else:
          target(*args, **kwargs)
      except Exception as e:
        logger.error(traceback.format_exc())
        if self.exit_on_exception:
          asyncio.get_event_loop().stop()
          return
      self.events.idle()
