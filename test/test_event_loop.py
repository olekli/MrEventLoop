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
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  async def onProcessedResult(self, result):
    self.content.append(result)

@has_event_loop('event_loop')
class NotReentrant:
  def __init__(self):
    self.value = 0
    self.control = 0
    self.event = asyncio.Event()

  @slot
  async def inc(self):
    self.value += 1

  def unblock(self):
    self.event.set()

  @slot
  async def block(self):
    await self.event.wait()

@pytest.mark.asyncio
async def test_pipeline_one_loop_unordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
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
async def test_pipeline_one_loop_ordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  event_loop = EventLoop()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  event_loop = EventLoop()
  setEventLoop(producer, event_loop)
  setEventLoop(processor_even, event_loop)
  setEventLoop(processor_odd, event_loop)
  setEventLoop(consumer, event_loop)

  for i in range(0, 10):
    producer.produce()

  await event_loop.__aenter__()
  await event_loop.__aexit__(None, None, None)

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
async def test_pipeline_multiple_loops():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

  async with EventLoop() as event_loop_2, EventLoop() as event_loop_1:
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
async def test_event_loop_does_not_reenter():
  obj = NotReentrant()
  assert obj.value == 0

  async with EventLoop() as event_loop:
    setEventLoop(obj, event_loop)
    obj.block()
    obj.inc()
    obj.inc()
    assert obj.value == 0
    assert len(asyncio.all_tasks()) == 2
    obj.unblock()

  while tasks := [ t for t in asyncio.all_tasks() if t is not asyncio.current_task() ]:
    await asyncio.gather(*tasks)
  assert obj.value == 2
