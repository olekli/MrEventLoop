# MrEventLoop

Simple event system for Python.


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
connect(producer, 'produced', None, lambda product: print(f'{product}'))
```
The receiver is `None` in this case as there is no receiving object, just a callback.

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
