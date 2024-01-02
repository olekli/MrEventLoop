# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import asyncio
from mreventloop import Events, SyncEvent

@pytest.mark.asyncio
async def test_no_async():
  events = Events([ 'event1', 'event2' ])
  sync = SyncEvent(events.event1)
  events.event1('foo')
  events.event1('bar')
  result = await sync
  assert result == 'foo'

@pytest.mark.asyncio
async def test_async():
  events = Events([ 'event1', 'event2' ])
  sync = SyncEvent(events.event1)
  async def emit(s):
    events.event1(s)
  asyncio.create_task(emit('foo'))
  result = await sync
  assert result == 'foo'

@pytest.mark.asyncio
async def test_async_multiple_args():
  events = Events([ 'event1', 'event2' ])
  sync = SyncEvent(events.event1)
  async def emit(s, r):
    events.event1(s, r)
  asyncio.create_task(emit('foo', 'bar'))
  result = await sync
  assert result == [ 'foo', 'bar' ]

@pytest.mark.asyncio
async def test_async_kwargs():
  events = Events([ 'event1', 'event2' ])
  sync = SyncEvent(events.event1)
  async def emit(s, r):
    events.event1(first = s, second = r)
  asyncio.create_task(emit('foo', 'bar'))
  result = await sync
  assert result == { 'first': 'foo', 'second': 'bar' }

@pytest.mark.asyncio
async def test_async_args_kwargs():
  events = Events([ 'event1', 'event2' ])
  sync = SyncEvent(events.event1)
  async def emit(s, r):
    events.event1(r, s, first = s, second = r)
  asyncio.create_task(emit('foo', 'bar'))
  result = await sync
  assert result == ( [ 'bar', 'foo' ], { 'first': 'foo', 'second': 'bar' } )
