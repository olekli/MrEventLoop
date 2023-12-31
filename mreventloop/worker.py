# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import traceback
import asyncio
import logging
import sys

logger = logging.getLogger(__name__)

class Worker:
  def __init__(self):
    self.stop_event = None
    self.main = None

  async def run(self):
    pass

  async def _run(self):
    self.stop_event = asyncio.Event()
    while not self.stop_event.is_set():
      try:
        await self.run()
      except Exception as e:
        logger.error(traceback.format_exc())
        sys.exit(1)

  async def __aenter__(self):
    self.main = asyncio.create_task(self._run())
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    assert self.stop_event
    self.stop_event.set()
    await self.main

  def __await__(self):
    yield from self.main.__await__()
