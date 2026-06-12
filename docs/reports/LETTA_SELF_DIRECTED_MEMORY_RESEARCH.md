# Letta (MemGPT) Self-Directed Memory Management Research

## Executive Summary

Letta (formerly MemGPT) is a revolutionary platform for building stateful AI agents with self-directed memory management. It implements an OS-inspired hierarchical memory architecture that enables agents to overcome LLM context window limitations through autonomous memory decisions.

**Key Innovation**: Agents can self-edit their own memory using function tools, deciding what to remember, forget, and consolidate without human intervention.

---

## 1. Letta Architecture: Self-Directed Memory Implementation

### 1.1 Core Concept: LLM as Operating System

Letta implements the "LLM as Operating System" paradigm from the MemGPT paper (arXiv:2310.08560):

```
┌─────────────────────────────────────────────────────────────┐
│                    LETTA AGENT ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              MAIN CONTEXT (Limited)                  │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │    │
│  │  │   SYSTEM    │ │   CORE      │ │  WORKING    │    │    │
│  │  │   PROMPT    │ │   MEMORY    │ │  MEMORY     │    │    │
│  │  │  (Persona)  │ │  (Blocks)   │ │ (Messages)  │    │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘    │    │
│  │         ↑ Always in context (like RAM)              │    │
│  └─────────────────────────────────────────────────────┘    │
│                         ↕                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           EXTERNAL MEMORY (Unlimited)                │    │
│  │  ┌─────────────────┐ ┌─────────────────────────┐    │    │
│  │  │     RECALL      │ │      ARCHIVAL           │    │    │
│  │  │     MEMORY      │ │      MEMORY             │    │    │
│  │  │ (Message DB)    │ │ (Vector Database)       │    │    │
│  │  └─────────────────┘ └─────────────────────────┘    │    │
│  │         ↑ Requires retrieval (like Disk)            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Memory Hierarchy (OS-Inspired)

| Memory Tier | Analogy | Characteristics | Capacity |
|-------------|---------|-----------------|----------|
| **Main Context** | CPU Registers | Always visible to LLM | Fixed (context window) |
| **Core Memory** | RAM | In-context, self-editable | Limited (~2000-8000 tokens) |
| **Recall Memory** | Page Cache | Conversation history | Semi-limited |
| **Archival Memory** | Disk/SSD | Vector DB, searchable | Unlimited |

### 1.3 Key Architecture Components

```python
# Letta Agent Structure (Conceptual)
class LettaAgent:
    """Simplified Letta agent structure showing memory components"""
    
    def __init__(self):
        # System Prompt - Defines agent persona and behavior
        self.system_prompt = """
        You are a helpful AI assistant with memory capabilities.
        You have access to memory tools to store and retrieve information.
        Manage your memory wisely to provide personalized responses.
        """
        
        # Core Memory Blocks - Always in context
        self.core_memory = {
            "persona": "Information about the AI's identity",
            "human": "Information about the user",
            "tasks": "Current tasks and goals"
        }
        
        # Working Memory - Recent messages
        self.working_memory = []  # Recent conversation
        
        # Recall Memory - Full message history
        self.recall_memory = MessageDatabase()  # All messages
        
        # Archival Memory - Long-term semantic storage
        self.archival_memory = VectorDatabase()  # Unlimited storage
        
        # Memory Tools - Self-modification capabilities
        self.memory_tools = [
            "core_memory_append",
            "core_memory_replace", 
            "archival_memory_insert",
            "archival_memory_search",
            "conversation_search",
            # ... more tools
        ]
```

---

## 2. Memory Tiers: Detailed Breakdown

### 2.1 Core Memory (Memory Blocks)

**Definition**: Structured sections of the agent's context window that persist across all interactions. Always visible - no retrieval needed.

```python
# Core Memory Structure
class CoreMemoryBlock:
    """A structured memory block in core memory"""
    label: str           # e.g., "persona", "human", "tasks"
    content: str         # The actual content
    limit: int           # Character/token limit
    priority: int        # Importance for context management

