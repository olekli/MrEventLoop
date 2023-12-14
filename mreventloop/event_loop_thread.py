# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import queue
import logging
import traceback
from mreventloop.decorators import emits
from mreventloop.attr import setEventLoopAttr, setEventLoop

logger = logging.getLogger(__name__)

@emits('events', [ 'active', 'idle' ])
class EventLoopThread:
  def __init__(self, exit_on_exception = True):
    self.exit_on_exception = exit_on_exception
    self.queue = queue.Queue()
    self.thread = threading.Thread(target = self.runThread)
    self.closed = threading.Event()

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
    self.events.idle()
    while not (self.closed.is_set() and self.queue.empty()):
      item = self.queue.get()
      if item == None:
        continue
      self.events.active()
      target, args, kwargs = item
      try:
        target(*args, **kwargs)
      except Exception as e:
        logger.error(traceback.format_exc())
        if self.exit_on_exception:
          return
      self.events.idle()

def has_event_loop_thread(event_loop_attr):
  def has_event_loop_(cls):
    setEventLoopAttr(cls, event_loop_attr)
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
      setEventLoop(self, EventLoopThread())
      original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls
  return has_event_loop_

