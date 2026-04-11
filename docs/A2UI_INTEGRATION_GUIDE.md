# RICCO AI - A2UI Integration & Context Engineering Guide

## Overview

This document describes the complete integration with Google A2UI (Agent-to-User Interface) and the Context Engineering system for the RICCO ecosystem.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RICCO AI Service                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Context        │  │  A2UI Service   │  │  GenUI SDK      │ │
│  │  Engineering    │──▶│  (UI Gen)       │──▶│  (Flutter)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│          │                    │                                 │
│          ▼                    ▼                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │  Agent Seeds    │  │  React Renderer │                      │
│  │  (All Solutions)│  │  (Web Apps)     │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    MCP Servers Arsenal (50+)                ││
│  │  Filesystem | Database | Web | AI | Finance | RICCO        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 1. Context Engineering

Context Engineering is the core system that enables truly personalized AI agents by fusing multiple context sources.

### Context Types

#### Personal Context
User-specific information including:
- Profile data (name, email, timezone, language)
- Preferences and interests
- Calendar events and appointments
- Communication patterns
- Trust score and verification status

```python
from app.context import PersonalContext, get_context_service

# Build personal context
personal = PersonalContext(
    user_id="user123",
    name="Juan García",
    email="juan@example.com",
    language="es",
    timezone="America/Havana",
    trust_score=85.5,
    kyc_verified=True,
    roles=["seller", "premium"],
    interests=["technology", "sports", "travel"],
)
```

#### Spatial Context
Location-based information:
- GPS coordinates and address
- Location type (home, office, transit)
- Nearby points of interest
- Weather conditions
- Geofence events

```python
from app.context import SpatialContext

spatial = SpatialContext(
    latitude=23.1136,
    longitude=-82.3666,
    city="La Habana",
    country="Cuba",
    location_type="home",
    weather={"temp": 28, "condition": "sunny"},
)
```

#### Temporal Context
Time-based information:
- Current time and timezone
- Time of day category
- Business hours status
- Season and quarter
- Active events and deadlines

```python
from app.context import TemporalContext

# Automatically determined from current time
temporal = TemporalContext()
# time_of_day: "morning" | "afternoon" | "evening" | "night"
# is_business_hours: True/False
# is_weekend: True/False
# season: "spring" | "summer" | "autumn" | "winter"
```

#### Device Context
Device-specific information:
- Device type and platform
- Screen dimensions and orientation
- Battery level and charging status
- Network type and speed
- Available input methods
- Permissions

```python
from app.context import DeviceContext

device = DeviceContext(
    device_type="mobile",
    platform="ios",
    screen_width=390,
    screen_height=844,
    battery_level=75.0,
    battery_charging=True,
    network_type="wifi",
    color_scheme="dark",
)
```

#### Solution Context
RICCO solution-specific data:
- Active solution and user role
- Cart items and orders (Commerce)
- Appointments and records (Health)
- Shipments and addresses (Logistics)

```python
from app.context import SolutionContext

solution = SolutionContext(
    solution_id="ricco-commerce",
    solution_name="Commerce",
    user_role="seller",
    cart_items=[{"product_id": "123", "quantity": 2}],
    recent_searches=["laptop", "phone"],
)
```

#### Horizontal Context
Cross-solution shared data:
- Energy Points balance
- Trust Score and level
- Subscription plan
- Accessible solutions
- Global preferences

```python
from app.context import HorizontalContext

horizontal = HorizontalContext(
    energy_points_balance=1500.0,
    trust_score=85.5,
    subscription_plan="premium",
    accessible_solutions=["commerce", "health", "logistics"],
    language="es",
    currency="USD",
)
```

#### Vertical Context
Deep vertical-specific context:
- Commerce: purchase history, spending patterns
- Health: medical profile, conditions, medications
- Logistics: shipping preferences, frequent routes
- Finance: accounts, investments, budgets

```python
from app.context import VerticalContext

vertical = VerticalContext(
    commerce={
        "purchase_history": [...],
        "preferred_categories": ["electronics", "books"],
        "total_spent": 2500.00,
    }
)
```

