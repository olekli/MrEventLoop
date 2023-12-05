# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import threading

def assert_thread(method):
  def wrapper(self, *args, **kwargs):
    if not hasattr(self, '__mreventloop_thread__'):
      self.__mreventloop_thread__ = threading.get_ident()
    else:
      assert self.__mreventloop_thread__ == threading.get_ident()
    return method(self, *args, **kwargs)
  return wrapper
