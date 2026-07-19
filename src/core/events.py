"""
Event System for AI Operating System
Enables communication between components through events.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime
import threading
import queue
import logging
import uuid
import json
import argparse
import signal
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EventSystem')


class EventType(Enum):
    """Event types for the AI Operating System."""
    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_FAILED = "agent.failed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


@dataclass
class EventFilter:
    """Filter for events based on various criteria."""
    event_types: Optional[Set[EventType]] = None
    source_pattern: Optional[str] = None
    data_filter: Optional[Callable[[Dict], bool]] = None
    
    def matches(self, event: 'Event') -> bool:
        """Check if an event matches this filter."""
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.source_pattern and self.source_pattern not in event.source:
            return False
        if self.data_filter and not self.data_filter(event.data):
            return False
        return True


@dataclass
class Event:
    """Represents an event in the system."""
    id: str
    event_type: EventType
    source: str
    data: Dict
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create event from dictionary."""
        return cls(
            id=data['id'],
            event_type=EventType(data['event_type']),
            source=data['source'],
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class Subscription:
    """Represents a subscription to an event type."""
    handler: Callable
    priority: int = 0
    event_filter: Optional[EventFilter] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventBus:
    """Event bus for publishing and subscribing to events."""
    
    def __init__(self, max_history: int = 1000):
        self.subscribers: Dict[str, List[Subscription]] = {}
        self.event_history: List[Event] = []
        self.event_queue: queue.Queue = queue.Queue()
        self.running = False
        self.max_history = max_history
        self.lock = threading.RLock()
        self.processor_thread: Optional[threading.Thread] = None
        self.stats = {
            'published': 0,
            'processed': 0,
            'errors': 0
        }
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        return str(uuid.uuid4())
    
    def publish(self, event: Event, async_mode: bool = False) -> str:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
            async_mode: If True, queue event for async processing
            
        Returns:
            The event ID
        """
        with self.lock:
            self.stats['published'] += 1
        
        if async_mode:
            self.event_queue.put(event)
            logger.debug(f"Event queued: {event.event_type.value} from {event.source}")
        else:
            self._process_event(event)
        
        return event.id
    
    def create_and_publish(
        self,
        event_type: EventType,
        source: str,
        data: Dict,
        metadata: Optional[Dict] = None,
        async_mode: bool = False
    ) -> str:
        """Create and publish an event."""
        event = Event(
            id=self._generate_event_id(),
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        return self.publish(event, async_mode)
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        priority: int = 0,
        event_filter: Optional[EventFilter] = None
    ) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type string or '*' for wildcard
            handler: Callback function to handle events
            priority: Higher priority handlers run first
            event_filter: Optional filter for events
            
        Returns:
            Subscription ID
        """
        with self.lock:
            subscription = Subscription(
                handler=handler,
                priority=priority,
                event_filter=event_filter
            )
            
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            
            self.subscribers[event_type].append(subscription)
            self.subscribers[event_type].sort(
                key=lambda s: s.priority,
                reverse=True
            )
            
            logger.debug(f"Subscribed to {event_type} with priority {priority}")
            return subscription.id
    
    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type string
            subscription_id: Subscription ID to remove
            
        Returns:
            True if unsubscribed, False otherwise
        """
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type] = [
                    s for s in self.subscribers[event_type]
                    if s.id != subscription_id
                ]
                logger.debug(f"Unsubscribed from {event_type}")
                return True
            return False
    
    def _process_event(self, event: Event) -> None:
        """Process an event by calling all matching handlers."""
        with self.lock:
            self.stats['processed'] += 1
            self._add_to_history(event)
        
        handlers_called = []
        
        with self.lock:
            specific_handlers = self.subscribers.get(event.event_type.value, [])
            wildcard_handlers = self.subscribers.get('*', [])
            all_handlers = specific_handlers + wildcard_handlers
        
        for subscription in all_handlers:
            try:
                if subscription.event_filter and not subscription.event_filter.matches(event):
                    continue
                
                subscription.handler(event)
                handlers_called.append(subscription.id)
                
            except Exception as e:
                with self.lock:
                    self.stats['errors'] += 1
                logger.error(f"Error in event handler: {e}")
        
        logger.debug(
            f"Processed event {event.event_type.value} "
            f"with {len(handlers_called)} handlers"
        )
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit."""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
    
    def start(self) -> None:
        """Start the event bus processor."""
        if self.running:
            logger.warning("Event bus is already running")
            return
        
        self.running = True
        self.processor_thread = threading.Thread(
            target=self._process_queue,
            daemon=True,
            name="EventBus-Processor"
        )
        self.processor_thread.start()
        logger.info("Event bus started")
    
    def stop(self) -> None:
        """Stop the event bus processor."""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Event bus stopped")
    
    def _process_queue(self) -> None:
        """Process events from the queue."""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self._process_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self.lock:
            if event_type:
                events = [e for e in self.event_history if e.event_type == event_type]
            else:
                events = self.event_history.copy()
            
            if limit:
                events = events[-limit:]
            
            return events
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self.lock:
            self.event_history.clear()
            logger.info("Event history cleared")
    
    def get_stats(self) -> Dict:
        """Get event bus statistics."""
        with self.lock:
            return {
                **self.stats,
                'queue_size': self.event_queue.qsize(),
                'subscribers': sum(len(handlers) for handlers in self.subscribers.values()),
                'history_size': len(self.event_history)
            }
    
    def archive_events(self, filename: str) -> int:
        """
        Archive events to a JSON file.
        
        Args:
            filename: Path to archive file
            
        Returns:
            Number of events archived
        """
        with self.lock:
            events_to_archive = self.event_history.copy()
        
        with open(filename, 'w') as f:
            json.dump(
                [e.to_dict() for e in events_to_archive],
                f,
                indent=2
            )
        
        logger.info(f"Archived {len(events_to_archive)} events to {filename}")
        return len(events_to_archive)
    
    def load_archive(self, filename: str) -> int:
        """
        Load events from an archive file.
        
        Args:
            filename: Path to archive file
            
        Returns:
            Number of events loaded
        """
        with open(filename, 'r') as f:
            events_data = json.load(f)
        
        events = [Event.from_dict(e) for e in events_data]
        
        with self.lock:
            self.event_history.extend(events)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
        
        logger.info(f"Loaded {len(events)} events from {filename}")
        return len(events)
    
    def replay_events(
        self,
        events: Optional[List[Event]] = None,
        delay: float = 0.1
    ) -> None:
        """
        Replay events.
        
        Args:
            events: Events to replay (defaults to history)
            delay: Delay between events in seconds
        """
        if events is None:
            events = self.get_history()
        
        for event in events:
            self._process_event(event)
            time.sleep(delay)


def create_event(
    event_type: EventType,
    source: str,
    data: Dict,
    metadata: Optional[Dict] = None
) -> Event:
    """Helper function to create an event."""
    return Event(
        id=str(uuid.uuid4()),
        event_type=event_type,
        source=source,
        data=data,
        timestamp=datetime.now(),
        metadata=metadata or {}
    )


class CLIInterface:
    """CLI interface for testing the event system."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.running = False
    
    def handle_event(self, event: Event) -> None:
        """Handle received events."""
        print(f"\n{'='*60}")
        print(f"Event Received: {event.event_type.value}")
        print(f"ID: {event.id}")
        print(f"Source: {event.source}")
        print(f"Time: {event.timestamp.isoformat()}")
        print(f"Data: {json.dumps(event.data, indent=2)}")
        if event.metadata:
            print(f"Metadata: {json.dumps(event.metadata, indent=2)}")
        print(f"{'='*60}\n")
    
    def publish_event(self, event_type_str: str, data_str: str) -> None:
        """Publish an event from CLI."""
        try:
            event_type = EventType(event_type_str)
            data = json.loads(data_str) if data_str else {}
            
            event = create_event(
                event_type=event_type,
                source="cli",
                data=data
            )
            
            self.event_bus.publish(event)
            print(f"Published event: {event.id}")
            print(f"Type: {event_type.value}")
            print(f"Data: {json.dumps(data, indent=2)}")
            
        except ValueError as e:
            print(f"Error: Invalid event type '{event_type_str}'")
            print(f"Valid types: {[t.value for t in EventType]}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON data: {e}")
    
    def subscribe_to_events(self, event_type_str: str) -> None:
        """Subscribe to events from CLI."""
        event_type = event_type_str if event_type_str == '*' else event_type_str
        
        subscription_id = self.event_bus.subscribe(
            event_type=event_type,
            handler=self.handle_event
        )
        
        print(f"Subscribed to {event_type}")
        print(f"Subscription ID: {subscription_id}")
        print("Waiting for events... (Press Ctrl+C to stop)")
        
        self.running = True
        self.event_bus.start()
        
        def signal_handler(sig, frame):
            self.running = False
            print("\nStopping...")
        
        signal.signal(signal.SIGINT, signal_handler)
        
        while self.running:
            time.sleep(0.1)
        
        self.event_bus.stop()
    
    def show_history(self, event_type_str: Optional[str] = None) -> None:
        """Show event history."""
        event_type = None
        if event_type_str:
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                print(f"Invalid event type: {event_type_str}")
                return
        
        events = self.event_bus.get_history(event_type)
        
        if not events:
            print("No events in history")
            return
        
        print(f"\nEvent History ({len(events)} events):")
        print("="*60)
        
        for event in events:
            print(f"\nID: {event.id}")
            print(f"Type: {event.event_type.value}")
            print(f"Source: {event.source}")
            print(f"Time: {event.timestamp.isoformat()}")
            print(f"Data: {json.dumps(event.data, indent=2)}")
            print("-"*40)
    
    def show_stats(self) -> None:
        """Show event bus statistics."""
        stats = self.event_bus.get_stats()
        
        print("\nEvent Bus Statistics:")
        print("="*40)
        print(f"Events Published: {stats['published']}")
        print(f"Events Processed: {stats['processed']}")
        print(f"Errors: {stats['errors']}")
        print(f"Queue Size: {stats['queue_size']}")
        print(f"Subscribers: {stats['subscribers']}")
        print(f"History Size: {stats['history_size']}")
        print("="*40)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='AI Operating System Event System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python events.py --publish task.created '{"task_id": "123"}'
  python events.py --subscribe task.created
  python events.py --subscribe '*'
  python events.py --history
  python events.py --history task.created
  python events.py --stats
  python events.py --archive events.json
  python events.py --load events.json
        """
    )
    
    parser.add_argument(
        '--publish',
        nargs=2,
        metavar=('EVENT_TYPE', 'DATA'),
        help='Publish an event (JSON data)'
    )
    
    parser.add_argument(
        '--subscribe',
        metavar='EVENT_TYPE',
        help='Subscribe to events (* for all)'
    )
    
    parser.add_argument(
        '--history',
        nargs='?',
        const=None,
        metavar='EVENT_TYPE',
        help='Show event history'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show event bus statistics'
    )
    
    parser.add_argument(
        '--archive',
        metavar='FILENAME',
        help='Archive events to file'
    )
    
    parser.add_argument(
        '--load',
        metavar='FILENAME',
        help='Load events from archive'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear event history'
    )
    
    args = parser.parse_args()
    cli = CLIInterface()
    
    if args.publish:
        event_type, data = args.publish
        cli.publish_event(event_type, data)
    elif args.subscribe:
        cli.subscribe_to_events(args.subscribe)
    elif args.history is not None or (args.history is None and not args.stats and not args.archive and not args.load and not args.clear and not args.publish and not args.subscribe):
        cli.show_history(args.history)
    elif args.stats:
        cli.show_stats()
    elif args.archive:
        count = cli.event_bus.archive_events(args.archive)
        print(f"Archived {count} events to {args.archive}")
    elif args.load:
        count = cli.event_bus.load_archive(args.load)
        print(f"Loaded {count} events from {args.load}")
    elif args.clear:
        cli.event_bus.clear_history()
        print("History cleared")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
