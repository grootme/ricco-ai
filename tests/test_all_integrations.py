#!/usr/bin/env python3
"""
Script de Pruebas de Integración Completo
Prueba todas las integraciones del proyecto RICCO AI una por una.
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project to path
sys.path.insert(0, '/home/z/my-project')
sys.path.insert(0, '/home/z/my-project/src')

# Load environment variables
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ricco_ai')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('QDRANT_URL', 'http://localhost:6333')

# Test results storage
test_results = []

def log_result(test_name: str, success: bool, message: str, details: Any = None):
    """Log test result"""
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {test_name}: {message}")
    if details and not success:
        print(f"    Details: {details}")


async def test_openrouter():
    """Test 1: OpenRouter Integration"""
    print("\n" + "="*60)
    print("TEST 1: OpenRouter Integration")
    print("="*60)
    
    try:
        from config.openrouter_config import OpenRouterConfig, OpenRouterClient
        
        # Test configuration
        config = OpenRouterConfig()
        
        if not config.api_key:
            log_result("OpenRouter Config", False, "API key not found in environment")
            return False
        
        log_result("OpenRouter Config", True, f"API key loaded: {config.api_key[:20]}...")
        
        # Test API call
        client = OpenRouterClient(config)
        
        messages = [{"role": "user", "content": "Say 'Hello, this is a test' in exactly those words."}]
        
        print("  Calling OpenRouter API with model: meta-llama/llama-3.1-8b-instruct...")
        
        try:
            response = await client.chat_completion(
                messages=messages,
                model="meta-llama/llama-3.1-8b-instruct",
                max_tokens=50
            )
            
            if "choices" in response:
                content = response["choices"][0]["message"]["content"]
                log_result("OpenRouter API Call", True, f"Response: {content[:100]}...")
                return True
            else:
                log_result("OpenRouter API Call", False, "No choices in response", response)
                return False
                
        except Exception as e:
            log_result("OpenRouter API Call", False, str(e))
            return False
            
    except ImportError as e:
        log_result("OpenRouter Import", False, str(e))
        return False


async def test_openrouter_provider():
    """Test 1b: OpenRouter Provider Class"""
    print("\n--- Testing OpenRouter Provider ---")
    
    try:
        from ai_providers.providers.openrouter_provider import OpenRouterProvider, OpenRouterProviderConfig
        
        config = OpenRouterProviderConfig(
            model="meta-llama/llama-3.1-8b-instruct",
            max_tokens=50,
            temperature=0.7
        )
        
        provider = OpenRouterProvider(config=config)
        
        # Test connection
        result = await provider.test_connection()
        
        if result.get("success"):
            log_result("OpenRouter Provider", True, f"Model: {result.get('model')}, Free: {result.get('is_free')}")
            await provider.close()
            return True
        else:
            log_result("OpenRouter Provider", False, result.get("error", "Unknown error"))
            await provider.close()
            return False
            
    except Exception as e:
        log_result("OpenRouter Provider", False, str(e))
        return False


async def test_database():
    """Test 2: Database (PostgreSQL/Prisma)"""
    print("\n" + "="*60)
    print("TEST 2: Database Integration (PostgreSQL/Prisma)")
    print("="*60)
    
    try:
        from config.database import get_db_session
        
        log_result("Database Import", True, "Database module imported")
        
        # Try to connect
        try:
            async with get_db_session() as session:
                result = await session.execute("SELECT 1 as test")
                row = result.fetchone()
                log_result("Database Connection", True, f"Query result: {row}")
                return True
        except Exception as e:
            log_result("Database Connection", False, str(e))
            return False
            
    except ImportError as e:
        log_result("Database Import", False, str(e))
        return False


async def test_redis():
    """Test 3: Redis Integration"""
    print("\n" + "="*60)
    print("TEST 3: Redis Integration")
    print("="*60)
    
    try:
        from config.redis import get_redis_client
        
        log_result("Redis Import", True, "Redis module imported")
        
        try:
            client = await get_redis_client()
            
            # Test SET
            await client.set("test_key", "test_value")
            log_result("Redis SET", True, "Set test_key = test_value")
            
            # Test GET
            value = await client.get("test_key")
            if value == "test_value":
                log_result("Redis GET", True, f"Retrieved: {value}")
            else:
                log_result("Redis GET", False, f"Expected 'test_value', got {value}")
            
            # Test DELETE
            await client.delete("test_key")
            log_result("Redis DELETE", True, "Key deleted")
            
            return True
            
        except Exception as e:
            log_result("Redis Connection", False, str(e))
            return False
            
    except ImportError as e:
        log_result("Redis Import", False, str(e))
        return False


async def test_qdrant():
    """Test 4: Qdrant Vector Database"""
    print("\n" + "="*60)
    print("TEST 4: Qdrant Vector Database Integration")
    print("="*60)
    
    try:
        from infra.vector.qdrant_store import QdrantVectorStore
        
        log_result("Qdrant Import", True, "Qdrant module imported")
        
        try:
            store = QdrantVectorStore()
            
            # Test health check
            health = await store.health_check()
            log_result("Qdrant Health", health.get("status") == "ok", health.get("message", str(health)))
            
            return health.get("status") == "ok"
            
        except Exception as e:
            log_result("Qdrant Connection", False, str(e))
            return False
            
    except ImportError as e:
        log_result("Qdrant Import", False, str(e))
        return False


async def test_milvus():
    """Test 4b: Milvus Vector Database (Alternative)"""
    print("\n--- Testing Milvus Vector Store ---")
    
    try:
        from infra.vector.milvus_store import MilvusVectorStore
        
        log_result("Milvus Import", True, "Milvus module imported")
        
        try:
            store = MilvusVectorStore()
            log_result("Milvus Connection", True, "Milvus store initialized")
            return True
        except Exception as e:
            log_result("Milvus Connection", False, str(e))
            return False
            
    except ImportError as e:
        log_result("Milvus Import", False, str(e))
        return False


async def test_fastapi_routes():
    """Test 5: FastAPI Routes"""
    print("\n" + "="*60)
    print("TEST 5: FastAPI Routes")
    print("="*60)
    
    try:
        # Import all route modules
        routes_imported = []
        routes_failed = []
        
        route_modules = [
            "api.agent_routes",
            "api.chat_routes",
            "api.auth_routes",
            "api.tool_routes",
            "api.mcp_server_routes",
            "api.nexus_routes",
            "api.a2a_routes",
        ]
        
        for module in route_modules:
            try:
                __import__(module, fromlist=[''])
                routes_imported.append(module)
            except ImportError as e:
                routes_failed.append((module, str(e)))
        
        if routes_imported:
            log_result("FastAPI Routes Import", True, f"Imported: {len(routes_imported)} modules")
        
        if routes_failed:
            for module, error in routes_failed:
                log_result(f"Route {module}", False, error)
        
        return len(routes_failed) == 0
        
    except Exception as e:
        log_result("FastAPI Routes", False, str(e))
        return False


async def test_mcp_servers():
    """Test 6: MCP Servers"""
    print("\n" + "="*60)
    print("TEST 6: MCP Servers")
    print("="*60)
    
    try:
        from mcp.servers.base_server import BaseMCPServer
        
        log_result("MCP Base Server Import", True, "BaseMCPServer imported")
        
        try:
            from mcp.servers.multi_agent_server import MultiAgentMCPServer
            log_result("MCP Multi-Agent Server", True, "MultiAgentMCPServer imported")
        except ImportError as e:
            log_result("MCP Multi-Agent Server", False, str(e))
        
        try:
            from mcp.registry.server_registry import MCPServerRegistry
            log_result("MCP Server Registry", True, "MCPServerRegistry imported")
        except ImportError as e:
            log_result("MCP Server Registry", False, str(e))
        
        return True
        
    except ImportError as e:
        log_result("MCP Servers Import", False, str(e))
        return False


async def test_ai_providers():
    """Test 7: AI Providers"""
    print("\n" + "="*60)
    print("TEST 7: AI Providers")
    print("="*60)
    
    providers_status = {}
    
    # Test OpenRouter Provider
    try:
        from ai_providers.providers.openrouter_provider import OpenRouterProvider
        providers_status["openrouter"] = "available"
        log_result("OpenRouter Provider", True, "Available")
    except ImportError as e:
        providers_status["openrouter"] = f"error: {e}"
        log_result("OpenRouter Provider", False, str(e))
    
    # Test OpenAI Provider
    try:
        from ai_providers.providers.openai_provider import OpenAIProvider
        providers_status["openai"] = "available"
        log_result("OpenAI Provider", True, "Available")
    except ImportError as e:
        providers_status["openai"] = f"error: {e}"
        log_result("OpenAI Provider", False, str(e))
    
    # Test Anthropic Provider
    try:
        from ai_providers.providers.anthropic_provider import AnthropicProvider
        providers_status["anthropic"] = "available"
        log_result("Anthropic Provider", True, "Available")
    except ImportError as e:
        providers_status["anthropic"] = f"error: {e}"
        log_result("Anthropic Provider", False, str(e))
    
    # Test Local Provider
    try:
        from ai_providers.providers.local_provider import LocalProvider
        providers_status["local"] = "available"
        log_result("Local Provider", True, "Available")
    except ImportError as e:
        providers_status["local"] = f"error: {e}"
        log_result("Local Provider", False, str(e))
    
    available_count = sum(1 for v in providers_status.values() if v == "available")
    log_result("AI Providers Summary", available_count > 0, f"{available_count}/4 providers available")
    
    return available_count > 0


async def test_blueprints():
    """Test 8: Blueprints"""
    print("\n" + "="*60)
    print("TEST 8: Blueprints")
    print("="*60)
    
    try:
        from blueprints.registry import BlueprintRegistry
        
        log_result("Blueprint Registry Import", True, "BlueprintRegistry imported")
        
        try:
            registry = BlueprintRegistry()
            blueprints = registry.list_blueprints()
            log_result("Blueprints List", True, f"Found {len(blueprints)} blueprints")
            return True
        except Exception as e:
            log_result("Blueprints Init", False, str(e))
            return False
            
    except ImportError as e:
        log_result("Blueprint Registry Import", False, str(e))
        return False


async def test_services():
    """Test 9: Core Services"""
    print("\n" + "="*60)
    print("TEST 9: Core Services")
    print("="*60)
    
    services = [
        ("services.agent_service", "AgentService"),
        ("services.auth_service", "AuthService"),
        ("services.session_service", "SessionService"),
        ("services.tool_service", "ToolService"),
        ("services.mcp_arsenal", "MCPArsenal"),
    ]
    
    imported = 0
    for module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            log_result(f"Service: {class_name}", True, "Available")
            imported += 1
        except (ImportError, AttributeError) as e:
            log_result(f"Service: {class_name}", False, str(e))
    
    log_result("Services Summary", imported > 0, f"{imported}/{len(services)} services available")
    return imported > 0


async def test_dag():
    """Test 10: DAG (Directed Acyclic Graph)"""
    print("\n" + "="*60)
    print("TEST 10: DAG Module")
    print("="*60)
    
    try:
        from dag import DAGNode, DAG
        
        log_result("DAG Import", True, "DAG module imported")
        return True
    except ImportError as e:
        log_result("DAG Import", False, str(e))
        return False


async def test_queue():
    """Test 11: Queue System"""
    print("\n" + "="*60)
    print("TEST 11: Queue System")
    print("="*60)
    
    try:
        from queue.redis_streams import RedisStreamsQueue
        log_result("Redis Streams Queue Import", True, "Available")
    except ImportError as e:
        log_result("Redis Streams Queue Import", False, str(e))
    
    try:
        from queue.event_dispatcher import EventDispatcher
        log_result("Event Dispatcher Import", True, "Available")
    except ImportError as e:
        log_result("Event Dispatcher Import", False, str(e))
    
    try:
        from queue.worker import QueueWorker
        log_result("Queue Worker Import", True, "Available")
        return True
    except ImportError as e:
        log_result("Queue Worker Import", False, str(e))
        return False


async def test_vector_store():
    """Test 12: Vector Store Core"""
    print("\n" + "="*60)
    print("TEST 12: Vector Store Core")
    print("="*60)
    
    try:
        from vector_store.core import VectorStore
        
        log_result("Vector Store Import", True, "VectorStore imported")
        return True
    except ImportError as e:
        log_result("Vector Store Import", False, str(e))
        return False


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "#"*60)
    print("# RICCO AI - INTEGRATION TEST SUITE")
    print(f"# Started: {datetime.now().isoformat()}")
    print("#"*60)
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("OpenRouter", test_openrouter),
        ("OpenRouter Provider", test_openrouter_provider),
        ("Database", test_database),
        ("Redis", test_redis),
        ("Qdrant", test_qdrant),
        ("Milvus", test_milvus),
        ("FastAPI Routes", test_fastapi_routes),
        ("MCP Servers", test_mcp_servers),
        ("AI Providers", test_ai_providers),
        ("Blueprints", test_blueprints),
        ("Services", test_services),
        ("DAG", test_dag),
        ("Queue", test_queue),
        ("Vector Store", test_vector_store),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = await test_func()
        except Exception as e:
            log_result(name, False, f"Exception: {e}")
            results[name] = False
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Duration: {duration:.2f} seconds")
    
    # Detailed results
    print("\n" + "-"*60)
    print("Detailed Results:")
    print("-"*60)
    
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    # Save results to file
    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100
        },
        "results": test_results
    }
    
    with open('/home/z/my-project/download/integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: /home/z/my-project/download/integration_test_report.json")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(run_all_tests())
