# MrEventLoop
Simple event system for Python building on `asyncio` and working seamlessly across sockets.

### Installation
```
pip install mreventloop
```

### Emitting Events
```python
from mreventloop import emits

@emits('events', [ 'produced' ])
class Producer:
  def requestProduct(self):
    self.events.produced('some product')
```

You can now connect a callback to the event:
```python
from mreventloop import connect

producer = Producer()
connect(producer, 'produced', lambda product: print(f'{product}'))
```
You can disconnect all listeners from an event:
```python
from mreventloop import disconnect
disconnect(producer, 'produced')
```

### Event Loop and Slots
Objects can have an event loop building on `asyncio`:
```python
from mreventloop import has_event_loop, slot

@has_event_loop('event_loop')
class Consumer:
  @slot
  def onProduced(self, product):
    print(f'{product}')
```
Calling a `@slot` will not run the corresponding method directly,
but queue its execution on the object's event loop.
The event loop will run them strictly sequentially in FIFO order.
Thus, slots do not need to be reentrant.

The event loop has to be started:
```python
consumer = Consumer()
connect(producer, 'produced', consumer, 'onProduced')
async with consumer.event_loop:
  producer.requestProduct()
```
After exiting, the event loop will still process all queued events.

When creating an object that `has_event_loop`,
an event loop will automatically be created.
But you can also share event loops between objects:
```python
producer1 = Producer()
producer2 = Producer()
consumer1 = Consumer()
consumer2 = Consumer()
consumer2.event_loop = consumer1.event_loop
connect(producer1, 'produced', consumer1, 'onProduced')
connect(producer2, 'produced', consumer2, 'onProduced')
async with consumer1.event_loop:
  producer1.requestProduct()
  producer2.requestProduct()
```
All calls to slots in both `consumer1` and `consumer2` will be run sequentially.

### Async Slots
Slots can also be coroutines:
```python
import asyncio

@has_event_loop('event_loop')
class ConsumerAsync:
  @slot
  async def onProduced(self, product):
    await asyncio.sleep(0.1)
    print(f'{product}')
```
The coroutine will be awaited inside the event loop.


### Awaiting Events
Events can be awaited:
```python
from mreventloop import SyncEvent

producer = Producer()
sync_event = SyncEvent(producer.events.produced)

async def emit():
  producer.requestProduct()

asyncio.create_task(emit())
result = await sync_event
print(f'{result}')
```

### Events of the Event Loop
The event loop itself emits the following events:
```
[ 'started', 'stopped', 'active', 'idle', 'exception' ]
```

### Exceptions on the Event Loop
If an exception ocurrs executing a slot, the app will exit.
This can be prevented by creating the loop manually with:
```python
from mreventloop import EventLoop

consumer.event_loop = EventLoop(exit_on_exception = False)
```
In this case, any exception will be emitted through the `exception` event.

(The general idea here is to just not use exceptions.)


### Crossing Sockets
Events and slots across multiple applications can be connected via sockets.
This requires one instance of a `Broker` and any number of `Peer`s.
A `Peer` subscribes to a number of events.
If any other `Peer` publishes such events,
they will be emitted by the subscribing `Peer`.

```python
from mreventloop import Broker, Peer

in_socket_path = 'ipc:///tmp/mreventloop_test_in.sock'
out_socket_path = 'ipc:///tmp/mreventloop_test_out.sock'

producer_peer = Peer(in_socket_path, out_socket_path, [ 'request_product' ], [ 'produced' ])
consumer_peer = Peer(in_socket_path, out_socket_path, [ 'produced' ], [ 'request_product' ])
async with Broker(in_socket_path, out_socket_path), producer_peer, consumer_peer:
  consumer = Consumer()
  connect(consumer, 'request_product', consumer_peer.publish, 'request_product')
  connect(consumer_peer, 'product', consumer, 'onProduct')

  producer = Producer()
  connect(producer, 'produce', producer_peer.publish, 'produce')
  connect(producer_peer, 'request_product', producer, 'onRequestProduct')

  async with producer.event_loop, consumer.event_loop:
    consumer.events.request_product()
```
