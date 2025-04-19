"""
Example showing how to set up and use the event subscription management system.

This example demonstrates:
1. Setting up the subscription manager with a PostgreSQL event store
2. Registering event types
3. Creating subscriptions
4. Setting up the FastAPI endpoints for subscription management
5. Integrating the web UI component
"""

import os
import asyncio
import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from uno.core.events import (
    AsyncEventBus, 
    Event, 
    PostgresEventStore, 
    PostgresEventStoreConfig,
    EventPublisher,
    SubscriptionManager,
    SubscriptionRepository,
    SubscriptionConfig,
    EventTypeInfo,
    create_subscription_router
)


# Define some sample events
class UserCreated(Event):
    """Event emitted when a user is created."""
    user_id: str
    username: str
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def aggregate_id(self) -> str:
        return self.user_id
    
    @property
    def aggregate_type(self) -> str:
        return "user"


class OrderCreated(Event):
    """Event emitted when an order is created."""
    order_id: str
    user_id: str
    total_amount: float
    items: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def aggregate_id(self) -> str:
        return self.order_id
    
    @property
    def aggregate_type(self) -> str:
        return "order"


# Define sample event handlers
async def send_welcome_email(event: UserCreated):
    """Send a welcome email to a new user."""
    print(f"[EMAIL] Sending welcome email to {event.email}")
    # Simulate processing delay
    await asyncio.sleep(0.1)
    print(f"[EMAIL] Welcome email sent to {event.username} <{event.email}>")


async def create_user_profile(event: UserCreated):
    """Create a default profile for a new user."""
    print(f"[PROFILE] Creating profile for user {event.username}")
    # Simulate processing delay
    await asyncio.sleep(0.2)
    print(f"[PROFILE] Profile created for user {event.username}")


async def notify_inventory(event: OrderCreated):
    """Notify inventory system about a new order."""
    print(f"[INVENTORY] Processing order {event.order_id} for inventory")
    # Simulate processing delay
    await asyncio.sleep(0.15)
    
    # Occasionally fail to demonstrate error handling
    if sum(item.get("quantity", 0) for item in event.items) > 10:
        raise ValueError(f"Order {event.order_id} exceeds inventory capacity")
    
    print(f"[INVENTORY] Order {event.order_id} processed for inventory")


# FastAPI app setup
app = FastAPI(title="UNO Event Subscription Management Example")

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)

