# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from queue import SimpleQueue
import threading
from mreventloop.decorators import emits

@emits('events', [ 'active', 'idle' ])
class EventLoop:
  def __init__(self):
    self.queue = SimpleQueue()
    self.thread = threading.Thread(target = self.run)
    self.closed = threading.Event()

  def enqueue(self, target, *args, **kwargs):
    if not self.closed.is_set() or threading.current_thread().ident == self.thread.ident:
      self.queue.put( (target, args, kwargs) )

  def __enter__(self):
    self.thread.start()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.queue.put(None)
    self.thread.join()

  def run(self):
    self.events.idle()
    while True:
      if self.closed.is_set() and self.queue.empty():
        break
      item = self.queue.get()
      if item == None:
        self.closed.set()
        continue
      self.events.active()
      target, args, kwargs = item
      target(*args, **kwargs)
      self.events.idle()