# Default Core Memory Blocks
DEFAULT_BLOCKS = {
    "persona": {
        "description": "AI's identity and capabilities",
        "limit": 2000,
        "content": "I am a helpful AI assistant..."
    },
    "human": {
        "description": "User information and preferences",
        "limit": 2000,
        "content": "User prefers Python..."
    }
}
```

**Key Characteristics**:
- **Always in context**: No retrieval overhead
- **Self-editable**: Agent can modify using tools
- **Structured**: Organized by topic/purpose
- **Limited**: Must be carefully managed

### 2.2 Working Memory (Message Queue)

**Definition**: Recent conversation messages in the main context. Analogous to CPU cache.

```python
# Working Memory Management
class WorkingMemory:
    """Recent messages in main context"""
    
    def __init__(self, max_messages: int = 10):
        self.messages = []
        self.max_messages = max_messages
    
    def add_message(self, message: Message):
        """Add message, evict oldest if needed"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # Oldest messages moved to recall memory
            self._evict_oldest()
    
    def get_context(self) -> str:
        """Format for LLM context"""
        return "\n".join(m.content for m in self.messages)
```

### 2.3 Recall Memory (Conversation History)

**Definition**: Full conversation history stored in a database. Requires search/retrieval.

```python
# Recall Memory Operations
class RecallMemory:
    """Full message history with search capabilities"""
    
    async def search_conversations(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Message]:
        """Search through conversation history"""
        # Returns relevant past conversations
        pass
    
    async def get_recent(
        self,
        user_id: str,
        count: int = 5
    ) -> List[Message]:
        """Get most recent messages"""
        pass
```

### 2.4 Archival Memory (Vector Database)

**Definition**: Semantically searchable long-term storage for facts, knowledge, and information.

```python
# Archival Memory Operations
class ArchivalMemory:
    """Vector database for long-term semantic storage"""
    
    async def insert(
        self,
        content: str,
        metadata: Dict = None
    ) -> str:
        """Store new information with embeddings"""
        # Creates embedding, stores in vector DB
        pass
    
    async def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[ArchivalResult]:
        """Semantic search across all stored content"""
        # Returns most relevant stored information
        pass
    
    async def delete(self, memory_id: str):
        """Remove stored information"""
        pass
```

---

## 3. Memory Operations: Self-Directed Tools

### 3.1 Core Memory Tools

Letta agents use these tools to self-modify their core memory:

```python
# Core Memory Tools (Letta/MemGPT)

def core_memory_append(
    label: str,
    content: str
) -> str:
    """
    Append content to a core memory block.
    
    Args:
        label: Name of the memory block (e.g., "persona", "human")
        content: Content to append
    
    Returns:
        Status message with updated block size
    """
    # Agent decides what's important to remember
    pass

def core_memory_replace(
    label: str,
    old_content: str,
    new_content: str
) -> str:
    """
    Replace specific content in a core memory block.
    
    Args:
        label: Name of the memory block
        old_content: Text to find and replace
        new_content: New text to insert
    
    Returns:
        Status message
    """
    # Agent can update/correct memories
    pass
```

### 3.2 Archival Memory Tools

```python
# Archival Memory Tools (Letta/MemGPT)

def archival_memory_insert(
    content: str
) -> str:
    """
    Store information in archival memory (long-term storage).
    
    Args:
        content: Information to store permanently
    
    Returns:
        Memory ID for future reference
    """
    # Agent decides what's worth long-term storage
    pass

def archival_memory_search(
    query: str,
    page: int = 0
) -> List[ArchivalResult]:
    """
    Search archival memory semantically.
    
    Args:
        query: Search query
        page: Pagination (0 = first page)
    
    Returns:
        List of matching memories with relevance scores
    """
    # Agent retrieves relevant past knowledge
    pass

def archival_memory_delete(
    memory_id: str
) -> str:
    """
    Delete a memory from archival storage.
    
    Args:
        memory_id: ID of memory to delete
    
    Returns:
        Status message
    """
    # Agent can "forget" outdated information
    pass
```

### 3.3 Conversation Search Tools

```python
# Conversation/Recall Memory Tools

def conversation_search(
    query: str,
    page: int = 0
) -> List[ConversationResult]:
    """
    Search through past conversations.
    
    Args:
        query: Search query
        page: Pagination
    
    Returns:
        List of matching conversations
    """
    pass

def conversation_search_date(
    start_date: str,
    end_date: str
) -> List[ConversationResult]:
    """
    Search conversations by date range.
    
    Args:
        start_date: ISO format start date
        end_date: ISO format end date
    
    Returns:
        List of conversations in date range
    """
    pass
```

---

## 4. Self-Modification: How Agents Modify Their Own Memory

### 4.1 The Self-Editing Loop

```
┌─────────────────────────────────────────────────────────────┐
│              SELF-DIRECTED MEMORY MODIFICATION               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Message                                                │
│       ↓                                                      │
│  ┌─────────────┐                                            │
│  │  LLM sees   │  → Context = System + Core Memory +        │
│  │  context    │    Working Memory + Message                │
│  └─────────────┘                                            │
│       ↓                                                      │
│  ┌─────────────────────────────────────────────────┐        │
│  │  LLM decides:                                     │        │
│  │                                                   │        │
│  │  1. Do I need to REMEMBER this?                  │        │
│  │     → core_memory_append()                       │        │
│  │                                                   │        │
│  │  2. Is this important for long-term?             │        │
│  │     → archival_memory_insert()                   │        │
│  │                                                   │        │
│  │  3. Do I need to UPDATE existing memory?         │        │
│  │     → core_memory_replace()                      │        │
│  │                                                   │        │
│  │  4. Do I need to RECALL past info?               │        │
│  │     → archival_memory_search()                   │        │
│  │     → conversation_search()                      │        │
│  │                                                   │        │
│  │  5. Is this outdated/WRONG?                      │        │
│  │     → archival_memory_delete()                   │        │
│  │                                                   │        │
│  └─────────────────────────────────────────────────┘        │
│       ↓                                                      │
│  Tool Execution → Memory State Updated                       │
│       ↓                                                      │
│  Response Generation                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Example: Agent Self-Editing Memory

```python
# Example of self-directed memory modification

# User says: "My name is Alice and I love Python programming"

# Agent's internal process:
THINKING = """
The user is introducing themselves. I should:
1. Store their name in my 'human' core memory block
2. Store their programming preference for future reference
3. This seems important for long-term - add to archival
"""

# Agent executes these tools:
TOOL_CALLS = [
    {
        "name": "core_memory_append",
        "arguments": {
            "label": "human",
            "content": "\nName: Alice"
        }
    },
    {
        "name": "core_memory_append", 
        "arguments": {
            "label": "human",
            "content": "\nPreferred language: Python"
        }
    },
    {
        "name": "archival_memory_insert",
        "arguments": {
            "content": "User Alice prefers Python programming. Mentioned on first meeting."
        }
    }
]

# Later, user asks: "Can you help me with a coding problem?"
# Agent's context now includes: "User prefers Python"
# Agent can tailor response accordingly
```

### 4.3 Memory Importance Decisions

The agent autonomously decides importance based on:

```python
# Implicit decision factors for memory storage
class MemoryImportance:
    """Factors the LLM considers for memory importance"""
    
    FACTORS = {
        "user_preferences": {
            "weight": "high",
            "examples": ["likes Python", "prefers brief responses"]
        },
        "personal_info": {
            "weight": "high", 
            "examples": ["name is Alice", "works at Google"]
        },
        "task_context": {
            "weight": "medium",
            "examples": ["working on project X", "debugging issue Y"]
        },
        "temporal_relevance": {
            "weight": "variable",
            "examples": ["meeting tomorrow" vs "met last year"]
        },
        "emotional_significance": {
            "weight": "high",
            "examples": ["frustrated with errors", "excited about progress"]
        }
    }
```

---

## 5. Key Algorithms: Memory Management

### 5.1 Context Window Management (Heartbeats)

Letta uses a "heartbeat" mechanism for context management:

```python
# Heartbeat-based context management
class HeartbeatManager:
    """
    Periodically triggers context evaluation and management.
    Similar to OS memory management interrupts.
    """
    
    def __init__(self, max_context_tokens: int = 8000):
        self.max_tokens = max_context_tokens
        self.heartbeat_interval = 10  # messages
    
    async def check_and_compact(self, state: AgentState):
        """Check if context compaction is needed"""
        current_tokens = self._count_tokens(state)
        
        if current_tokens > self.max_tokens * 0.8:
            # Trigger compaction
            await self._compact_context(state)
    
    async def _compact_context(self, state: AgentState):
        """Compact context by summarizing old messages"""
        # 1. Summarize old messages
        summary = await self._summarize_messages(
            state.messages[:-5]  # Keep recent 5
        )
        
        # 2. Store summary in archival memory
        await state.archival_memory.insert(
            f"Conversation summary: {summary}"
        )
        
        # 3. Remove compacted messages from working memory
        state.messages = state.messages[-5:]
        
        # 4. Update core memory if needed
        # Agent decides via tool calls
```

### 5.2 Memory Consolidation

```python
# Memory consolidation algorithm (conceptual)
class MemoryConsolidation:
    """
    Consolidate information across memory tiers.
    Inspired by sleep-dependent memory consolidation.
    """
    
    async def consolidate_session(self, session_id: str):
        """Consolidate session memories into long-term storage"""
        
        # 1. Extract key facts from session
        session_memories = await self.recall_memory.get_session(session_id)
        key_facts = await self._extract_facts(session_memories)
        
        # 2. Check for conflicts with existing memories
        for fact in key_facts:
            conflicts = await self._find_conflicts(fact)
            
            if conflicts:
                # Resolve conflicts - keep most recent/relevant
                await self._resolve_conflict(fact, conflicts)
            else:
                # Store new fact
                await self.archival_memory.insert(fact)
        
        # 3. Update core memory if user preferences changed
        await self._update_core_memory_preferences()
```

### 5.3 Relevance Scoring

```python
# Relevance scoring for memory retrieval
class RelevanceScorer:
    """
    Score memory relevance for retrieval decisions.
    """
    
    def compute_relevance(
        self,
        query: str,
        memory: MemoryItem,
        context: Dict
    ) -> float:
        """
        Compute relevance score combining multiple factors.
        
        Returns:
            Score between 0 and 1
        """
        scores = {}
        
        # 1. Semantic similarity (vector embedding)
        scores['semantic'] = self._semantic_similarity(
            query, memory.content
        )
        
        # 2. Recency factor
        scores['recency'] = self._recency_score(
            memory.timestamp
        )
        
        # 3. Access frequency
        scores['frequency'] = self._frequency_score(
            memory.access_count
        )
        
        # 4. Importance weight (if stored)
        scores['importance'] = memory.importance or 0.5
        
        # 5. Context relevance
        scores['context'] = self._context_relevance(
            memory, context
        )
        
        # Weighted combination
        weights = {
            'semantic': 0.35,
            'recency': 0.20,
            'frequency': 0.15,
            'importance': 0.15,
            'context': 0.15
        }
        
        return sum(
            scores[k] * weights[k] 
            for k in weights
        )
```

### 5.4 Consolidation Triggers

```python
# Triggers for memory consolidation
class ConsolidationTriggers:
    """
    Events that trigger memory consolidation operations.
    """
    
    TRIGGERS = {
        # Context-based triggers
        "context_threshold": {
            "condition": "context_usage > 80%",
            "action": "compact_oldest_messages"
        },
        
        # Session-based triggers
        "session_end": {
            "condition": "session_closed",
            "action": "consolidate_session_memories"
        },
        
        # Importance-based triggers
        "high_importance": {
            "condition": "user_shows_emotional_significance",
            "action": "immediate_archival"
        },
        
        # Periodic triggers
        "periodic_heartbeat": {
            "condition": "every_N_messages",
            "action": "evaluate_memory_state"
        },
        
        # Conflict triggers
        "contradiction_detected": {
            "condition": "new_info_contradicts_stored",
            "action": "resolve_and_update"
        }
    }
```

---

## 6. Integration with LLMs

### 6.1 Model Requirements

Letta works with any LLM that supports:
1. **Function calling / Tool use**
2. **System prompts**
3. **Multi-turn conversations**

```python
# LLM Integration Requirements
class LettaLLMRequirements:
    """Requirements for LLM integration with Letta"""
    
    REQUIRED_CAPABILITIES = [
        "function_calling",      # For memory tools
        "system_prompt",         # For agent persona
        "multi_turn",            # For conversation
        "json_output"            # For structured tool calls
    ]
    
    SUPPORTED_PROVIDERS = {
        "openai": {
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "function_calling": "native"
        },
        "anthropic": {
            "models": ["claude-3-opus", "claude-3-sonnet"],
            "function_calling": "native",
            "memory_tool": "supported"  # New Anthropic memory tool
        },
        "google": {
            "models": ["gemini-pro", "gemini-ultra"],
            "function_calling": "native"
        },
        "local": {
            "models": ["llama-3", "mistral", "qwen"],
            "function_calling": "requires_formatting"
        }
    }
```

### 6.2 Tool Calling Flow

```python
# Tool calling flow for memory operations
async def process_message(
    agent: LettaAgent,
    user_message: str
) -> str:
    """Process user message with memory tool calls"""
    
    # 1. Build context
    context = build_context(
        system_prompt=agent.system_prompt,
        core_memory=agent.core_memory,
        working_memory=agent.working_memory,
        message=user_message
    )
    
    # 2. LLM generates response (possibly with tool calls)
    response = await llm.generate(
        messages=context,
        tools=agent.memory_tools,
        tool_choice="auto"  # LLM decides when to use tools
    )
    
    # 3. Process tool calls if any
    while response.tool_calls:
        for tool_call in response.tool_calls:
            # Execute memory tool
            result = await execute_tool(
                tool_call.name,
                tool_call.arguments
            )
            
            # Add result to context
            context.append({
                "role": "tool",
                "name": tool_call.name,
                "content": result
            })
        
        # Get next response
        response = await llm.generate(
            messages=context,
            tools=agent.memory_tools
        )
    
    # 4. Return final response
    return response.content
```

### 6.3 System Prompt Structure

```python
# Letta System Prompt Structure
LETTA_SYSTEM_PROMPT = """
You are {agent_name}, a helpful AI assistant with persistent memory.

