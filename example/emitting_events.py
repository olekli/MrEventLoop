# Copyright 2023 Ole Kliemann
# SPDX-License-Identifier: GPL-3.0-or-later

from mreventloop import emits
from mreventloop import connect
from mreventloop import disconnect

@emits('events', [ 'produced' ])
class Producer:
  def requestProduct(self):
    self.events.produced('some product')

producer = Producer()
connect(producer, 'produced', lambda product: print(f'{product}'))
producer.requestProduct()

disconnect(producer, 'produced')
producer.requestProduct()
