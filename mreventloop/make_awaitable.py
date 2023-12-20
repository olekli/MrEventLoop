# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import inspect

async def make_awaitable(result):
  if inspect.isawaitable(result):
    return await result
  else:
    return result
