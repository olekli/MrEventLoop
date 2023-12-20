# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

import re

def eventToSlotName(event_name):
  segments = event_name.split('_')
  return 'on' + ''.join([ segment.capitalize() for segment in segments ])

def slotToEventName(slot_name):
  segments = re.split(r'(?=[A-Z])', slot_name)
  return '_'.join([ segment.lower() for segment in segments[1:] ])

def eventToRequestName(event_name):
  return eventToSlotName(f'request_{event_name}')
