# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import inspect
from functools import partial
from mreventloop.attr import getEvents, setEventsAttr, setEvents, setEventLoopAttr, getEvent, getEventLoop, setEventLoop
from mreventloop.names import slotToEventName
from mreventloop.events import Events

def emits(events_attr, event_names):
  def emits_(cls):
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
      setEventsAttr(self, events_attr)
      setEvents(self, Events(event_names))
      original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls
  return emits_

def supports_event_loop(event_loop_attr):
  def supports_event_loop_(cls):
    setEventLoopAttr(cls, event_loop_attr)
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
      setEventLoop(self, asyncio.get_event_loop())
      original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls
  return supports_event_loop_

def slot(method):
  if inspect.iscoroutinefunction(method):
    def wrapper(self, *args, **kwargs):
      event_loop = getEventLoop(self)
      if event_loop:
        assert event_loop is asyncio.get_event_loop()
        return asyncio.create_task(method(self, *args, **kwargs))
      else:
        return method(self, *args, **kwargs)
  else:
    def wrapper(self, *args, **kwargs):
      event_loop = getEventLoop(self)
      if event_loop:
        assert event_loop is asyncio.get_event_loop()
        return event_loop.call_soon(lambda: method(self, *args, **kwargs))
      else:
        return method(self, *args, **kwargs)
  return wrapper

def forwards(slot_names, event_names = None):
  def forwards_(cls, event_names = event_names):
    if not event_names:
      event_names = list()
      for slot_name in slot_names:
        event_names.append(slotToEventName(slot_name))

    assert len(slot_names) == len(event_names)

    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
      original_init(self, *args, **kwargs)
      for slot_name, event_name in zip(slot_names, event_names):
        setattr(self, slot_name, getEvent(self, event_name))
    cls.__init__ = new_init
    return cls
  return forwards_
