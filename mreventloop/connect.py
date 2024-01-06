# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop.attr import getEvents, getEvent
from mreventloop.names import eventToSlotName
from mreventloop.events import Events

def connect(*args, use_slot_names = True):
  if len(args) == 2 and isinstance(args[0], Events) and callable(args[1]):
    connectSingle(*args)
  elif len(args) == 4 and isinstance(args[1], str) and isinstance(args[3], str):
    connectSingleByName(*args)
  elif len(args) == 3 and isinstance(args[1], str) and callable(args[2]):
    connectSingleByNameFunction(*args)
  elif len(args) == 3 and isinstance(args[1], str) and not callable(args[2]):
    connectSingleByNameBlind(*args)
  elif len(args) == 4 and isinstance(args[1], list) and isinstance(args[3], list):
    connectList(*args)
  elif len(args) == 3 and isinstance(args[1], list):
    connectListBlind(*args)
  elif len(args) == 2 and not isinstance(args[0], Events) and not callable(args[1]) and use_slot_names:
    connectAllSlotNames(*args)
  elif len(args) == 2 and not isinstance(args[0], Events) and not callable(args[1]) and not use_slot_names:
    connectAllPlain(*args)
  else:
    assert False

def disconnect(*args, use_slot_names = True):
  if len(args) == 2 and isinstance(args[0], Events) and callable(args[1]):
    disconnectSingle(*args)
  elif len(args) == 4 and isinstance(args[1], str) and isinstance(args[3], str):
    disconnectSingleByName(*args)
  elif len(args) == 3 and isinstance(args[1], str) and callable(args[2]):
    disconnectSingleByNameFunction(*args)
  elif len(args) == 3 and isinstance(args[1], str) and not callable(args[2]):
    disconnectSingleByNameBlind(*args)
  elif len(args) == 4 and isinstance(args[1], list) and isinstance(args[3], list):
    disconnectList(*args)
  elif len(args) == 2 and not isinstance(args[0], Events) and not callable(args[1]) and use_slot_names:
    disconnectAllSlotNames(*args)
  elif len(args) == 2 and not isinstance(args[0], Events) and not callable(args[1]) and not use_slot_names:
    disconnectAllPlain(*args)
  elif len(args) == 1 and isinstance(args[0], Events):
    disconnectAllFromEvent(*args)
  elif len(args) == 2 and isinstance(args[1], str):
    disconnectAllFromEventName(*args)
  elif len(args) == 1 and not isinstance(args[0], Events):
    disconnectAllFromEmitter(*args)
  else:
    assert False

def connectSingle(event, slot):
  event.addListener(slot)

def disconnectSingle(event, slot):
  event.removeListener(slot)

def connectSingleByName(emitter, event_name, receiver, slot_name):
  connectSingle(getEvent(emitter, event_name), getattr(receiver, slot_name))

def disconnectSingleByName(emitter, event_name, receiver, slot_name):
  disconnectSingle(getEvent(emitter, event_name), getattr(receiver, slot_name))

def connectSingleByNameFunction(emitter, event_name, function):
  connectSingle(getEvent(emitter, event_name), function)

def disconnectSingleByNameFunction(emitter, event_name, function):
  disconnectSingle(getEvent(emitter, event_name), function)

def connectSingleByNameBlind(emitter, event_name, receiver, ignore_missing_slot = False):
  if not ignore_missing_slot or hasattr(receiver, eventToSlotName(event_name)):
    connectSingle(getEvent(emitter, event_name), getattr(receiver, eventToSlotName(event_name)))

def disconnectSingleByNameBlind(emitter, event_name, receiver, ignore_missing_slot = False):
  if not ignore_missing_slot or hasattr(receiver, eventToSlotName(event_name)):
    disconnectSingle(getEvent(emitter, event_name), getattr(receiver, eventToSlotName(event_name)))

def connectList(emitter, event_names, receiver, slot_names):
  for event_name, slot_name in zip(event_names, slot_names):
    connectSingleByName(emitter, event_name, receiver, slot_name)

def disconnectList(emitter, event_names, receiver, slot_names):
  for event_name, slot_name in zip(event_names, slot_names):
    disconnectSingleByName(emitter, event_name, receiver, slot_name)

def connectListBlind(emitter, event_names, receiver):
  for event_name in event_names:
    connectSingleByNameBlind(emitter, event_name, receiver)

def disconnectListBlind(emitter, event_names, receiver):
  for event_name in event_names:
    disconnectSingleByNameBlind(emitter, event_name, receiver)

def connectAllPlain(emitter, receiver):
  for event_name in getEvents(emitter).__event_names__:
    connectSingleByName(emitter, event_name, receiver, event_name, ignore_missing_slot = True)

def disconnectAllPlain(emitter, receiver):
  for event_name in getEvents(emitter).__event_names__:
    disconnectSingleByName(emitter, event_name, receiver, event_name, ignore_missing_slot = True)

def connectAllSlotNames(emitter, receiver):
  for event_name in getEvents(emitter).__event_names__:
    connectSingleByNameBlind(emitter, event_name, receiver, ignore_missing_slot = True)

def disconnectAllSlotNames(emitter, receiver):
  for event_name in getEvents(emitter).__event_names__:
    disconnectSingleByNameBlind(emitter, event_name, receiver, ignore_missing_slot = True)

def disconnectAllFromEvent(event):
  event.clearListeners()

def disconnectAllFromEventName(emitter, event_name):
  getEvent(emitter, event_name).clearListeners()

def disconnectAllFromEmitter(emitter):
  for event_name in getEvents(emitter).__event_names__:
    disconnectAllFromEventName(emitter, event_name)
