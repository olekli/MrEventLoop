# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

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
    self.__event_names__ = event_names

    for event_name in event_names:
      setattr(
        self,
        event_name,
        Event()
      )
