# AI Virtual Assistant Blueprint Skill

## Overview
NVIDIA AI Virtual Assistant Blueprint integration for creating intelligent customer service bots that can greet customers, respond to inquiries, and guide them through common issues.

## Description
This skill provides tools for building AI-powered virtual assistants for customer service across every industry. It supports:

- **Multi-channel Support**: Web, mobile, voice, messaging platforms
- **Intent Recognition**: Understand customer intents
- **Context Management**: Maintain conversation context
- **Knowledge Integration**: Connect to knowledge bases
- **Handoff to Humans**: Seamless escalation to human agents

## Tools (15)

### va_init
Initialize virtual assistant system.

**Parameters:**
- `assistant_name` (required): Name for the assistant
- `industry` (optional): Industry vertical (retail, healthcare, finance, etc.)
- `channels` (optional): Supported channels ('web', 'mobile', 'voice', 'messaging')
- `languages` (optional): Supported languages

### va_create_persona
Create assistant persona.

**Parameters:**
- `persona_name` (required): Name for the persona
- `personality` (optional): Personality traits
- `greeting_message` (optional): Default greeting
- `tone` (optional): 'professional', 'friendly', 'casual'

### va_define_intents
Define conversation intents.

**Parameters:**
- `intents` (required): List of intent definitions
- `training_phrases` (optional): Example phrases per intent
- `entities` (optional): Entities to extract

### va_create_flow
Create conversation flow.

**Parameters:**
- `flow_name` (required): Name for the flow
- `trigger_intent` (required): Intent that triggers the flow
- `steps` (required): Conversation steps
- `fallback` (optional): Fallback behavior

### va_add_knowledge
Add knowledge to assistant.

**Parameters:**
- `knowledge_type` (required): 'faq', 'document', 'api', 'database'
- `source` (required): Knowledge source
- `auto_update` (optional): Enable auto-updates

### va_create_faq
Create FAQ knowledge base.

**Parameters:**
- `faqs` (required): List of Q&A pairs
- `category` (optional): FAQ category
- `synonyms` (optional): Synonym mappings

### va_set_context
Set conversation context.

**Parameters:**
- `session_id` (required): Session identifier
- `context_data` (required): Context information
- `ttl` (optional): Context time-to-live

### va_process_message
Process user message.

**Parameters:**
- `session_id` (required): Session identifier
- `message` (required): User message
- `channel` (optional): Message channel
- `user_info` (optional): User information

### va_generate_response
Generate assistant response.

**Parameters:**
- `session_id` (required): Session identifier
- `intent` (required): Recognized intent
- `entities` (optional): Extracted entities
- `context` (optional): Current context

### va_detect_sentiment
Detect user sentiment.

**Parameters:**
- `message` (required): User message
- `include_emotions` (optional): Include emotion detection
- `track_history` (optional): Track sentiment over time

### va_handoff
Hand off to human agent.

**Parameters:**
- `session_id` (required): Session to handoff
- `reason` (required): Handoff reason
- `priority` (optional): Priority level
- `summary` (optional): Conversation summary

### va_analyze_conversation
Analyze conversation metrics.

**Parameters:**
- `session_id` (required): Session to analyze
- `analysis_type` (optional): 'satisfaction', 'intent', 'performance'
- `time_range` (optional): Time range for analysis

### va_get_analytics
Get assistant analytics.

**Parameters:**
- `metrics` (required): Metrics to retrieve
- `time_range` (optional): Time range
- `group_by` (optional): Grouping dimension

### va_train_intent
Train intent recognition model.

**Parameters:**
- `intents` (required): Intents to train
- `training_data` (optional): Additional training data
- `model_type` (optional): Model architecture

### va_deploy
Deploy assistant to channels.

**Parameters:**
- `assistant_name` (required): Assistant to deploy
- `channels` (required): Target channels
- `environment` (optional): 'development', 'staging', 'production'

## Conversation Flows

### Simple FAQ Flow
```
User: "What are your hours?"
→ Intent: get_hours
→ Response: "We're open Monday-Friday, 9am-5pm."
```

### Multi-step Flow
```
User: "I want to return an item"
→ Intent: return_item
→ Step 1: Ask for order number
→ Step 2: Verify order
→ Step 3: Ask for reason
→ Step 4: Process return
```

### Escalation Flow
```
User: "I need to speak to someone"
→ Intent: request_human
→ Action: va_handoff()
→ Human agent receives context
```

## Channel Integration

### Web Chat
```javascript
// Embed widget
<script src="https://assistant.nvidia.com/widget.js"
        data-assistant="my-assistant"
        data-channel="web">
</script>
```

### Voice (Phone)
```python
va_deploy(
    assistant_name="phone-bot",
    channels=["voice"],
    environment="production"
)
```

### Messaging Platforms
- WhatsApp Business
- Facebook Messenger
- Telegram
- SMS

## Industry Templates

### Retail
```python
va_init(
    assistant_name="retail-bot",
    industry="retail",
    channels=["web", "messaging"]
)
va_create_faq([
    ("What's your return policy?", "Returns accepted within 30 days..."),
    ("Do you offer free shipping?", "Free shipping on orders over $50..."),
])
```

### Healthcare
```python
va_init(
    assistant_name="health-bot",
    industry="healthcare",
    channels=["web", "voice"]
)
va_define_intents([
    {"name": "schedule_appointment", "phrases": ["book appointment", "see a doctor"]},
    {"name": "check_symptoms", "phrases": ["I have a headache", "feeling sick"]},
])
```

### Financial Services
```python
va_init(
    assistant_name="finance-bot",
    industry="finance",
    channels=["web", "mobile", "messaging"]
)
va_add_knowledge(
    knowledge_type="api",
    source={"url": "/api/account-balance", "auth": "oauth2"}
)
```

## Sentiment Analysis

### Real-time Sentiment
```
Message: "This is taking forever and I'm very frustrated!"
→ Sentiment: NEGATIVE (score: -0.8)
→ Emotion: frustration
→ Action: Offer escalation or priority support
```

### Sentiment Tracking
```
Session timeline:
- Message 1: Neutral (0.1)
- Message 3: Positive (0.4)
- Message 5: Negative (-0.6)
→ Trend: Declining
→ Action: Proactive intervention
```

## Integration with NVIDIA

- **NVIDIA Riva**: Speech AI for voice channels
- **NVIDIA NIM**: LLM inference for response generation
- **NVIDIA NeMo**: Conversational AI training
- **NVIDIA ACE**: Digital human integration

## References

- [AI Virtual Assistant Blueprint](https://github.com/NVIDIA-AI-Blueprints/ai-virtual-assistant)
- [Conversation Design](./references/conversation_design.md)
- [Channel Integration](./references/channels.md)
