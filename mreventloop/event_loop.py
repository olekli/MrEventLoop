# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import threading

class EventLoop:
  def __init__(self):
    self.thread = threading.Thread(target = self.run)
    self.loop = asyncio.new_event_loop()

  def __enter__(self):
    self.thread.start()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    asyncio.run_coroutine_threadsafe(self.stop(), self.loop)
    self.thread.join()

  def run(self):
    asyncio.set_event_loop(self.loop)
    self.cv = asyncio.Condition()
    self.loop.run_until_complete(self.wait())

  async def stop(self):
    async with self.cv:
      self.cv.notify_all()

  async def wait(self):
    async with self.cv:
      await self.cv.wait()
    while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task()]:
      await asyncio.gather(*tasks)
