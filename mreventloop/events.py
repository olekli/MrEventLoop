# Copyright 2024 Ole Kliemann
# SPDX-License-Identifier: Apache-2.0

class Event:
  def __init__(self):
    self.listeners = []

  def addListener(self, slot):
    assert callable(slot)
    self.listeners.append(slot)

  def removeListener(self, slot):
    self.listeners.remove(slot)

  def clearListeners(self):
    self.listeners = []

  def __call__(self, *args, **kwargs):
    for slot in self.listeners:
      slot(*args, **kwargs)

class Events:
  def __init__(self, event_names):
    self.__event_names__ = []

    for event_name in event_names:
      self += event_name

  def __iadd__(self, event_name):
    self.__event_names__.append(event_name)
    setattr(self, event_name, Event())
    return self
