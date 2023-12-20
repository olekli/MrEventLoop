# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import pytest
import tempfile
from mreventloop import emits, slot, forwards, connect, EventLoop, setEventLoop, has_event_loop, emits_bilaterally, Client, Server
import logging

logger = logging.getLogger(__name__)

@has_event_loop('event_loop')
class Producer:
  def __init__(self):
    self.counter = 0

  @slot
  def produceA(self):
    self.counter += 1
    logger.debug(f'producing: {self.counter}')
    return str(self.counter)

  @slot
  def produceB(self, x, y):
    self.counter += (x + y)
    logger.debug(f'producing: {self.counter}')
    return str(self.counter)

@has_event_loop('event_loop')
@emits('events', [ 'request_produce_a', 'request_produce_b' ])
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  def onProduce(self, product):
    self.content.append(product)

  @slot
  def requestProduceA(self):
    self.events.request_produce_a()

  @slot
  def requestProduceB(self, x, y):
    self.events.request_produce_b(x, y)

@pytest.mark.asyncio
async def test_client_server():
  with tempfile.NamedTemporaryFile(
      prefix = 'socket',
      suffix = '.ipc',
      delete = True
  ) as socket_file:
    producer = Producer()
    consumer = Consumer()
    client = Client(f'ipc://{socket_file.name}', [ 'produce_a', 'produce_b' ])
    server = Server(f'ipc://{socket_file.name}', [ 'produce_a', 'produce_b' ])

    connect(server, 'produce_a', producer, 'produceA')
    connect(server, 'produce_b', producer, 'produceB')
    connect(consumer, 'request_produce_a', client, 'onRequestProduceA')
    connect(consumer, 'request_produce_b', client, 'onRequestProduceB')
    connect(client, 'produce_a', consumer, 'onProduce')
    connect(client, 'produce_b', consumer, 'onProduce')

    async with server, client, producer.event_loop, consumer.event_loop:
      consumer.requestProduceA()
      consumer.requestProduceA()
      consumer.requestProduceA()
      consumer.requestProduceB(0, 0)
      consumer.requestProduceB(2, 1)
      consumer.requestProduceA()
      for i in range(0, 100):
        if len(consumer.content) == 3:
          break
        await asyncio.sleep(0.01)
      print('done')

    assert consumer.content == [ '1', '2', '3', '3', '6', '7' ]
