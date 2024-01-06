import asyncio
from mreventloop import emits, connect
from mreventloop import has_event_loop, slot

@emits('events', [ 'produced' ])
class Producer:
  def requestProduct(self):
    self.events.produced('some product')

@has_event_loop('event_loop')
class ConsumerAsync:
  @slot
  async def onProduced(self, product):
    await asyncio.sleep(0.1)
    print(f'{product}')

async def main():
  producer = Producer()
  consumer = ConsumerAsync()
  connect(producer, 'produced', consumer, 'onProduced')
  async with consumer.event_loop:
    print('entering event loop...')
    producer.requestProduct()
    print('exiting event loop...')

asyncio.run(main())
