# Copyright 2024 Ole Kliemann
# SPDX-License-Identifier: Apache-2.0

import re

def eventToSlotName(event_name):
  segments = event_name.split('_')
  return 'on' + ''.join([ segment.capitalize() for segment in segments ])

def slotToEventName(slot_name):
  segments = re.split(r'(?=[A-Z])', slot_name)
  return '_'.join([ segment.lower() for segment in segments[1:] ])

def eventToRequestName(event_name):
  segments = event_name.split('_')
  return ''.join([segments[0]] + [segment.capitalize() for segment in segments[1:]])
