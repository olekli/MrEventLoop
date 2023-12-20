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
  def produce(self):
    self.counter += 1
    logger.debug(f'producing: {self.counter}')
    return str(self.counter)

@has_event_loop('event_loop')
@emits('events', [ 'request_produce' ])
class Consumer:
  def __init__(self):
    self.content = []

  @slot
  def onProduce(self, product):
    self.content.append(product)

  @slot
  def requestProduce(self):
    self.events.request_produce()

@pytest.mark.asyncio
async def test_client_server():
  with tempfile.NamedTemporaryFile(
      prefix = 'socket',
      suffix = '.ipc',
      delete = True
  ) as socket_file:
    producer = Producer()
    consumer = Consumer()
    client = Client(f'ipc://{socket_file.name}', [ 'produce' ])
    server = Server(f'ipc://{socket_file.name}', [ 'produce' ])

    connect(server, 'produce', producer, 'produce')
    connect(consumer, 'request_produce', client, 'onRequestProduce')
    connect(client, 'produce', consumer, 'onProduce')

    async with server, client, producer.event_loop, consumer.event_loop:
      consumer.requestProduce()
      consumer.requestProduce()
      consumer.requestProduce()
      for i in range(0, 100):
        if len(consumer.content) == 3:
          break
        await asyncio.sleep(0.01)
      print('done')

    assert consumer.content == [ '1', '2', '3' ]
