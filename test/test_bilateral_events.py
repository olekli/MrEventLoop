# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop import BilateralEvents

class Listener:
  def __init__(self):
    self.received = []

  def slot(self, item):
    self.received.append(item)
    return item[::-1]

def test_dispatches_correctly_with_listener():
  listener1 = Listener()
  events = BilateralEvents([ 'event1', 'event2' ])
  events.event1.addListener(listener1.slot)
  assert events.event1('foo') == 'oof'
  assert events.event1('bar') == 'rab'
  assert listener1.received == [ 'foo', 'bar' ]

def test_dispatches_correctly_with_multiple_listeners_on_multiple_events():
  listener1 = Listener()
  listener2 = Listener()
  events = BilateralEvents([ 'event1', 'event2' ])
  events.event1.addListener(listener1.slot)
  events.event2.addListener(listener2.slot)
  assert events.event1('foo') == 'oof'
  assert events.event2('123') == '321'
  assert events.event1('bar') == 'rab'
  assert events.event2('baz') == 'zab'
  assert listener1.received == [ 'foo', 'bar' ]
  assert listener2.received == [ '123', 'baz' ]

def test_dispatches_correctly_after_removing_listener():
  listener1 = Listener()
  listener2 = Listener()
  events = BilateralEvents([ 'event1', 'event2' ])
  events.event1.addListener(listener1.slot)
  assert events.event1('foo') == 'oof'

  events.event1.removeListener(listener1.slot)
  events.event1.addListener(listener2.slot)
  assert events.event1('bar') == 'rab'

  assert listener1.received == [ 'foo' ]
  assert listener2.received == [ 'bar' ]
