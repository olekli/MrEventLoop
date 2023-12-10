# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
from mreventloop import emits, slot, forwards, connect, EventLoop, setEventLoop, supports_event_loop

@supports_event_loop('event_loop')
@emits('events', [ 'result' ])
class Producer:
  def __init__(self):
    self.counter = 0

  @slot
  async def produce(self):
    self.events.result(f'product', self.counter)
    self.counter += 1

@supports_event_loop('event_loop')
@forwards([ 'onProcessedResult' ])
@emits('events', [ 'processed_result', 'result' ])
class ProcessorEven:
  @slot
  async def onResult(self, result, number):
    if (int(number / 2) * 2) == number:
      self.events.processed_result(f'{result} even {number}')
    else:
      self.events.result(result, number)

@supports_event_loop('event_loop')
@forwards([ 'onProcessedResult' ])
@emits('events', [ 'processed_result', 'result' ])
class ProcessorOdd:
  @slot
  def onResult(self, result, number):
    if (int(number / 2) * 2) != number:
      self.events.processed_result(f'{result} odd {number}')
    else:
      self.events.result(result, number)

@supports_event_loop('event_loop')
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  async def onProcessedResult(self, result):
    self.content.append(result)

@pytest.mark.asyncio
async def test_pipeline_one_loop_unordered():
  producer = Producer()
  processor_even = ProcessorEven()
  processor_odd =  ProcessorOdd()
  consumer = Consumer()
  connect(producer, None, processor_even, None)
  connect(processor_even, None, processor_odd, None)
  connect(processor_odd, None, consumer, None)

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

  for i in range(0, 10):
    producer.produce()

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
