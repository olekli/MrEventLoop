# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop import emits, slot, forwards, connect, emits_bilaterally, disconnect

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

@forwards([ 'onRequest' ])
@emits('events', [ 'result', 'request' ])
class ProducerForward:
  def __init__(self, product):
    self.product = product

  @slot
  def onRequest(self):
    print(f'onRequest: {self}')
    self.events.result(self.product)

class RequestSpy:
  def __init__(self):
    self.content = []

  @slot
  def onRequest(self):
    self.content.append('foo')

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

@emits_bilaterally('events', [ 'request' ])
class BilateralSender:
  def __init__(self):
    pass

  @slot
  def sendRequest(self, req):
    return self.events.request(req)

class BilateralReceiver:
  def __init__(self):
    pass

  @slot
  def onRequest(self, req):
    return req[::-1]

@emits('events', [ 'request' ])
class Sender:
  def __init__(self):
    pass

  @slot
  def sendRequest(self, req):
    return self.events.request(req)

class Receiver:
  def __init__(self):
    self.content = []

  @slot
  def onRequest(self, req):
    self.content.append(req)

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

def test_simple_consumer_producer_loop_with_forwarder_lambda_connect():
  consumer = Consumer()
  consumer_2 = Consumer()
  producer = Producer('product')
  producer_2 = Producer('foo')

  connect(consumer, 'request', consumer_2, lambda: consumer_2.onRequest())
  connect(consumer_2, 'request', producer, lambda: producer.onRequest())
  connect(producer, 'result', producer_2, lambda x: producer_2.onResult(x))
  connect(producer_2, 'result', consumer, lambda x: consumer.onResult(x))

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

def test_forwarding_does_not_override_impl():
  producer = ProducerForward('product')
  spy = RequestSpy()
  consumer = Consumer()
  connect(producer, 'request', spy, 'onRequest')
  connect(producer, 'result', consumer, 'onResult')

  producer.onRequest()

  assert spy.content == []
  assert consumer.result == [ 'product' ]

def test_connected_bilateral_return_value():
  sender = BilateralSender()
  receiver = BilateralReceiver()

  connect(sender, 'request', receiver, 'onRequest')

  assert sender.sendRequest('foo') == 'oof'

def test_disconnect():
  sender = Sender()
  receiver = Receiver()

  connect(sender, 'request', receiver, 'onRequest')

  sender.sendRequest('foo')

  assert receiver.content == [ 'foo' ]

  disconnect(sender, 'request')

  sender.sendRequest('bar')

  assert receiver.content == [ 'foo' ]

def test_disconnect_bilateral():
  sender = BilateralSender()
  receiver = BilateralReceiver()

  connect(sender, 'request', receiver, 'onRequest')

  assert sender.sendRequest('foo') == 'oof'

  disconnect(sender, 'request')

  assert sender.sendRequest('bar') == None