# Create template file if it doesn't exist
template_path = os.path.join(templates_dir, "subscription_manager.html")
if not os.path.exists(template_path):
    with open(template_path, "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Subscription Manager</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 16px;
        }
        header {
            background-color: #3f51b5;
            color: white;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header h1 {
            margin: 0;
            font-size: 24px;
        }
        main {
            padding: 16px;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Event Subscription Manager</h1>
        </div>
    </header>
    <main>
        <div class="container">
            <wa-event-subscription-manager baseUrl="/api/events"></wa-event-subscription-manager>
        </div>
    </main>
    
    <script type="module">
        import { WebAwesomeEventSubscriptionManager } from '/static/components/events/wa-event-subscription-manager.js';
        
        // If you need to add custom elements for the UI
        customElements.define('wa-select', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                        }
                        label {
                            display: block;
                            margin-bottom: 8px;
                            font-weight: 500;
                        }
                        select {
                            width: 100%;
                            padding: 8px;
                            border: 1px solid #e0e0e0;
                            border-radius: 4px;
                        }
                    </style>
                    <label><slot name="label"></slot></label>
                    <select>
                        <slot></slot>
                    </select>
                `;
                
                this._select = this.shadowRoot.querySelector('select');
                this._select.addEventListener('change', (e) => {
                    this.dispatchEvent(new CustomEvent('change', {
                        detail: { value: this._select.value }
                    }));
                });
            }
            
            get value() {
                return this._select.value;
            }
            
            set value(val) {
                this._select.value = val;
            }
        });
        
        customElements.define('wa-option', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <option value="${this.getAttribute('value')}">
                        <slot></slot>
                    </option>
                `;
            }
        });
        
        customElements.define('wa-switch', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: inline-block;
                        }
                        .switch {
                            position: relative;
                            display: inline-block;
                            width: 40px;
                            height: 20px;
                        }
                        .switch input {
                            opacity: 0;
                            width: 0;
                            height: 0;
                        }
                        .slider {
                            position: absolute;
                            cursor: pointer;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            background-color: #ccc;
                            transition: .4s;
                            border-radius: 20px;
                        }
                        .slider:before {
                            position: absolute;
                            content: "";
                            height: 16px;
                            width: 16px;
                            left: 2px;
                            bottom: 2px;
                            background-color: white;
                            transition: .4s;
                            border-radius: 50%;
                        }
                        input:checked + .slider {
                            background-color: #3f51b5;
                        }
                        input:checked + .slider:before {
                            transform: translateX(20px);
                        }
                    </style>
                    <label class="switch">
                        <input type="checkbox">
                        <span class="slider"></span>
                    </label>
                `;
                
                this._input = this.shadowRoot.querySelector('input');
                this._input.addEventListener('change', (e) => {
                    this.dispatchEvent(new CustomEvent('change', {
                        detail: { checked: this._input.checked }
                    }));
                });
            }
            
            get checked() {
                return this._input.checked;
            }
            
            set checked(val) {
                this._input.checked = val;
            }
        });
        
        customElements.define('wa-tabs', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                        }
                        .tabs {
                            display: flex;
                            gap: 4px;
                            margin-bottom: 16px;
                            border-bottom: 1px solid #e0e0e0;
                        }
                    </style>
                    <div class="tabs">
                        <slot></slot>
                    </div>
                `;
                
                // Handle tab selection
                this.addEventListener('tab-selected', (e) => {
                    this.value = e.detail.value;
                    this.dispatchEvent(new CustomEvent('change', {
                        detail: { value: e.detail.value }
                    }));
                });
            }
            
            get value() {
                return this.getAttribute('value');
            }
            
            set value(val) {
                this.setAttribute('value', val);
                // Update all child tabs
                const tabs = this.querySelectorAll('wa-tab');
                tabs.forEach(tab => {
                    tab.active = tab.value === val;
                });
            }
        });
        
        customElements.define('wa-tab', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                        }
                        button {
                            padding: 8px 16px;
                            border: none;
                            background: transparent;
                            cursor: pointer;
                            font-family: inherit;
                            font-size: inherit;
                            color: inherit;
                            border-bottom: 2px solid transparent;
                        }
                        button.active {
                            border-bottom: 2px solid #3f51b5;
                            color: #3f51b5;
                        }
                    </style>
                    <button><slot></slot></button>
                `;
                
                this._button = this.shadowRoot.querySelector('button');
                this._button.addEventListener('click', () => {
                    this.dispatchEvent(new CustomEvent('tab-selected', {
                        detail: { value: this.value },
                        bubbles: true,
                        composed: true
                    }));
                });
                
                this._updateActive();
            }
            
            static get observedAttributes() {
                return ['active', 'value'];
            }
            
            attributeChangedCallback(name, oldValue, newValue) {
                if (name === 'active') {
                    this._updateActive();
                }
            }
            
            get value() {
                return this.getAttribute('value');
            }
            
            get active() {
                return this.hasAttribute('active');
            }
            
            set active(val) {
                if (val) {
                    this.setAttribute('active', '');
                } else {
                    this.removeAttribute('active');
                }
                this._updateActive();
            }
            
            _updateActive() {
                if (this.active) {
                    this._button.classList.add('active');
                } else {
                    this._button.classList.remove('active');
                }
            }
        });
        
        customElements.define('wa-tab-panel', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                        }
                        .panel {
                            display: none;
                        }
                        .panel.active {
                            display: block;
                        }
                    </style>
                    <div class="panel">
                        <slot></slot>
                    </div>
                `;
                
                this._panel = this.shadowRoot.querySelector('.panel');
                this._updateActive();
            }
            
            static get observedAttributes() {
                return ['active'];
            }
            
            attributeChangedCallback(name, oldValue, newValue) {
                if (name === 'active') {
                    this._updateActive();
                }
            }
            
            get active() {
                return this.hasAttribute('active');
            }
            
            set active(val) {
                if (val) {
                    this.setAttribute('active', '');
                } else {
                    this.removeAttribute('active');
                }
                this._updateActive();
            }
            
            _updateActive() {
                if (this.active) {
                    this._panel.classList.add('active');
                } else {
                    this._panel.classList.remove('active');
                }
            }
        });
        
        customElements.define('wa-spinner', class extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
                this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: inline-block;
                        }
                        .spinner {
                            width: 24px;
                            height: 24px;
                            border: 3px solid rgba(0,0,0,0.1);
                            border-top: 3px solid #3f51b5;
                            border-radius: 50%;
                            animation: spin 1s linear infinite;
                        }
                        .small {
                            width: 16px;
                            height: 16px;
                            border-width: 2px;
                        }
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                    <div class="spinner"></div>
                `;
                
                this._spinner = this.shadowRoot.querySelector('.spinner');
                if (this.getAttribute('size') === 'small') {
                    this._spinner.classList.add('small');
                }
            }
        });
    </script>
</body>
</html>""")

# Set up static files serving
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global variables for event system components
event_bus = None
event_store = None
event_publisher = None
subscription_manager = None


async def get_event_bus():
    """Dependency for getting the event bus."""
    return event_bus


async def get_subscription_manager():
    """Dependency for getting the subscription manager."""
    return subscription_manager


async def setup_event_system():
    """Set up the event system components."""
    global event_bus, event_store, event_publisher, subscription_manager
    
    # Create the event bus
    event_bus = AsyncEventBus(max_concurrency=10)
    
    # Set up the event store
    config = PostgresEventStoreConfig(
        connection_string="postgresql+asyncpg://postgres:postgres@localhost:5432/events",
        schema="events",
        table_name="events",
        create_schema_if_missing=True
    )
    event_store = PostgresEventStore(config=config)
    
    # Initialize the event store
    await event_store.initialize()
    
    # Create the event publisher
    event_publisher = EventPublisher(event_bus=event_bus, event_store=event_store)
    
    # Set up the subscription repository
    repository = SubscriptionRepository()
    
    # Create the subscription manager
    subscription_manager = SubscriptionManager(
        event_bus=event_bus,
        repository=repository,
        auto_load=True
    )
    
    # Initialize the subscription manager
    await subscription_manager.initialize()
    
    # Register event types
    await repository.register_event_type(EventTypeInfo(
        name="UserCreated",
        description="Triggered when a new user is created",
        schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"}
            },
            "required": ["user_id", "username", "email"]
        },
        example={
            "user_id": "user-123",
            "username": "johndoe",
            "email": "john@example.com",
            "created_at": "2023-01-01T00:00:00Z"
        },
        domain="users"
    ))
    
    await repository.register_event_type(EventTypeInfo(
        name="OrderCreated",
        description="Triggered when a new order is created",
        schema={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "user_id": {"type": "string"},
                "total_amount": {"type": "number"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number"}
                        }
                    }
                },
                "created_at": {"type": "string", "format": "date-time"}
            },
            "required": ["order_id", "user_id", "total_amount", "items"]
        },
        example={
            "order_id": "order-123",
            "user_id": "user-123",
            "total_amount": 99.99,
            "items": [
                {"product_id": "product-123", "quantity": 1, "price": 49.99},
                {"product_id": "product-456", "quantity": 2, "price": 24.99}
            ],
            "created_at": "2023-01-01T00:00:00Z"
        },
        domain="orders"
    ))
    
    # Create default subscriptions
    # 1. Welcome email handler
    await subscription_manager.create_subscription(SubscriptionConfig(
        event_type="UserCreated",
        handler_name="send_welcome_email",
        handler_module="uno.core.examples.subscription_management_example",
        description="Sends a welcome email to newly registered users",
        is_active=True
    ))
    
    # 2. User profile handler
    await subscription_manager.create_subscription(SubscriptionConfig(
        event_type="UserCreated",
        handler_name="create_user_profile",
        handler_module="uno.core.examples.subscription_management_example",
        description="Creates a default profile for new users",
        is_active=True
    ))
    
    # 3. Inventory notification handler
    await subscription_manager.create_subscription(SubscriptionConfig(
        event_type="OrderCreated",
        handler_name="notify_inventory",
        handler_module="uno.core.examples.subscription_management_example",
        description="Notifies inventory system about a new order",
        is_active=True
    ))


@app.on_event("startup")
async def startup():
    """Initialize the application on startup."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Set up the event system
    await setup_event_system()
    
    # Register the API router
    subscription_router = create_subscription_router(subscription_manager)
    app.include_router(subscription_router, prefix="/api")


@app.get("/")
async def get_subscription_manager_ui(request: Request):
    """Render the subscription manager UI."""
    return templates.TemplateResponse(
        "subscription_manager.html",
        {"request": request}
    )


@app.post("/api/demo/user")
async def create_user(publisher: EventPublisher = Depends(get_event_bus)):
    """Create a demo user to generate events."""
    user_id = f"user-{uuid.uuid4()}"
    username = f"user_{user_id[-6:]}"
    email = f"{username}@example.com"
    
    # Create and publish the event
    event = UserCreated(
        user_id=user_id,
        username=username,
        email=email
    )
    
    await event_publisher.publish(event)
    
    return {
        "message": "User created successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email
        }
    }


@app.post("/api/demo/order")
async def create_order(publisher: EventPublisher = Depends(get_event_bus)):
    """Create a demo order to generate events."""
    order_id = f"order-{uuid.uuid4()}"
    user_id = f"user-{uuid.uuid4()}"
    
    # Generate random items (occasionally with high quantities to trigger errors)
    items = []
    total_amount = 0
    
    for i in range(1, 4):
        product_id = f"product-{uuid.uuid4()}"
        quantity = 1 if i < 3 else (12 if uuid.uuid4().int % 5 == 0 else 2)  # Occasionally high quantity
        price = round(float(uuid.uuid4().int % 10000) / 100, 2)
        
        items.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price
        })
        
        total_amount += quantity * price
    
    # Create and publish the event
    event = OrderCreated(
        order_id=order_id,
        user_id=user_id,
        total_amount=round(total_amount, 2),
        items=items
    )
    
    await event_publisher.publish(event)
    
    return {
        "message": "Order created successfully",
        "order": {
            "id": order_id,
            "user_id": user_id,
            "total_amount": round(total_amount, 2),
            "items": items
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)