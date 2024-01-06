# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
from mreventloop import emits, connect
from mreventloop import SyncEvent

@emits('events', [ 'produced' ])
class Producer:
  def requestProduct(self):
    self.events.produced('some product')

async def main():
  producer = Producer()
  sync_event = SyncEvent(producer.events.produced)

  async def emit():
    producer.requestProduct()

  asyncio.create_task(emit())
  result = await sync_event
  print(f'{result}')

asyncio.run(main())
