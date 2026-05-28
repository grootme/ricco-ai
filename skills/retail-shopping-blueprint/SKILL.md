# Retail Shopping Assistant Blueprint Skill

AI-powered retail shopping assistant with multi-agent architecture, visual search, and intelligent cart management.

## Description

This skill provides an intelligent shopping assistant that can search products using natural language or images, manage shopping carts, and provide personalized recommendations. Built with LangGraph for agent orchestration and NVIDIA NIMs for LLM capabilities.

## When to Use

- Natural language product search
- Visual/image-based product search
- Shopping cart management
- Product recommendations
- Conversational shopping assistance
- Price comparisons and deals

## Blueprint Source

Based on: [NVIDIA retail-shopping-assistant](https://github.com/NVIDIA-AI-Blueprints/retail-shopping-assistant)

## Tools

### Product Search Tools

| Tool | Description |
|------|-------------|
| `search_products_text` | Search products using natural language |
| `search_products_image` | Search products using image (visual search) |
| `get_product_details` | Get detailed product information |
| `get_product_reviews` | Get product reviews and ratings |
| `compare_products` | Compare multiple products |
| `get_similar_products` | Find similar products |

### Cart Management Tools

| Tool | Description |
|------|-------------|
| `add_to_cart` | Add product to shopping cart |
| `remove_from_cart` | Remove product from cart |
| `update_cart_quantity` | Update product quantity in cart |
| `get_cart` | Get current cart contents |
| `clear_cart` | Clear all items from cart |
| `get_cart_total` | Get cart total with discounts |

### Recommendation Tools

| Tool | Description |
|------|-------------|
| `get_personalized_recommendations` | Get personalized product recommendations |
| `get_trending_products` | Get trending products |
| `get_deals` | Get current deals and promotions |
| `get_category_recommendations` | Get category-specific recommendations |

### Conversation Tools

| Tool | Description |
|------|-------------|
| `chat` | Natural language shopping conversation |
| `get_shopping_context` | Get current shopping context |
| `set_preferences` | Set user shopping preferences |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Port 3000)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Chat UI      │ │ Visual Search│ │ Cart Management      │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────┐
│                    Chain Server (FastAPI)                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              LangGraph Orchestration                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │  │
│  │  │ Search   │ │ Cart     │ │ Recommend│ │ Guardrails│   │  │
│  │  │ Agent    │ │ Agent    │ │ Agent    │ │ Service   │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────┐
│                    NVIDIA NIM Services                        │
│  ┌───────────────────┐  ┌───────────────────────────────┐     │
│  │ Nemotron 3 Super  │  │ NV-EmbedQA-E5-v5             │     │
│  │ 120B LLM          │  │ Vector Embeddings             │     │
│  └───────────────────┘  └───────────────────────────────┘     │
│  ┌───────────────────┐  ┌───────────────────────────────┐     │
│  │ NV-CLIP           │  │ NeMoGuard Content Safety      │     │
│  │ Visual Embedding  │  │                               │     │
│  └───────────────────┘  └───────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────┐
│                    Data Layer                                  │
│  ┌───────────────────┐  ┌───────────────────────────────┐     │
│  │ Milvus            │  │ PostgreSQL                    │     │
│  │ Vector DB         │  │ Product Catalog               │     │
│  └───────────────────┘  └───────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API Keys
NGC_API_KEY=nvapi-xxx
LLM_API_KEY=$NGC_API_KEY
EMBED_API_KEY=$NGC_API_KEY
RAIL_API_KEY=$NGC_API_KEY

# Model Configuration
LLM_MODEL=nvidia/nemotron-3-super-120b-a12b
EMBED_MODEL=nvidia/nv-embedqa-e5-v5
VISION_MODEL=nvidia/nvclip

# Services
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### Integration with DeerFlow

```python
from deerflow.blueprints import RetailShoppingBlueprint

shopping = RetailShoppingBlueprint()

# Text search
results = await shopping.search_products_text(
    query="comfortable running shoes under $100",
    limit=10
)

# Visual search
results = await shopping.search_products_image(
    image_url="https://example.com/shoe.jpg"
)

# Add to cart
await shopping.add_to_cart(
    product_id="PROD-001",
    quantity=2
)

# Get recommendations
recs = await shopping.get_personalized_recommendations(
    user_id="user-123"
)
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| Nemotron 3 Super 120B | 4x A100 80GB | 4x H100 80GB |
| NV-EmbedQA | 1x A100 | 1x H100 |
| NV-CLIP | 1x A100 | 1x L40S |

## Content Safety

Built-in moderation using NeMo Guardrails:
- Content safety checks on queries
- Topic control for appropriate content
- Input/output validation

## Example Usage

```python
from deerflow.tools.shopping import ShoppingAssistant

assistant = ShoppingAssistant()

# Natural language search
products = await assistant.search("I need a laptop for gaming under $1500")

# Visual search - upload image to find similar products
similar = await assistant.search_by_image("./product_image.jpg")

# Manage cart
await assistant.add_to_cart("LAPTOP-001", quantity=1)
cart = await assistant.get_cart()
print(f"Cart total: ${cart.total}")

# Chat interaction
response = await assistant.chat(
    "What's the best gaming laptop in my cart?"
)
```

## References

- [NVIDIA NIM Catalog](https://catalog.ngc.nvidia.com/orgs/nim)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Milvus Vector DB](https://milvus.io/)
- [NV-CLIP Model](https://build.nvidia.com/nvidia/nvclip)
