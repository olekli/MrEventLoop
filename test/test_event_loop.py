# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
from mreventloop import emits, slot, forwards, connect, EventLoop, setEventLoop, has_event_loop, emits_bilaterally

@has_event_loop('event_loop')
@emits('events', [ 'result' ])
class Producer:
  def __init__(self):
    self.counter = 0

  @slot
  async def produce(self):
    self.events.result(f'product', self.counter)
    self.counter += 1

@has_event_loop('event_loop')
@forwards([ 'onProcessedResult' ])
@emits('events', [ 'processed_result', 'result' ])
class ProcessorEven:
  @slot
  async def onResult(self, result, number):
    if (int(number / 2) * 2) == number:
      self.events.processed_result(f'{result} even {number}')
    else:
      self.events.result(result, number)

@has_event_loop('event_loop')
@forwards([ 'onProcessedResult' ])
@emits('events', [ 'processed_result', 'result' ])
class ProcessorOdd:
  @slot
  def onResult(self, result, number):
    if (int(number / 2) * 2) != number:
      self.events.processed_result(f'{result} odd {number}')
    else:
      self.events.result(result, number)

@has_event_loop('event_loop')
@forwards([ 'onProcessedResult' ])
@emits('events', [ 'processed_result', 'result' ])
class ProcessorOddAsync:
  @slot
  def onResult(self, result, number):
    if (int(number / 2) * 2) != number:
      self.events.processed_result(f'{result} odd {number}')
    else:
      self.events.result(result, number)

@has_event_loop('event_loop')
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  async def onProcessedResult(self, result):
    self.content.append(result)

@has_event_loop('event_loop')
class ConsumerException:
  def __init__(self):
    self.content = []

  @slot
  async def onProcessedResult(self, result):
    raise RuntimeError('foo')

@has_event_loop('event_loop')
class ExceptionReceiver:
  def __init__(self):
    self.content = []

  @slot
  async def onException(self, e):
    self.content.append(e)

@has_event_loop('event_loop')
class SlotWithReturnValue:
  @slot
  def call(self):
    return 'foo'

@has_event_loop('event_loop')
class AsyncSlotWithReturnValue:
  @slot
  async def call(self):
    await asyncio.sleep(0.01)
    return 'foo'

@emits_bilaterally('events', [ 'request' ])
@has_event_loop('event_loop')
class BilateralSender:
  def __init__(self):
    pass

  @slot
  async def sendRequest(self, req):
    return await self.events.request(req)

@has_event_loop('event_loop')
class BilateralReceiver:
  def __init__(self):
    pass

  @slot
  def onRequest(self, req):
    return req[::-1]

@emits_bilaterally('events', [ 'request' ])
@has_event_loop('event_loop')
class BilateralSenderAsync:
  def __init__(self):
    pass

  @slot
  async def sendRequest(self, req):
    return await self.events.request(req)

@has_event_loop('event_loop')
class BilateralReceiverAsync:
  def __init__(self):
    pass

  @slot
  async def onRequest(self, req):
    await asyncio.sleep(0.01)
    return req[::-1]

@pytest.mark.asyncio
async def test_pipeline_one_loop_async_unordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOddAsync()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  async with EventLoop() as event_loop:
    setEventLoop(producer, event_loop)
    setEventLoop(processor_even, event_loop)
    setEventLoop(processor_odd, event_loop)
    setEventLoop(consumer, event_loop)

    for i in range(10):
      producer.produce()

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert len(consumer.content) == 10
  for item in [
    'product even 0',
    'product odd 1',
    'product even 2',
    'product odd 3',
    'product even 4',
    'product odd 5',
    'product even 6',
    'product odd 7',
    'product even 8',
    'product odd 9',
  ]:
    assert item in consumer.content

@pytest.mark.asyncio
async def test_pipeline_multiple_loops_async():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOddAsync()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  async with EventLoop() as event_loop_3:
    async with EventLoop() as event_loop_2:
      async with EventLoop() as event_loop_1:
        setEventLoop(producer, event_loop_1)
        setEventLoop(processor_even, event_loop_1)
        setEventLoop(processor_odd, event_loop_2)
        setEventLoop(consumer, event_loop_3)

        for i in range(10):
          producer.produce()

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert len(consumer.content) == 10
  for item in [
    'product even 0',
    'product odd 1',
    'product even 2',
    'product odd 3',
    'product even 4',
    'product odd 5',
    'product even 6',
    'product odd 7',
    'product even 8',
    'product odd 9',
  ]:
    assert item in consumer.content

@pytest.mark.asyncio
async def test_pipeline_multiple_loops_async_exception():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOddAsync()
  consumer = ConsumerException()
  setEventLoop(consumer, EventLoop(False))
  e_receiver = ExceptionReceiver()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)
  connect(consumer.event_loop, 'exception', e_receiver, 'onException')

  async with e_receiver.event_loop:
    async with consumer.event_loop:
      async with processor_odd.event_loop:
        async with processor_even.event_loop:
          async with producer.event_loop:
            for i in range(10):
              producer.produce()

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert len(e_receiver.content) == 10

@pytest.mark.asyncio
async def test_pipeline_multiple_loops_async_defaults():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  async with consumer.event_loop:
    async with processor_odd.event_loop:
      async with processor_even.event_loop:
        async with producer.event_loop:
          for i in range(10):
            producer.produce()

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert len(consumer.content) == 10
  for item in [
    'product even 0',
    'product odd 1',
    'product even 2',
    'product odd 3',
    'product even 4',
    'product odd 5',
    'product even 6',
    'product odd 7',
    'product even 8',
    'product odd 9',
  ]:
    assert item in consumer.content

@pytest.mark.asyncio
async def test_slot_return():
  a = SlotWithReturnValue()
  async with a.event_loop:
    result = a.call()
    assert result != 'foo'
    awaited_result = await result
    assert awaited_result == 'foo'

@pytest.mark.asyncio
async def test_slot_return_async():
  a = AsyncSlotWithReturnValue()
  async with a.event_loop:
    result = a.call()
    assert result != 'foo'
    awaited_result = await result
    assert awaited_result == 'foo'

@pytest.mark.asyncio
async def test_connected_bilateral_return_value():
  sender = BilateralSender()
  receiver = BilateralReceiver()

  connect(sender, 'request', receiver, 'onRequest')

  async with sender.event_loop, receiver.event_loop:
    result = sender.sendRequest('foo')
    assert await result == 'oof'

@pytest.mark.asyncio
async def test_connected_bilateral_return_value_async():
  sender = BilateralSenderAsync()
  receiver = BilateralReceiverAsync()

  connect(sender, 'request', receiver, 'onRequest')

  async with sender.event_loop, receiver.event_loop:
    result = sender.sendRequest('foo')
    assert await result == 'oof'
