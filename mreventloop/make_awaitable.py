# Copyright 2024 Ole Kliemann
# SPDX-License-Identifier: Apache-2.0

import inspect

async def make_awaitable(result):
  if inspect.isawaitable(result):
    return await result
  else:
    return result
