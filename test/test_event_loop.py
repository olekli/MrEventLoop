# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
from mreventloop import emits, slot, forwards, connect, EventLoop, setEventLoop, has_event_loop

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

@pytest.mark.asyncio
async def test_pipeline_one_loop_async_unordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOddAsync()
  consumer = Consumer()
  connect(producer, processor_even)
  connect(processor_even, processor_odd)
  connect(processor_odd, consumer)

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
  connect(producer, processor_even)
  connect(processor_even, processor_odd)
  connect(processor_odd, consumer)

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
  connect(producer, processor_even)
  connect(processor_even, processor_odd)
  connect(processor_odd, consumer)
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
  connect(producer, processor_even)
  connect(processor_even, processor_odd)
  connect(processor_odd, consumer)

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
async def test_event_loop_started_stopped():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, processor_even)
  connect(processor_even, processor_odd)
  connect(processor_odd, consumer)
  connect(producer.event_loop, 'started', lambda r=range(10): [ producer.produce() for i in r ])
  connect(producer.event_loop, 'stopped', lambda: consumer.content.append('final'))

  async with consumer.event_loop:
    async with processor_odd.event_loop:
      async with processor_even.event_loop:
        async with producer.event_loop:
          pass

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert len(consumer.content) == 11
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
    'final'
  ]:
    assert item in consumer.content
