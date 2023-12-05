# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop.attr import getEvents, setEventsAttr, setEvents, setEventLoopAttr
from mreventloop.names import eventToSlotName

def connect_(emitter, event_name, receiver, slot_name):
  event = getattr(getEvents(emitter), event_name)
  event.addListener(getattr(receiver, slot_name))

def connect(emitter, event_name, receiver, slot_name):
  if event_name == None and slot_name == None:
    for event_name in getEvents(emitter).__event_names__:
      slot_name = eventToSlotName(event_name)
      if callable(getattr(receiver, slot_name, None)):
        connect_(emitter, event_name, receiver, slot_name)

  elif isinstance(event_name, list) and isinstance(slot_name, list):
    assert len(event_name) == len(slot_name)
    for e, s in zip(event_name, slot_name):
      connect_(emitter, e, receiver, s)

  elif isinstance(event_name, list) and slot_name == None:
    for e in event_name:
      connect_(emitter, e, receiver, eventToSlotName(e))

  elif isinstance(event_name, str) and isinstance(slot_name, str):
    connect_(emitter, event_name, receiver, slot_name)

  else:
    assert False
