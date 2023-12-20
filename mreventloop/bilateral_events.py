# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

logger = logging.getLogger(__name__)

class BilateralEvent:
  def __init__(self):
    self.listener = None

  def addListener(self, slot):
    assert not self.listener
    self.listener = slot

  def removeListener(self, slot):
    if self.listener.__self__ is slot.__self__ and self.listener.__func__ is slot.__func__:
      self.listener = None

  def __call__(self, *args, **kwargs):
    assert callable(self.listener)
    return self.listener(*args, **kwargs)

class BilateralEvents:
  def __init__(self, event_names):
    self.__event_names__ = event_names

    for event_name in event_names:
      setattr(
        self,
        event_name,
        BilateralEvent()
      )
