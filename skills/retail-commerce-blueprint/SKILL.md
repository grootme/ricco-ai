# Retail Agentic Commerce Blueprint Skill

NVIDIA AI Blueprint for Agentic Commerce Protocol (ACP) and Universal Commerce Protocol (UCP) implementation.

## Description

This skill provides tools for merchant-controlled checkout, payments, and agent orchestration in retail commerce. Implements ACP for checkout sessions and UCP for agent-to-agent communication.

## When to Use

- E-commerce checkout automation
- Payment processing delegation
- Product recommendations and promotions
- Post-purchase messaging
- Shopping cart management
- Agent-to-agent commerce protocols

## Blueprint Source

Based on: [NVIDIA Retail-Agentic-Commerce](https://github.com/NVIDIA-AI-Blueprints/Retail-Agentic-Commerce)

## Tools

### ACP (Agentic Commerce Protocol) Tools

| Tool | Description |
|------|-------------|
| `create_checkout_session` | Create new checkout session |
| `get_checkout_session` | Get checkout session details |
| `update_checkout_session` | Update checkout session |
| `complete_checkout` | Complete checkout process |
| `cancel_checkout` | Cancel checkout session |
| `apply_promotion` | Apply promotion code |
| `get_payment_methods` | Get available payment methods |

### UCP (Universal Commerce Protocol) Tools

| Tool | Description |
|------|-------------|
| `discover_agent` | Discover merchant agent capabilities |
| `send_a2a_message` | Send agent-to-agent message |
| `get_agent_card` | Get agent card metadata |
| `query_product_catalog` | Query product catalog |

### NAT Agent Tools

| Tool | Description |
|------|-------------|
| `get_promotions` | Get available promotions |
| `get_recommendations` | Get personalized recommendations |
| `search_products` | Search product catalog |
| `send_post_purchase_message` | Send post-purchase communication |

### Payment Service Provider (PSP) Tools

| Tool | Description |
|------|-------------|
| `create_payment_intent` | Create payment intent |
| `confirm_payment` | Confirm payment |
| `get_vault_tokens` | Get saved payment tokens |
| `process_refund` | Process refund |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Agent Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │ MCP SDK  │  │ ACP REST │  │ UCP A2A JSON-RPC        │   │
│  └────┬─────┘  └────┬─────┘  └────────────┬─────────────┘   │
└───────┼─────────────┼─────────────────────┼─────────────────┘
        ↓             ↓                     ↓
┌───────────────────────────────────────────────────────────────┐
│                    Merchant API (Port 8000)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │ Products    │ │ Checkout    │ │ Orders                  │  │
│  │ Sessions    │ │ Promotions  │ │ Recommendations         │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────┐
│                    NAT Agents                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────┐   │
│  │ Promotion   │ │ Post-       │ │ Recs     │ │ Search    │   │
│  │ (8002)      │ │ Purchase    │ │ (8004)   │ │ (8005)    │   │
│  └─────────────┘ │ (8003)      │ └──────────┘ └───────────┘   │
└───────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────┐
│                    NVIDIA NIMs                                 │
│  ┌─────────────────────┐  ┌─────────────────────────────┐     │
│  │ Nemotron Nano LLM   │  │ NV-EmbedQA-E5              │     │
│  │ (Port 8010)         │  │ (Port 8011)                │     │
│  └─────────────────────┘  └─────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API
NVIDIA_API_KEY=nvapi-xxx

# Services
MERCHANT_API_URL=http://localhost:8000
PSP_SERVICE_URL=http://localhost:8001
MCP_SERVER_PORT=2091

# Agent Ports
PROMOTION_AGENT_PORT=8002
POST_PURCHASE_AGENT_PORT=8003
RECOMMENDATION_AGENT_PORT=8004
SEARCH_AGENT_PORT=8005
```

### Integration with DeerFlow

```python
from deerflow.blueprints import RetailCommerceBlueprint

blueprint = RetailCommerceBlueprint(
    merchant_api="http://localhost:8000",
    enable_mcp=True
)

# Create checkout session
session = await blueprint.create_checkout_session(
    cart_items=[{"sku": "PROD-001", "qty": 2}]
)

# Get recommendations
recs = await blueprint.get_recommendations(user_id="user-123")
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| Nemotron Nano | 1x A100 | 1x H100 |
| NV-EmbedQA | 1x A100 | 1x H100 |

## Protocol Endpoints

### ACP Endpoints
- `POST /checkout_sessions` - Create checkout session
- `GET /checkout_sessions/{id}` - Get session
- `PUT /checkout_sessions/{id}` - Update session

### UCP Endpoints
- `GET /.well-known/ucp` - UCP discovery
- `GET /.well-known/agent-card.json` - Agent card
- `POST /a2a` - Agent-to-agent messaging

### MCP Server
- `Port 2091` - Apps SDK MCP Server

## Example Usage

```python
# Initialize commerce agent
from deerflow.tools.retail_commerce import CommerceAgent

agent = CommerceAgent()

# Search products
products = await agent.search_products("wireless headphones")

# Create checkout
checkout = await agent.create_checkout_session(
    items=[{"sku": "WH-001", "quantity": 1}],
    user_id="user-123"
)

# Apply promotion
await agent.apply_promotion(
    session_id=checkout.id,
    code="SAVE20"
)

# Get recommendations
recs = await agent.get_recommendations(
    user_id="user-123",
    context={"category": "electronics"}
)
```

## References

- [Agentic Commerce Protocol Spec](https://build.nvidia.com/)
- [Universal Commerce Protocol](https://build.nvidia.com/)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)
- [Milvus Vector Search](https://milvus.io/)
