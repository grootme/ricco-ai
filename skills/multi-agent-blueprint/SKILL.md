# Multi-Agent Blueprint Skill

## Overview
NVIDIA Multi-Agent Blueprint integration for orchestrating multiple AI agents with hierarchical task delegation, agent-to-agent communication, and collaborative problem solving.

## Description
This skill provides tools for building multi-agent systems where specialized agents work together to solve complex tasks. It supports various coordination patterns including:

- **Hierarchical Orchestration**: Lead agent delegates to specialized sub-agents
- **Swarm Intelligence**: Multiple agents collaborate as equals
- **Pipeline Processing**: Sequential agent execution with handoffs
- **Debate & Consensus**: Agents discuss and reach conclusions

## Tools (12)

### multiagent_init
Initialize a multi-agent system with configuration.

**Parameters:**
- `system_name` (required): Name of the multi-agent system
- `orchestration_pattern` (required): 'hierarchical', 'swarm', 'pipeline', or 'debate'
- `max_agents` (optional): Maximum number of agents (default: 10)
- `communication_protocol` (optional): 'direct', 'broadcast', or 'pubsub'

### multiagent_create_agent
Create a new agent in the system.

**Parameters:**
- `agent_name` (required): Unique name for the agent
- `role` (required): Agent role (e.g., 'researcher', 'writer', 'reviewer')
- `capabilities` (required): List of agent capabilities
- `model_config` (optional): LLM configuration for the agent
- `tools` (optional): List of tools available to the agent

### multiagent_create_lead
Create a lead/orchestrator agent.

**Parameters:**
- `lead_name` (required): Name for the lead agent
- `sub_agents` (required): List of sub-agent names to manage
- `delegation_strategy` (optional): 'round_robin', 'capability_match', or 'load_balance'
- `timeout_seconds` (optional): Maximum time for task completion

### multiagent_delegate_task
Delegate a task to the agent system.

**Parameters:**
- `task_description` (required): Description of the task
- `assigned_to` (optional): Specific agent name or 'auto'
- `priority` (optional): 'low', 'medium', 'high', or 'critical'
- `context` (optional): Additional context for the task
- `dependencies` (optional): List of task IDs that must complete first

### multiagent_send_message
Send a message between agents.

**Parameters:**
- `from_agent` (required): Sender agent name
- `to_agent` (required): Recipient agent name or 'broadcast'
- `message_type` (required): 'task', 'query', 'result', or 'control'
- `content` (required): Message content
- `requires_response` (optional): Whether a response is expected

### multiagent_get_status
Get status of agents and tasks.

**Parameters:**
- `agent_name` (optional): Specific agent or 'all'
- `include_tasks` (optional): Include active tasks (default: true)
- `include_history` (optional): Include task history (default: false)

### multiagent_create_workflow
Create a multi-agent workflow.

**Parameters:**
- `workflow_name` (required): Name for the workflow
- `steps` (required): List of workflow steps with agent assignments
- `parallel_steps` (optional): Steps that can run in parallel
- `error_handling` (optional): 'stop', 'continue', or 'retry'

### multiagent_execute_workflow
Execute a defined workflow.

**Parameters:**
- `workflow_name` (required): Name of the workflow to execute
- `input_data` (required): Input data for the workflow
- `timeout_seconds` (optional): Maximum execution time
- `checkpoint_enabled` (optional): Enable checkpointing for recovery

### multiagent_debate
Initiate a debate between agents.

**Parameters:**
- `topic` (required): Debate topic
- `agents` (required): List of participating agents
- `rounds` (optional): Number of debate rounds (default: 3)
- `consensus_threshold` (optional): Agreement threshold (0.0-1.0)

### multiagent_merge_results
Merge results from multiple agents.

**Parameters:**
- `task_id` (required): Original task ID
- `agent_results` (required): List of results from different agents
- `merge_strategy` (optional): 'vote', 'average', 'best', or 'combine'
- `tie_breaker` (optional): How to handle ties

### multiagent_set_memory
Set shared memory for agents.

**Parameters:**
- `key` (required): Memory key
- `value` (required): Value to store
- `scope` (optional): 'system', 'workflow', or 'task'
- `ttl_seconds` (optional): Time-to-live for the memory

### multiagent_get_memory
Retrieve shared memory.

**Parameters:**
- `key` (required): Memory key or pattern
- `scope` (optional): Scope to search in

## Orchestration Patterns

### Hierarchical Pattern
```
Lead Agent
├── Research Agent
├── Analysis Agent
└── Writing Agent
```

### Swarm Pattern
```
Agent A ←→ Agent B
    ↕        ↕
Agent C ←→ Agent D
```

### Pipeline Pattern
```
Input → Agent1 → Agent2 → Agent3 → Output
```

### Debate Pattern
```
        ┌── Agent A ──┐
Topic ──┼── Agent B ──┼── Consensus
        └── Agent C ──┘
```

## Usage Examples

### Creating a Research Team
```
1. multiagent_init(system_name="research_team", orchestration_pattern="hierarchical")
2. multiagent_create_agent(agent_name="researcher", role="researcher", capabilities=["web_search", "summarize"])
3. multiagent_create_agent(agent_name="analyst", role="analyst", capabilities=["analyze", "compare"])
4. multiagent_create_agent(agent_name="writer", role="writer", capabilities=["write", "format"])
5. multiagent_create_lead(lead_name="lead", sub_agents=["researcher", "analyst", "writer"])
6. multiagent_delegate_task(task_description="Research AI trends in 2024")
```

### Running a Debate
```
1. multiagent_init(system_name="debate_team", orchestration_pattern="debate")
2. multiagent_create_agent(agent_name="proponent", role="proponent", capabilities=["argue"])
3. multiagent_create_agent(agent_name="opponent", role="opponent", capabilities=["argue"])
4. multiagent_debate(topic="AI should be regulated", agents=["proponent", "opponent"], rounds=3)
```

## Integration with LangGraph

This skill integrates with LangGraph 1.2.0 for agent state management and interrupt/resume capabilities:

- Use `interrupt()` for human-in-the-loop workflows
- State persistence across sessions
- Checkpoint recovery for long-running tasks

## Configuration

### Environment Variables
- `NVIDIA_API_KEY`: NVIDIA NIM API key (optional, falls back to OpenRouter)
- `OPENROUTER_API_KEY`: OpenRouter API key
- `DEFAULT_MODEL`: Default model for agents
- `MULTIAGENT_MAX_AGENTS`: Maximum agents per system
- `MULTIAGENT_TIMEOUT`: Default timeout in seconds

### Agent Profiles
Agents can be configured with profiles from `agents.json`:
```json
{
  "researcher": {
    "model": "openrouter/free",
    "system_prompt": "You are a research specialist...",
    "tools": ["web_search", "summarize"]
  }
}
```

## References

- [NVIDIA Multi-Agent Blueprint](https://developer.nvidia.com/blueprints)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Agent Communication Protocols](./references/protocols.md)
- [Workflow Patterns](./references/workflows.md)
