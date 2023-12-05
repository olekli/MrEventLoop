# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

MREVENTLOOP_EVENTS_ATTR = '__mreventloop_events_attr__'
MREVENTLOOP_EVENT_LOOP_ATTR = '__mreventloop_event_loop_attr__'
MREVENTLOOP_NONE_ATTR = '__mreventloop_none_attr__'

def getEventsAttr(cls):
  return getattr(cls, MREVENTLOOP_EVENTS_ATTR, MREVENTLOOP_NONE_ATTR)

def setEventsAttr(cls, events_attr):
  setattr(cls, MREVENTLOOP_EVENTS_ATTR, events_attr)

def getEvents(cls):
  return getattr(cls, getEventsAttr(cls), None)

def getEvent(cls, event_name):
  return getattr(getEvents(cls), event_name)

def setEvents(cls, events):
  setattr(cls, getEventsAttr(cls), events)

def getEventLoopAttr(cls):
  return getattr(cls, MREVENTLOOP_EVENT_LOOP_ATTR, MREVENTLOOP_NONE_ATTR)

def setEventLoopAttr(cls, event_loop_attr):
  setattr(cls, MREVENTLOOP_EVENT_LOOP_ATTR, event_loop_attr)

def getEventLoop(cls):
  return getattr(cls, getEventLoopAttr(cls), None)

def setEventLoop(cls, event_loop):
  setattr(cls, getEventLoopAttr(cls), event_loop)
