# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop import Events

class Listener:
  def __init__(self):
    self.received = []

  def slot(self, item):
    self.received.append(item)

def test_dispatches_correctly_with_one_listener():
  listener1 = Listener()
  events = Events([ 'event1', 'event2' ])
  events.event1.addListener(listener1.slot)
  events.event1('foo')
  events.event1('bar')
  assert listener1.received == [ 'foo', 'bar' ]

def test_dispatches_correctly_with_multiple_listeners_on_one_event():
  listener1 = Listener()
  listener2 = Listener()
  events = Events([ 'event1', 'event2' ])
  events.event1.addListener(listener1.slot)
  events.event1.addListener(listener2.slot)
  events.event1('foo')
  events.event1('bar')
  assert listener1.received == [ 'foo', 'bar' ]
  assert listener2.received == [ 'foo', 'bar' ]

def test_dispatches_correctly_with_multiple_listeners_on_multiple_events():
  listener1_1 = Listener()
  listener1_2 = Listener()
  listener2_1 = Listener()
  listener2_2 = Listener()
  events = Events([ 'event1', 'event2' ])
  events.event1.addListener(listener1_1.slot)
  events.event2.addListener(listener2_1.slot)
  events.event1.addListener(listener1_2.slot)
  events.event2.addListener(listener2_2.slot)
  events.event1('foo')
  events.event2('baz')
  events.event1('bar')
  events.event2('123')
  assert listener1_1.received == [ 'foo', 'bar' ]
  assert listener1_2.received == [ 'foo', 'bar' ]
  assert listener2_1.received == [ 'baz', '123' ]
  assert listener2_2.received == [ 'baz', '123' ]

def test_dispatches_correctly_after_removing_listener():
  listener1_1 = Listener()
  listener1_2 = Listener()
  listener2_1 = Listener()
  listener2_2 = Listener()
  events = Events([ 'event1', 'event2' ])
  events.event1.addListener(listener1_1.slot)
  events.event2.addListener(listener2_1.slot)
  events.event1.addListener(listener1_2.slot)
  events.event2.addListener(listener2_2.slot)
  events.event1('foo')
  events.event2('baz')
  events.event1('bar')
  events.event2('123')

  events.event1.removeListener(listener1_1.slot)

  events.event1('456')

  assert listener1_1.received == [ 'foo', 'bar' ]
  assert listener1_2.received == [ 'foo', 'bar', '456' ]
  assert listener2_1.received == [ 'baz', '123' ]
  assert listener2_2.received == [ 'baz', '123' ]
