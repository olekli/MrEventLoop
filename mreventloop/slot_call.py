# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import inspect

class SlotCall:
  def __init__(self, target, args, kwargs):
    self._target = target
    self._args = args
    self._kwargs = kwargs
    self._result_ready = asyncio.Event()
    self._result = None

  def __await__(self):
    yield from self._result_ready.wait().__await__()
    return self._result

  async def _run(self):
    if inspect.iscoroutinefunction(self._target):
      self._result = await self._target(*self._args, **self._kwargs)
    else:
      self._result = self._target(*self._args, **self._kwargs)
    self._result_ready.set()
