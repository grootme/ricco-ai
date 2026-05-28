#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for RICCO AI
Tests each integration individually with proper error handling
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Results storage
results = {}

def log_test(category: str, test_name: str, success: bool, message: str = "", details: Any = None):
    """Log a test result"""
    key = f"{category}/{test_name}"
    results[key] = {
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}: {message}")
    return success


async def test_openrouter():
    """Test 1: OpenRouter Integration"""
    print("\n" + "="*60)
    print("TEST 1: OpenRouter Integration")
    print("="*60)
    
    import httpx
    
    api_key = os.environ.get("OPENROUTER_API_KEY", "REDACTED_API_KEY")
    
    # Test 1a: Models endpoint
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if response.status_code == 200:
                data = response.json()
                log_test("OpenRouter", "Models Endpoint", True, f"Found {len(data.get('data', []))} models")
            else:
                log_test("OpenRouter", "Models Endpoint", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("OpenRouter", "Models Endpoint", False, str(e))
    
    # Test 1b: Chat completion
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ricco.ai"
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": "Say 'OK'"}],
                    "max_tokens": 10
                }
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                log_test("OpenRouter", "Chat Completion", True, f"Response: {content[:30]}")
            else:
                log_test("OpenRouter", "Chat Completion", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("OpenRouter", "Chat Completion", False, str(e))


async def test_ai_providers():
    """Test 2: AI Providers"""
    print("\n" + "="*60)
    print("TEST 2: AI Providers")
    print("="*60)
    
    providers_to_test = [
        ("OpenAI", "ai_providers.providers", "OpenAIProvider"),
        ("Anthropic", "ai_providers.providers.anthropic_provider", "AnthropicProvider"),
        ("Local", "ai_providers.providers.local_provider", "LocalProvider"),
    ]
    
    for name, module_path, class_name in providers_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            log_test("AI Providers", name, True, f"{class_name} available")
        except ImportError as e:
            log_test("AI Providers", name, False, str(e))


async def test_mcp_servers():
    """Test 3: MCP Servers"""
    print("\n" + "="*60)
    print("TEST 3: MCP Servers")
    print("="*60)
    
    # Test base server
    try:
        from mcp.servers.base_server import BaseMCPServer
        log_test("MCP", "Base Server", True, "BaseMCPServer imported")
    except ImportError as e:
        log_test("MCP", "Base Server", False, str(e))
    
    # Test multi-agent server
    try:
        from mcp.servers.multi_agent_server import MultiAgentMCPServer
        log_test("MCP", "Multi-Agent Server", True, "MultiAgentMCPServer imported")
    except ImportError as e:
        log_test("MCP", "Multi-Agent Server", False, str(e))
    
    # Test tools
    try:
        from mcp.tools.tool_definitions import TOOL_DEFINITIONS
        log_test("MCP", "Tool Definitions", True, f"{len(TOOL_DEFINITIONS)} tools defined")
    except ImportError as e:
        log_test("MCP", "Tool Definitions", False, str(e))


async def test_blueprints():
    """Test 4: Blueprints"""
    print("\n" + "="*60)
    print("TEST 4: Blueprints")
    print("="*60)
    
    try:
        from blueprints.registry import BlueprintRegistry
        registry = BlueprintRegistry()
        blueprints = registry.list_blueprints()
        log_test("Blueprints", "Registry", True, f"{len(blueprints)} blueprints registered")
    except Exception as e:
        log_test("Blueprints", "Registry", False, str(e))
    
    try:
        from blueprints.rag import RAGBlueprint
        log_test("Blueprints", "RAG Blueprint", True, "Available")
    except ImportError as e:
        log_test("Blueprints", "RAG Blueprint", False, str(e))


async def test_vector_stores():
    """Test 5: Vector Stores"""
    print("\n" + "="*60)
    print("TEST 5: Vector Stores")
    print("="*60)
    
    # Qdrant
    try:
        from infra.vector.qdrant_store import QdrantVectorStore
        log_test("Vector Stores", "Qdrant Import", True, "QdrantVectorStore imported")
    except ImportError as e:
        log_test("Vector Stores", "Qdrant Import", False, str(e))
    
    # Milvus
    try:
        from infra.vector.milvus_store import MilvusVectorStore
        log_test("Vector Stores", "Milvus Import", True, "MilvusVectorStore imported")
    except ImportError as e:
        log_test("Vector Stores", "Milvus Import", False, str(e))


async def test_config():
    """Test 6: Configuration"""
    print("\n" + "="*60)
    print("TEST 6: Configuration")
    print("="*60)
    
    try:
        from config.settings import settings
        log_test("Config", "Settings", True, f"API: {settings.API_TITLE}")
    except Exception as e:
        log_test("Config", "Settings", False, str(e))
    
    try:
        from config.openrouter_config import OpenRouterConfig, FREE_MODELS
        log_test("Config", "OpenRouter Config", True, f"{len(FREE_MODELS)} free models configured")
    except Exception as e:
        log_test("Config", "OpenRouter Config", False, str(e))


async def test_services():
    """Test 7: Core Services"""
    print("\n" + "="*60)
    print("TEST 7: Core Services")
    print("="*60)
    
    # A2UI Service
    try:
        from services.a2ui import A2UIService, ComponentType
        log_test("Services", "A2UI Service", True, "A2UIService imported")
    except ImportError as e:
        log_test("Services", "A2UI Service", False, str(e))
    
    # Context Engine
    try:
        from services.context_engine import ContextEngine
        log_test("Services", "Context Engine", True, "ContextEngine imported")
    except ImportError as e:
        log_test("Services", "Context Engine", False, str(e))


async def test_queue_system():
    """Test 8: Queue System"""
    print("\n" + "="*60)
    print("TEST 8: Queue System")
    print("="*60)
    
    try:
        from task_queue.event_dispatcher import EventDispatcher
        log_test("Queue", "Event Dispatcher", True, "EventDispatcher imported")
    except ImportError as e:
        log_test("Queue", "Event Dispatcher", False, str(e))
    
    try:
        from task_queue.worker import QueueWorker
        log_test("Queue", "Queue Worker", True, "QueueWorker imported")
    except ImportError as e:
        log_test("Queue", "Queue Worker", False, str(e))


async def test_schemas():
    """Test 9: Schemas"""
    print("\n" + "="*60)
    print("TEST 9: Schemas")
    print("="*60)
    
    try:
        from schemas.a2a_types import AgentCard, AgentCapabilities
        log_test("Schemas", "A2A Types", True, "AgentCard imported")
    except ImportError as e:
        log_test("Schemas", "A2A Types", False, str(e))
    
    try:
        from schemas.chat import ChatMessage, ChatSession
        log_test("Schemas", "Chat Schemas", True, "ChatMessage imported")
    except ImportError as e:
        log_test("Schemas", "Chat Schemas", False, str(e))


async def test_integration_modules():
    """Test 10: Integration Modules"""
    print("\n" + "="*60)
    print("TEST 10: Integration Modules")
    print("="*60)
    
    try:
        from integration.integration_service import IntegrationService
        log_test("Integration", "Integration Service", True, "IntegrationService imported")
    except ImportError as e:
        log_test("Integration", "Integration Service", False, str(e))
    
    try:
        from core.container import ServiceContainer
        log_test("Integration", "Service Container", True, "ServiceContainer imported")
    except ImportError as e:
        log_test("Integration", "Service Container", False, str(e))
    
    try:
        from core.protocols import ServiceProtocol
        log_test("Integration", "Protocols", True, "ServiceProtocol imported")
    except ImportError as e:
        log_test("Integration", "Protocols", False, str(e))


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "#"*60)
    print("# RICCO AI - COMPREHENSIVE INTEGRATION TEST SUITE")
    print(f"# Started: {datetime.now().isoformat()}")
    print("#"*60)
    
    start_time = time.time()
    
    # Run tests
    await test_openrouter()
    await test_ai_providers()
    await test_mcp_servers()
    await test_blueprints()
    await test_vector_stores()
    await test_config()
    await test_services()
    await test_queue_system()
    await test_schemas()
    await test_integration_modules()
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    total = len(results)
    passed = sum(1 for r in results.values() if r["success"])
    failed = total - passed
    
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Duration: {duration:.2f} seconds")
    
    # Group by category
    categories = {}
    for key, result in results.items():
        category, test = key.split("/")
        if category not in categories:
            categories[category] = {"passed": 0, "failed": 0}
        if result["success"]:
            categories[category]["passed"] += 1
        else:
            categories[category]["failed"] += 1
    
    print("\nBy Category:")
    for cat, stats in categories.items():
        total_cat = stats["passed"] + stats["failed"]
        print(f"  {cat}: {stats['passed']}/{total_cat} passed")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed/total)*100
        },
        "by_category": categories,
        "results": results
    }
    
    with open('/home/z/my-project/download/integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: /home/z/my-project/download/integration_test_report.json")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(run_all_tests())