### Building Complete Context

```python
from app.context import get_context_service

async def build_agent_context(user_id: str, solution: str):
    service = get_context_service()
    
    # Build complete context bundle
    bundle = await service.build_context(
        session_id="session-123",
        user_id=user_id,
        solution=solution,
        request_context={
            "device": {"type": "mobile", "platform": "ios"},
            "location": {"city": "La Habana", "country": "Cuba"},
            "language": "es",
        }
    )
    
    # Generate prompt for AI
    prompt = await service.generate_context_prompt(bundle)
    
    return bundle, prompt
```

## 2. A2UI Service

A2UI generates dynamic UI components based on context and user intent.

### Component Types

```python
from app.services.a2ui_service import (
    A2UIService,
    ComponentType,
    A2UIComponent,
    A2UIResponse,
)

service = A2UIService()

# Create components
text_component = A2UIComponent(
    type=ComponentType.TEXT,
    properties={"content": "Hello, world!"},
)

button_component = A2UIComponent(
    type=ComponentType.BUTTON,
    properties={"label": "Click me", "variant": "primary"},
    actions={
        "click": ComponentAction(
            type="navigate",
            navigation={"route": "/products"},
        )
    },
)

card_component = A2UIComponent(
    type=ComponentType.CARD,
    children=[text_component, button_component],
    style=ComponentStyle(padding="16px", borderRadius="8px"),
)
```

### Generating UI Responses

```python
# Create session
session = await service.create_session(
    user_id="user123",
    solution="ricco-commerce",
    device_context=device_context,
)

# Build context
context = await service.build_context_bundle(
    user_id="user123",
    session_id=session.session_id,
    solution="ricco-commerce",
)

# Generate UI response
response = await service.generate_response(
    session_id=session.session_id,
    agent_response="Here are your search results",
    intent="product_search",
    entities={"products": products_list},
    context_bundle=context,
)
```

### Exporting for Different Platforms

```python
# For React
react_json = await service.export_for_react(response)

# For Lit (Web Components)
lit_json = await service.export_for_lit(response)

# For Flutter/GenUI
flutter_json = await service.export_for_flutter(response)
```

## 3. Flutter GenUI SDK

For we.ricco.com and mobile apps using Flutter.

### Widget Types

```dart
// Flutter widget types supported
enum FlutterWidgetType {
  // Basic
  text, image, icon, container, card,
  
  // Layout
  row, column, stack, gridView, listView,
  
  // Input
  textField, dropdownButton, checkbox, switch,
  
  // Action
  elevatedButton, filledButton, outlinedButton,
  
  // RICCO Custom
  productCard, orderCard, trackingCard, appointmentCard,
  energyPointsDisplay, trustScoreBadge,
}
```

### Backend Integration

```python
from app.integrations import get_genui_service, create_flutter_response

service = get_genui_service()

# Generate UI for specific intent
ui = await service.generate_ui_response(
    intent="product",
    data={
        "id": "prod-123",
        "name": "iPhone 15",
        "price": 999.99,
        "image_url": "https://...",
        "rating": 4.8,
    },
)

# Generate solution home screens
commerce_home = await service.generate_commerce_home({
    "categories": [...],
    "featured_products": [...],
})

health_dashboard = await service.generate_health_dashboard({
    "user_name": "Juan",
    "next_appointment": {...},
})
```

### Flutter Client Example

