# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
from mreventloop import emits, slot, forwards, connect, EventLoopAsync, EventLoop, setEventLoop, has_event_loop

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
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  async def onProcessedResult(self, result):
    self.content.append(result)

@pytest.mark.asyncio
async def test_pipeline_one_loop_async_unordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  with EventLoopAsync() as event_loop:
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
async def test_pipeline_one_async_loop_ordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  event_loop = EventLoop()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  event_loop = EventLoopAsync()
  setEventLoop(producer, event_loop)
  setEventLoop(processor_even, event_loop)
  setEventLoop(processor_odd, event_loop)
  setEventLoop(consumer, event_loop)

  for i in range(0, 10):
    producer.produce()

  event_loop.__enter__()
  event_loop.__exit__(None, None, None)

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)

  assert consumer.content == [
    'product even 0',
    'product even 2',
    'product even 4',
    'product even 6',
    'product even 8',
    'product odd 1',
    'product odd 3',
    'product odd 5',
    'product odd 7',
    'product odd 9',
  ]

@pytest.mark.asyncio
async def test_pipeline_multiple_loops_async():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  with EventLoopAsync() as event_loop_2, EventLoopAsync() as event_loop_1:
    setEventLoop(producer, event_loop_1)
    setEventLoop(processor_even, event_loop_1)
    setEventLoop(processor_odd, event_loop_2)
    setEventLoop(consumer, event_loop_2)

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
async def test_pipeline_multiple_loops_some_async():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  with EventLoopAsync() as event_loop_3, EventLoop() as event_loop_2, EventLoopAsync() as event_loop_1:
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
