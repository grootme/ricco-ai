#!/usr/bin/env python3
"""
Agent Generator - Automatically generates agents from configuration.

This script demonstrates the OCP-compliant architecture:
- NO hardcoded agent types
- Agents are generated from domains.json and roles.json
- Adding a new domain or role automatically creates new agents

To add a new agent:
1. Add domain to domains.json OR
2. Add role to roles.json OR  
3. Add custom agent to agents.json

NO CODE CHANGES REQUIRED.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from itertools import product

# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent / "src" / "config"
DOMAINS_FILE = CONFIG_DIR / "domains.json"
ROLES_FILE = CONFIG_DIR / "roles.json"
PLATFORM_FILE = CONFIG_DIR / "platform.json"
AGENTS_FILE = CONFIG_DIR / "agents.json"


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON configuration file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_agent_id(domain: str, role: str) -> str:
    """Generate a unique agent ID."""
    return f"{role}_{domain}"


def generate_agent_name(domain_config: Dict, role_config: Dict) -> str:
    """Generate agent name from configuration."""
    domain_elegant = domain_config.get("elegant_name", domain_config.get("name", "Custom"))
    role_elegant = role_config.get("elegant_name", role_config.get("name", "Agent"))
    return f"{domain_elegant} {role_elegant}"


def generate_agent(
    domain_id: str,
    domain_config: Dict,
    role_id: str,
    role_config: Dict,
    platform_config: Dict,
) -> Dict[str, Any]:
    """
    Generate an agent definition from configuration.
    
    NO HARDCODED VALUES - Everything comes from configuration.
    """
    agent_id = generate_agent_id(domain_id, role_id)
    name = generate_agent_name(domain_config, role_config)
    
    # Get defaults from platform config
    role_defaults = platform_config.get("role_defaults", {}).get(role_id, {})
    domain_mcp = platform_config.get("domain_defaults", {}).get("mcp_servers_by_domain", {}).get(domain_id, [])
    agent_template = platform_config.get("agent_templates", {}).get("default", {})
    
    # Merge capabilities
    capabilities = {
        "skills": list(set(
            role_config.get("skills", []) +
            role_defaults.get("skills", [])
        )),
        "tools": list(set(
            role_config.get("tools", []) +
            role_defaults.get("tools", [])
        )),
        "mcp_servers": list(set(
            domain_config.get("mcp_servers", []) +
            domain_mcp
        )),
    }
    
    # Merge behavior
    role_behavior = role_defaults.get("behavior", {})
    behavior = {
        "tone": role_behavior.get("tone", role_config.get("elegant_name", "professional").lower()),
        "style": role_behavior.get("style", "balanced"),
        "response_format": role_config.get("response_format", "default"),
    }
    
    # Generate prompts from configuration
    prompts = {
        "system": f"You are a {role_config.get('elegant_name', role_id)} agent specialized in {domain_config.get('name', domain_id)}. {role_config.get('description', '')}",
        "task_template": f"Task: {{query}}\nDomain: {domain_config.get('name', domain_id)}\nRole: {role_config.get('elegant_name', role_id)}\nProvide detailed response."
    }
    
    # Get limits
    limits = agent_template.get("limits", {
        "max_tokens": 4096,
        "timeout_seconds": 60,
        "max_retries": 3
    })
    
    return {
        "id": agent_id,
        "name": name,
        "description": f"{role_config.get('description', '')} for {domain_config.get('name', domain_id)}",
        "domain": domain_id,
        "role": role_id,
        "capabilities": capabilities,
        "behavior": behavior,
        "prompts": prompts,
        "limits": limits,
        "enabled": True,
        "is_coordinator": False,
        "generated": True,
    }


def generate_coordinator(platform_config: Dict, domains: Dict) -> Dict[str, Any]:
    """Generate the coordinator agent."""
    nexus_config = platform_config.get("platform", {})
    
    return {
        "id": "nexus_coordinator",
        "name": nexus_config.get("name", "NEXUS"),
        "description": nexus_config.get("description", "Super Agent Coordinator"),
        "domain": "system",
        "role": "coordinator",
        "capabilities": {
            "skills": ["orchestration", "routing", "aggregation", "delegation"],
            "tools": ["agent-router", "response-aggregator", "context-manager"],
            "mcp_servers": ["all-available"]
        },
        "behavior": {
            "tone": "authoritative",
            "style": "comprehensive",
            "response_format": "unified"
        },
        "prompts": {
            "system": f"You are {nexus_config.get('name', 'NEXUS')}, the central coordinator. {nexus_config.get('tagline', '')}",
            "task_template": "Coordinate: {query}\nAvailable agents: {agents}\nProvide unified response."
        },
        "limits": {
            "max_tokens": 8192,
            "timeout_seconds": 300,
            "max_retries": 3
        },
        "enabled": True,
        "is_coordinator": True,
        "generated": True,
    }


def generate_agent_groups(
    domains: Dict,
    roles: Dict,
    agents: Dict[str, Dict],
) -> Dict[str, Dict]:
    """Generate agent groups from configuration."""
    groups = {}
    
    for domain_id, domain_config in domains.items():
        if domain_id == "custom":
            continue
            
        # Find all agents for this domain
        domain_agents = [
            agent_id for agent_id, agent in agents.items()
            if agent.get("domain") == domain_id and not agent.get("is_coordinator")
        ]
        
        if domain_agents:
            groups[f"{domain_id}_team"] = {
                "id": f"{domain_id}_team",
                "name": f"{domain_config.get('elegant_name', domain_id)} Team",
                "domain": domain_id,
                "agent_ids": domain_agents,
                "coordinator": "nexus_coordinator",
            }
    
    return groups


def main():
    """Generate all agents from configuration."""
    print("🚀 Generating agents from configuration...")
    
    # Load configurations
    domains_data = load_json(DOMAINS_FILE)
    roles_data = load_json(ROLES_FILE)
    platform_data = load_json(PLATFORM_FILE)
    
    domains = domains_data.get("domains", {})
    roles = roles_data.get("roles", {})
    platform_config = platform_data
    
    print(f"   Loaded {len(domains)} domains, {len(roles)} roles")
    
    # Generate agents for each domain × role combination
    agents = {}
    
    for domain_id, domain_config in domains.items():
        if domain_id == "custom":
            continue
            
        for role_id, role_config in roles.items():
            agent = generate_agent(
                domain_id=domain_id,
                domain_config=domain_config,
                role_id=role_id,
                role_config=role_config,
                platform_config=platform_config,
            )
            agents[agent["id"]] = agent
            print(f"   ✓ Generated: {agent['id']}")
    
    # Add coordinator
    coordinator = generate_coordinator(platform_config, domains)
    agents[coordinator["id"]] = coordinator
    print(f"   ✓ Generated: {coordinator['id']} (coordinator)")
    
    # Generate groups
    groups = generate_agent_groups(domains, roles, agents)
    print(f"   ✓ Generated {len(groups)} agent groups")
    
    # Load existing custom agents (if any)
    try:
        existing_data = load_json(AGENTS_FILE)
        existing_agents = existing_data.get("agents", {})
        
        # Preserve manually defined agents (not generated)
        for agent_id, agent in existing_agents.items():
            if not agent.get("generated"):
                agents[agent_id] = agent
                print(f"   ✓ Preserved custom agent: {agent_id}")
    except FileNotFoundError:
        pass
    
    # Build output
    output = {
        "version": "1.0.0",
        "description": "Auto-generated agents from configuration - DO NOT EDIT generated agents directly",
        "generated_at": str(Path(__file__).stat().st_mtime),
        "agents": agents,
        "agent_groups": groups,
    }
    
    # Save
    with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Generated {len(agents)} agents, {len(groups)} groups")
    print(f"   Saved to: {AGENTS_FILE}")
    print("\n💡 To add a new agent:")
    print("   1. Add domain to domains.json, OR")
    print("   2. Add role to roles.json, OR")
    print("   3. Add custom agent directly to agents.json")
    print("   NO CODE CHANGES REQUIRED!")


if __name__ == "__main__":
    main()