## Your Memory System

You have access to a sophisticated memory system with multiple tiers:

### Core Memory (Always Visible)
Your core memory blocks are always in your context window. Use these to store:
- {persona_block}: Your identity and capabilities
- {human_block}: Information about the user
- {tasks_block}: Current tasks and goals

### Archival Memory (Long-term Storage)
Store important information for long-term recall using archival_memory_insert.
Search your knowledge base with archival_memory_search.

### Recall Memory (Conversation History)
Search past conversations with conversation_search.

## Memory Management Guidelines

1. **Remember Important Information**: When the user shares preferences, 
   personal details, or important facts, store them in core memory.

2. **Long-term Storage**: Information that may be useful in future 
   conversations should go to archival memory.

3. **Update When Needed**: Use core_memory_replace to update outdated 
   information.

4. **Search Before Assuming**: Check your memory before making assumptions 
   about the user.

5. **Be Selective**: Don't store everything - focus on information that 
   helps provide personalized assistance.

## Current Memory State

{core_memory_state}

Remember: You control your own memory. Use your tools wisely to provide 
the best possible assistance.
"""
```

---

## 7. Implementation: Phase 3 Self-Directed Memory

### 7.1 Architecture for Implementation

```python
# Self-Directed Memory System Implementation
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class MemoryTier(Enum):
    """Memory tier classification"""
    CORE = "core"           # Always in context
    WORKING = "working"     # Recent messages
    RECALL = "recall"       # Conversation history
    ARCHIVAL = "archival"   # Long-term semantic storage


@dataclass
class MemoryBlock:
    """A structured memory block"""
    label: str
    content: str
    limit: int = 2000
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def can_append(self, text: str) -> bool:
        return len(self.content) + len(text) <= self.limit
    
    def append(self, text: str) -> bool:
        if self.can_append(text):
            self.content += text
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def replace(self, old: str, new: str) -> bool:
        if old in self.content:
            self.content = self.content.replace(old, new)
            self.updated_at = datetime.utcnow()
            return True
        return False


@dataclass
class ArchivalEntry:
    """Entry in archival memory"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0


