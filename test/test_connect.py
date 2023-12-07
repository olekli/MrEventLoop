# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop import emits, slot, forwards, connect

@forwards([ 'onResult' ])
@emits('events', [ 'result' ])
class Producer:
  def __init__(self, product):
    self.product = product

  @slot
  def onRequest(self):
    print(f'onRequest: {self}')
    self.events.result(self.product)

@forwards([ 'onRequest' ])
@emits('events', [ 'request' ])
class Consumer:
  def __init__(self):
    self.result = []

  @slot
  def onResult(self, result):
    print(f'onResult: {self}')
    self.result.append(result)

@emits('events', [ 'request' ])
class Integrated:
  def __init__(self, producer):
    self.producer = producer
    self.result = []
    connect(self, None, self.producer, None)
    connect(self.producer, None, self, None)

  def run(self):
    self.events.request()

  @slot
  def onResult(self, result):
    print(f'onResult: {self}')
    self.result.append(result)

def test_simple_consumer_producer_loop_single_connect():
  consumer = Consumer()
  producer = Producer('product')
  connect(consumer, 'request', producer, 'onRequest')
  connect(producer, 'result', consumer, 'onResult')

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]

def test_simple_consumer_producer_loop_blind_connect():
  consumer = Consumer()
  producer = Producer('product')
  connect(consumer, None, producer, None)
  connect(producer, None, consumer, None)

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]

def test_simple_consumer_producer_loop_list_connect():
  consumer = Consumer()
  producer = Producer('product')
  connect(consumer, [ 'request' ], producer, [ 'onRequest' ])
  connect(producer, [ 'result' ], consumer, [ 'onResult' ])

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]

def test_simple_consumer_producer_loop_with_forwarder_single_connect():
  consumer = Consumer()
  consumer_2 = Consumer()
  producer = Producer('product')
  producer_2 = Producer('foo')

  connect(consumer, 'request', consumer_2, 'onRequest')
  connect(consumer_2, 'request', producer, 'onRequest')
  connect(producer, 'result', producer_2, 'onResult')
  connect(producer_2, 'result', consumer, 'onResult')

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]
  assert consumer_2.result == [ ]

def test_simple_consumer_producer_loop_with_forwarder_list_connect():
  consumer = Consumer()
  consumer_2 = Consumer()
  producer = Producer('product')
  producer_2 = Producer('foo')

  connect(consumer, [ 'request' ], consumer_2, [ 'onRequest' ])
  connect(consumer_2, [ 'request' ], producer, [ 'onRequest' ])
  connect(producer, [ 'result' ], producer_2, [ 'onResult' ])
  connect(producer_2, [ 'result' ], consumer, [ 'onResult' ])

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]
  assert consumer_2.result == [ ]

def test_simple_consumer_producer_loop_with_forwarder_blind_connect():
  consumer = Consumer()
  consumer_2 = Consumer()
  producer = Producer('product')
  producer_2 = Producer('foo')

  connect(consumer, None, consumer_2, None)
  connect(consumer_2, None, producer, None)
  connect(producer, None, producer_2, None)
  connect(producer_2, None, consumer, None)

  consumer.events.request()
  consumer.events.request()

  assert consumer.result == [ 'product', 'product' ]
  assert consumer_2.result == [ ]

def test_connection_to_self_in_constructor():
  integrated = Integrated(Producer('product'))
  integrated.run()
  integrated.run()

  assert integrated.result == [ 'product', 'product' ]
