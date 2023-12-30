# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import inspect
from mreventloop.make_awaitable import make_awaitable

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
    self._result = await make_awaitable(self._target(*self._args, **self._kwargs))
    self._result_ready.set()

  async def _error(self):
    self._result = await make_awaitable(None)
    self._result_ready.set()
