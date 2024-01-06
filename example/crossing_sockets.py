# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
from mreventloop import emits, connect
from mreventloop import has_event_loop, slot
from mreventloop import Broker, Peer

@emits('events', [ 'produced' ])
@has_event_loop('event_loop')
class Producer:
  @slot
  def onRequestProduct(self):
    self.events.produced('some product')

@emits('events', [ 'request_product' ])
@has_event_loop('event_loop')
class Consumer:
  @slot
  def onProduced(self, product):
    print(f'{product}')

async def main():
  in_socket_path = 'ipc:///tmp/mreventloop_test_in.sock'
  out_socket_path = 'ipc:///tmp/mreventloop_test_out.sock'

  producer_peer = Peer(in_socket_path, out_socket_path, [ 'request_product' ], [ 'produced' ])
  consumer_peer = Peer(in_socket_path, out_socket_path, [ 'produced' ], [ 'request_product' ])
  async with Broker(in_socket_path, out_socket_path), producer_peer, consumer_peer:
    consumer = Consumer()
    connect(consumer, 'request_product', consumer_peer.publish, 'request_product')
    connect(consumer_peer, 'produced', consumer, 'onProduced')

    producer = Producer()
    connect(producer, 'produced', producer_peer.publish, 'produced')
    connect(producer_peer, 'request_product', producer, 'onRequestProduct')

    async with producer.event_loop, consumer.event_loop:
      consumer.events.request_product()
      await asyncio.sleep(0.2)

asyncio.run(main())