```dart
// lib/services/genui_client.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class GenUIClient {
  final String baseUrl;
  
  GenUIClient({required this.baseUrl});
  
  Future<Map<String, dynamic>> getUI(String endpoint) async {
    final response = await http.get(Uri.parse('$baseUrl$endpoint'));
    return json.decode(response.body);
  }
  
  Widget buildWidget(Map<String, dynamic> widgetData) {
    final type = widgetData['type'];
    final props = widgetData['properties'] ?? {};
    final children = widgetData['children'] ?? [];
    
    switch (type) {
      case 'Text':
        return Text(
          props['data'] ?? '',
          style: _parseTextStyle(props['style']),
        );
      case 'ElevatedButton':
        return ElevatedButton(
          onPressed: () => _handleAction(widgetData['onTap']),
          child: Text(props['label'] ?? ''),
        );
      case 'ProductCard':
        return ProductCard(
          productId: props['productId'],
          name: props['name'],
          price: props['price'],
          imageUrl: props['imageUrl'],
          onTap: () => _handleAction(widgetData['onTap']),
        );
      // ... more widget types
      default:
        return Container(child: Text('Unknown widget: $type'));
    }
  }
}
```

## 4. React Renderer

For RICCO web frontend solutions.

### Component Generation

```python
from app.integrations import get_react_renderer, create_react_response

renderer = get_react_renderer()

# Build components
button = renderer.build_button(
    label="Add to Cart",
    variant="primary",
    onClick=ReactAction(
        type="api_call",
        endpoint="/api/cart/add",
        method="POST",
        payload={"product_id": "123"},
    ),
)

product_card = renderer.build_product_card({
    "id": "prod-123",
    "name": "iPhone 15",
    "price": 999.99,
    "image_url": "https://...",
    "rating": 4.8,
})

form = renderer.build_form(
    fields=[
        {"name": "email", "type": "email", "label": "Email", "required": True},
        {"name": "password", "type": "password", "label": "Password", "required": True},
    ],
    submit_label="Login",
    submit_endpoint="/api/auth/login",
)
```

### Page Generation

```python
# Generate complete pages
commerce_page = await generate_commerce_homepage({
    "categories": [...],
    "featured_products": [...],
    "user_name": "Juan",
})

health_page = await generate_health_dashboard({
    "user_name": "Juan",
    "next_appointment": {...},
})
```

### React Client Example

```tsx
// components/DynamicUI.tsx
import React from 'react';
import { Button, Card, Input, Text } from '@ricco/ui';

interface Widget {
  type: string;
  props: Record<string, any>;
  children?: Widget[];
  events?: Record<string, Action>;
}

export const DynamicUI: React.FC<{ widget: Widget }> = ({ widget }) => {
  const renderWidget = (w: Widget): React.ReactNode => {
    const { type, props, children = [], events = {} } = w;
    
    switch (type) {
      case 'Text':
        return <Text {...props} />;
        
      case 'Button':
        return (
          <Button 
            {...props} 
            onClick={() => handleAction(events.onClick)}
          />
        );
        
      case 'Input':
        return <Input {...props} />;
        
      case 'Card':
        return (
          <Card {...props}>
            {children.map((child, i) => (
              <DynamicUI key={i} widget={child} />
            ))}
          </Card>
        );
        
      case 'ProductCard':
        return <ProductCard {...props} onClick={() => handleAction(events.onClick)} />;
        
      default:
        return <div>Unknown widget: {type}</div>;
    }
  };
  
  return <>{renderWidget(widget)}</>;
};
```

## 5. Integration Flow

### Complete Request Flow

```
1. User sends message
        │
        ▼
2. Build Context Bundle
   ├── Personal Context (from RICCO ID)
   ├── Spatial Context (from device GPS)
   ├── Temporal Context (auto-generated)
   ├── Device Context (from client)
   ├── Solution Context (active solution data)
   ├── Horizontal Context (Energy Points, Trust)
   └── Vertical Context (solution-specific)
        │
        ▼
3. Generate Context Prompt
        │
        ▼
4. Send to AI Agent with Context
        │
        ▼
5. AI Agent Returns Response
        │
        ▼
6. A2UI Generates UI Components
   ├── Analyze intent
   ├── Create appropriate components
   └── Apply context-aware styling
        │
        ▼
7. Export for Platform
   ├── Flutter JSON (mobile apps)
   ├── React JSON (web apps)
   └── Lit JSON (web components)
        │
        ▼
8. Client Renders UI
```

### Example: Product Search Flow

