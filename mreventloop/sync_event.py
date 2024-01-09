# Copyright 2024 Ole Kliemann
# SPDX-License-Identifier: Apache-2.0

import asyncio

class SyncEvent:
  def __init__(self, event):
    self.event = event
    self.event.addListener(self.onEvent)
    self.sync = asyncio.Event()
    self.result = None

  def onEvent(self, *args, **kwargs):
    self.event.removeListener(self.onEvent)
    if args and kwargs:
      self.result = (list(args), kwargs)
    elif args:
      self.result = list(args) if len(args) > 1 else args[0]
    elif kwargs:
      self.result = kwargs
    self.sync.set()

  def __await__(self):
    yield from self.sync.wait().__await__()
    return self.result
