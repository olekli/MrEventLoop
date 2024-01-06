# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
import tempfile
from mreventloop import emits, slot, forwards, connect, EventLoop, setEventLoop, has_event_loop, Peer, Broker
import logging

logger = logging.getLogger(__name__)

@has_event_loop('event_loop')
@emits('events', [ 'produced' ])
class Producer:
  def __init__(self):
    self.counter = 0

  @slot
  def produceA(self):
    self.counter += 1
    self.events.produced(str(self.counter))

  @slot
  def produceB(self, x, y):
    self.counter += (x + y)
    self.events.produced(str(self.counter))

@has_event_loop('event_loop')
@emits('events', [ 'produced' ])
class ProducerOnlyA:
  def __init__(self):
    self.counter = 0

  @slot
  def produceA(self):
    self.counter += 1
    self.events.produced(str(self.counter))

@has_event_loop('event_loop')
@emits('events', [ 'produced' ])
class ProducerOnlyB:
  def __init__(self):
    self.counter = 0

  @slot
  def produceB(self, x, y):
    self.counter += (x + y)
    self.events.produced(str(self.counter))

@has_event_loop('event_loop')
@emits('events', [ 'request_produce_a', 'request_produce_b' ])
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  def onProduced(self, product):
    self.content.append(product)

  @slot
  async def requestProduceA(self):
    self.events.request_produce_a()

  @slot
  async def requestProduceB(self, x, y):
    self.events.request_produce_b(x, y)

@pytest.mark.asyncio
async def test_two_peers():
  with tempfile.NamedTemporaryFile(
      prefix = 'in_socket',
      suffix = '.ipc',
      delete = True
  ) as in_socket_file, \
    tempfile.NamedTemporaryFile(
      prefix = 'out_socket',
      suffix = '.ipc',
      delete = True
  ) as out_socket_file:
    in_socket_path = f'ipc://{in_socket_file.name}'
    out_socket_path = f'ipc://{out_socket_file.name}'
    broker = Broker(in_socket_path, out_socket_path)
    producer_peer = Peer(
      in_socket_path, out_socket_path,
      [ 'request_produce_a', 'request_produce_b' ],
      [ 'produced' ]
    )
    consumer_peer = Peer(
      in_socket_path, out_socket_path,
      [ 'produced' ],
      [ 'request_produce_a', 'request_produce_b' ]
    )

    producer = Producer()
    connect(producer_peer, 'request_produce_a', producer, 'produceA')
    connect(producer_peer, 'request_produce_b', producer, 'produceB')
    connect(producer, 'produced', producer_peer.publish, 'produced')

    consumer = Consumer()
    connect(consumer, 'request_produce_a', consumer_peer.publish, 'request_produce_a')
    connect(consumer, 'request_produce_b', consumer_peer.publish, 'request_produce_b')
    connect(consumer_peer, 'produced', consumer, 'onProduced')

    async with broker, producer_peer, consumer_peer, producer.event_loop, consumer.event_loop:
      coros = []
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceB(0, 0))
      coros.append(consumer.requestProduceB(2, 1))
      coros.append(consumer.requestProduceA())
      await asyncio.gather(*coros)
      for i in range(0, 100):
        if len(consumer.content) == 6:
          break
        await asyncio.sleep(0.01)
      print('done')

    assert consumer.content == [ '1', '2', '3', '3', '6', '7' ]

@pytest.mark.asyncio
async def test_three_peers():
  with tempfile.NamedTemporaryFile(
      prefix = 'in_socket',
      suffix = '.ipc',
      delete = True
  ) as in_socket_file, \
    tempfile.NamedTemporaryFile(
      prefix = 'out_socket',
      suffix = '.ipc',
      delete = True
  ) as out_socket_file:
    in_socket_path = f'ipc://{in_socket_file.name}'
    out_socket_path = f'ipc://{out_socket_file.name}'
    broker = Broker(in_socket_path, out_socket_path)
    producer_a_peer = Peer(
      in_socket_path, out_socket_path,
      [ 'request_produce_a' ],
      [ 'produced' ]
    )
    producer_b_peer = Peer(
      in_socket_path, out_socket_path,
      [ 'request_produce_b' ],
      [ 'produced' ]
    )
    consumer_peer = Peer(
      in_socket_path, out_socket_path,
      [ 'produced' ],
      [ 'request_produce_a', 'request_produce_b' ]
    )

    producer_a = ProducerOnlyA()
    connect(producer_a_peer, 'request_produce_a', producer_a, 'produceA')
    connect(producer_a, 'produced', producer_a_peer.publish, 'produced')

    producer_b = ProducerOnlyB()
    connect(producer_b_peer, 'request_produce_b', producer_b, 'produceB')
    connect(producer_b, 'produced', producer_b_peer.publish, 'produced')

    consumer = Consumer()
    connect(consumer, 'request_produce_a', consumer_peer.publish, 'request_produce_a')
    connect(consumer, 'request_produce_b', consumer_peer.publish, 'request_produce_b')
    connect(consumer_peer, 'produced', consumer, 'onProduced')

    async with broker, \
    producer_a_peer, \
    producer_b_peer, \
    consumer_peer, \
    producer_a.event_loop, \
    producer_b.event_loop, \
    consumer.event_loop:
      coros = []
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceA())
      coros.append(consumer.requestProduceB(0, 0))
      coros.append(consumer.requestProduceB(2, 1))
      coros.append(consumer.requestProduceA())
      await asyncio.gather(*coros)
      for i in range(0, 100):
        if len(consumer.content) == 6:
          break
        await asyncio.sleep(0.01)
      print('done')

    assert consumer.content == [ '1', '2', '3', '0', '3', '4' ]