class SelfDirectedMemory:
    """
    Implementation of Letta-style self-directed memory.
    Agents can modify their own memory using tools.
    """
    
    def __init__(
        self,
        agent_id: str,
        vector_db: Optional[Any] = None
    ):
        self.agent_id = agent_id
        
        # Memory Tiers
        self.core_memory: Dict[str, MemoryBlock] = {}
        self.working_memory: List[Dict] = []
        self.recall_memory: List[Dict] = []
        self.archival_memory: List[ArchivalEntry] = []
        
        # Vector database for semantic search
        self.vector_db = vector_db
        
        # Initialize default core memory blocks
        self._init_core_memory()
        
        # Memory tools the agent can call
        self.tools = self._define_tools()
    
    def _init_core_memory(self):
        """Initialize default core memory blocks"""
        self.core_memory = {
            "persona": MemoryBlock(
                label="persona",
                content="I am a helpful AI assistant with persistent memory.",
                limit=2000
            ),
            "human": MemoryBlock(
                label="human", 
                content="",
                limit=2000
            ),
            "tasks": MemoryBlock(
                label="tasks",
                content="",
                limit=1000
            )
        }
    
    def _define_tools(self) -> List[Dict]:
        """Define memory tools the agent can use"""
        return [
            {
                "name": "core_memory_append",
                "description": "Append content to a core memory block",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "enum": list(self.core_memory.keys())
                        },
                        "content": {"type": "string"}
                    },
                    "required": ["label", "content"]
                }
            },
            {
                "name": "core_memory_replace",
                "description": "Replace content in a core memory block",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "old_content": {"type": "string"},
                        "new_content": {"type": "string"}
                    },
                    "required": ["label", "old_content", "new_content"]
                }
            },
            {
                "name": "archival_memory_insert",
                "description": "Store information in long-term memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "archival_memory_search",
                "description": "Search long-term memory semantically",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "conversation_search",
                "description": "Search past conversations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    # ==========================================
    # Core Memory Operations
    # ==========================================
    
    def core_memory_append(
        self,
        label: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Append content to a core memory block.
        Called by the agent through tool use.
        """
        if label not in self.core_memory:
            return {
                "success": False,
                "error": f"Unknown memory block: {label}"
            }
        
        block = self.core_memory[label]
        
        if block.append(content):
            return {
                "success": True,
                "message": f"Appended to {label}. Block size: {len(block.content)}/{block.limit}",
                "block_size": len(block.content)
            }
        else:
            return {
                "success": False,
                "error": f"Block {label} is full. Current: {len(block.content)}/{block.limit}"
            }
    
    def core_memory_replace(
        self,
        label: str,
        old_content: str,
        new_content: str
    ) -> Dict[str, Any]:
        """
        Replace content in a core memory block.
        Called by the agent through tool use.
        """
        if label not in self.core_memory:
            return {
                "success": False,
                "error": f"Unknown memory block: {label}"
            }
        
        block = self.core_memory[label]
        
        if block.replace(old_content, new_content):
            return {
                "success": True,
                "message": f"Updated {label}"
            }
        else:
            return {
                "success": False,
                "error": f"Content not found in {label}"
            }
    
    # ==========================================
    # Archival Memory Operations
    # ==========================================
    
    async def archival_memory_insert(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Store information in archival memory.
        Creates embedding for semantic search.
        """
        entry_id = f"arch_{len(self.archival_memory)}"
        
        entry = ArchivalEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {}
        )
        
        # Create embedding if vector DB available
        if self.vector_db:
            entry.embedding = await self._create_embedding(content)
            await self.vector_db.insert(entry)
        
        self.archival_memory.append(entry)
        
        return {
            "success": True,
            "memory_id": entry_id,
            "message": f"Stored in archival memory"
        }
    
    async def archival_memory_search(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search archival memory semantically.
        """
        results = []
        
        if self.vector_db:
            # Use vector search
            query_embedding = await self._create_embedding(query)
            results = await self.vector_db.search(query_embedding, limit)
        else:
            # Fallback to simple text search
            query_lower = query.lower()
            for entry in self.archival_memory:
                if query_lower in entry.content.lower():
                    entry.access_count += 1
                    results.append({
                        "id": entry.id,
                        "content": entry.content,
                        "metadata": entry.metadata,
                        "score": 1.0  # Simple match
                    })
        
        return {
            "success": True,
            "results": results[:limit],
            "total": len(results)
        }
    
    # ==========================================
    # Context Building
    # ==========================================
    
    def build_context(
        self,
        include_working: bool = True,
        include_recent_messages: int = 10
    ) -> str:
        """
        Build the context string for the LLM.
        Includes core memory and optionally working memory.
        """
        context_parts = []
        
        # Core memory (always included)
        context_parts.append("=== CORE MEMORY ===")
        for label, block in self.core_memory.items():
            if block.content:
                context_parts.append(f"\n[{label.upper()}]\n{block.content}")
        
        # Working memory (recent messages)
        if include_working and self.working_memory:
            context_parts.append("\n=== RECENT MESSAGES ===")
            recent = self.working_memory[-include_recent_messages:]
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"\n{role}: {content}")
        
        return "\n".join(context_parts)
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    async def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for text (placeholder)"""
        # In production, use actual embedding model
        # return await embedding_model.embed(text)
        return []
    
    def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state for system prompt"""
        return {
            "core_memory": {
                label: {
                    "content": block.content,
                    "size": len(block.content),
                    "limit": block.limit
                }
                for label, block in self.core_memory.items()
            },
            "working_memory_count": len(self.working_memory),
            "archival_count": len(self.archival_memory)
        }
```

### 7.2 Integration with Agent Loop

```python
# Agent loop with self-directed memory
class LettaStyleAgent:
    """
    Agent with self-directed memory management.
    """
    
    def __init__(
        self,
        llm_client: Any,
        memory: SelfDirectedMemory
    ):
        self.llm = llm_client
        self.memory = memory
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with memory instructions"""
        return """
You are an AI assistant with self-directed memory capabilities.

## Memory Tools Available

You have access to the following memory tools:

1. **core_memory_append(label, content)**: Add information to core memory
   - Use for: User preferences, important facts, ongoing context
   - Labels: "persona", "human", "tasks"

2. **core_memory_replace(label, old_content, new_content)**: Update existing memory
   - Use for: Correcting or updating information

3. **archival_memory_insert(content)**: Store for long-term
   - Use for: Important information that may be needed later

4. **archival_memory_search(query)**: Search long-term memory
   - Use for: Recalling past information

## Memory Guidelines

- Be proactive about remembering important information
- Store user preferences and personal details
- Update memories when you learn new information
- Search your memory before making assumptions
- Don't over-store trivial information
"""
    
    async def process_message(
        self,
        user_message: str
    ) -> str:
        """Process user message with memory operations"""
        
        # Add to working memory
        self.memory.working_memory.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": self.memory.build_context()},
            {"role": "user", "content": user_message}
        ]
        
        # Get LLM response with tool calling
        response = await self.llm.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=self.memory.tools,
            tool_choice="auto"
        )
        
        # Process tool calls
        while response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            
            for tool_call in tool_calls:
                # Execute the memory tool
                result = await self._execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                
                # Add tool result to messages
                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            # Get next response
            response = await self.llm.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=self.memory.tools
            )
        
        # Extract final response
        final_response = response.choices[0].message.content
        
        # Add to working memory
        self.memory.working_memory.append({
            "role": "assistant",
            "content": final_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return final_response
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict
    ) -> Dict:
        """Execute a memory tool"""
        
        if tool_name == "core_memory_append":
            return self.memory.core_memory_append(
                arguments["label"],
                arguments["content"]
            )
        
        elif tool_name == "core_memory_replace":
            return self.memory.core_memory_replace(
                arguments["label"],
                arguments["old_content"],
                arguments["new_content"]
            )
        
        elif tool_name == "archival_memory_insert":
            return await self.memory.archival_memory_insert(
                arguments["content"]
            )
        
        elif tool_name == "archival_memory_search":
            return await self.memory.archival_memory_search(
                arguments["query"],
                arguments.get("limit", 10)
            )
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
```

---

## 8. Comparison: Letta vs Other Memory Systems

| Feature | Letta/MemGPT | Mem0 | Zep | Simple RAG |
|---------|--------------|------|-----|------------|
| **Self-Directed** | ✅ Full autonomy | ❌ Manual config | ⚠️ Partial | ❌ No |
| **Memory Tiers** | ✅ 4 tiers | ⚠️ 2 tiers | ✅ 3 tiers | ❌ 1 tier |
| **Tool-Based** | ✅ Native | ❌ API-based | ⚠️ Hybrid | ❌ No |
| **OS-Inspired** | ✅ Full paradigm | ❌ No | ❌ No | ❌ No |
| **Unlimited Context** | ✅ Virtual context | ⚠️ Limited | ⚠️ Limited | ✅ Yes |
| **Conflict Resolution** | ⚠️ Manual | ❌ No | ✅ Auto | ❌ No |
| **Knowledge Graph** | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Open Source** | ✅ Yes | ✅ Yes | ⚠️ Partial | ✅ Varies |

---

## 9. Key Takeaways for Implementation

### 9.1 Core Principles

1. **Memory as Tools**: Letta treats memory operations as function tools the agent can call
2. **Self-Editing**: Agents decide what to remember, not developers
3. **Tiered Architecture**: Different memory tiers for different purposes
4. **Context Management**: OS-inspired virtual memory for unlimited context
5. **Tool-Based Autonomy**: No hard-coded memory rules

### 9.2 Implementation Checklist

- [ ] Implement core memory blocks with append/replace operations
- [ ] Add archival memory with vector search
- [ ] Create memory tools as function definitions
- [ ] Build context from memory state
- [ ] Add conversation search capability
- [ ] Implement heartbeat-based context management
- [ ] Add memory consolidation triggers
- [ ] Test with various LLM providers

### 9.3 Best Practices

1. **Start with clear system prompts** explaining memory tools
2. **Use appropriate memory tier** for different information types
3. **Monitor memory usage** and implement compaction
4. **Test agent memory decisions** before production
5. **Consider embedding quality** for archival search

---

## 10. Resources

### Official Sources
- **GitHub**: https://github.com/letta-ai/letta
- **Documentation**: https://docs.letta.com
- **Website**: https://www.letta.com
- **MemGPT Paper**: https://arxiv.org/abs/2310.08560

### Learning Resources
- **DeepLearning.AI Course**: "LLMs as Operating Systems: Agent Memory"
- **Letta Blog**: https://www.letta.com/blog
- **Agent Memory Techniques**: https://github.com/NirDiamant/Agent_Memory_Techniques

---

## 11. Conclusion

Letta (MemGPT) represents a paradigm shift in AI agent memory management. By treating memory operations as tools and giving agents autonomy over their own memory, Letta enables:

- **Unlimited effective context** through OS-inspired virtual memory
- **Personalized agents** that learn and remember user preferences
- **Self-improving systems** that update their own knowledge
- **Stateful interactions** across sessions and conversations

For Phase 3 implementation, the key is implementing the memory tools as callable functions and designing a system prompt that guides the agent to use them effectively. The agent itself becomes the memory manager, making autonomous decisions about what to store, update, and retrieve.

---

*Research compiled from Letta documentation, MemGPT paper (arXiv:2310.08560), and various technical sources.*