```python
async def handle_product_search(
    user_id: str,
    query: str,
    device_context: DeviceContext,
):
    # 1. Build context
    context_service = get_context_service()
    context = await context_service.build_context(
        session_id="search-session",
        user_id=user_id,
        solution="ricco-commerce",
        request_context={"device": device_context.model_dump()},
    )
    
    # 2. Generate AI prompt
    prompt = await context_service.generate_context_prompt(
        context,
        intent="product_search",
    )
    
    # 3. Get AI response (via OpenRouter)
    ai_response = await openrouter.chat(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
    )
    
    # 4. Search products
    products = await search_products(query)
    
    # 5. Generate UI
    a2ui = get_a2ui_service()
    ui_response = await a2ui.generate_response(
        session_id="search-session",
        agent_response=ai_response,
        intent="product_search",
        entities={"products": products},
        context_bundle=context,
    )
    
    # 6. Export for platform
    if device_context.platform == "ios" or device_context.platform == "android":
        return await a2ui.export_for_flutter(ui_response)
    else:
        return await a2ui.export_for_react(ui_response)
```

## 6. MCP Servers Arsenal

The MCP (Model Context Protocol) arsenal provides tools for agents:

### Categories (50+ servers)

1. **Filesystem & Storage**: filesystem, S3, Google Drive
2. **Database**: PostgreSQL, MongoDB, Redis, NebulaGraph
3. **Web & API**: Fetch, Brave Search, Puppeteer
4. **AI & LLM**: OpenAI, OpenRouter, Ollama, HuggingFace
5. **Productivity**: Google Maps, Calendar, Email, Slack
6. **Finance**: Stripe, QvaPay, Crypto, Binance
7. **RICCO**: ID, Energy Points, Commerce, Logistics, Health
8. **DevOps**: GitHub, GitLab, Docker, Kubernetes
9. **Monitoring**: Prometheus, Grafana, Langfuse
10. **Documents**: PDF, DOCX, XLSX

### Usage with Agents

```python
from app.seeds.mcp_servers import get_mcp_servers_for_solution

# Get recommended MCPs for a solution
commerce_mcps = get_mcp_servers_for_solution("ricco-commerce")
# Returns: postgres, redis, commerce, stripe, qvapay, + AI MCPs

# Configure agent with MCPs
agent = AgentConfig(
    name="Commerce Assistant",
    mcp_servers=[mcp.id for mcp in commerce_mcps],
)
```

## 7. Agent Seeds

Pre-configured agent templates for each RICCO solution:

### Available Agents

| Solution | Agents |
|----------|--------|
| Commerce | Assistant, Recommender |
| Health | Assistant |
| Logistics | Assistant |
| Funding | Assistant, Analyst |
| Legal | Assistant |
| Social | Assistant, Moderator |
| Connect | Assistant |
| ID | Assistant, KYC Processor |
| Assets | Assistant |
| Booking | Assistant, Pricing Agent |
| Gym | Assistant, Virtual Trainer |
| POS | Assistant, Analytics Agent |
| Cargo | Assistant, Customs Agent |
| Travel | Assistant, Trip Planner |

### Using Agent Seeds

```python
from app.seeds.agent_seeds import get_agent_seeds_by_solution, get_agent_seed_by_id

# Get all agents for a solution
commerce_agents = get_agent_seeds_by_solution("ricco-commerce")

# Get specific agent
assistant = get_agent_seed_by_id("commerce-assistant")

# Agent properties
print(assistant.system_prompt)
print(assistant.capabilities)
print(assistant.tools)
print(assistant.mcp_servers)
```

## Summary

The RICCO AI integration provides:

1. **Context Engineering**: 9 context types for personalized AI
2. **A2UI**: Dynamic UI generation from AI responses
3. **Flutter GenUI SDK**: Mobile app integration for we.ricco.com
4. **React Renderer**: Web frontend integration
5. **MCP Arsenal**: 50+ tool servers for agent capabilities
6. **Agent Seeds**: Pre-configured templates for all solutions

This enables building AI agents that truly understand user context and generate appropriate, personalized UI responses across all platforms.
