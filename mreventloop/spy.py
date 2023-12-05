# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from functools import partial

class Spy:
  def __init__(self, slot_names):
    self.__result__ = dict()
    for slot_name in slot_names:
      setattr(self, slot_name, partial(self.__store__, slot_name))

  def __store__(self, slot_name, *args, **kwargs):
    self.__result__.setdefault(slot_name, []).append( (args, kwargs) )
