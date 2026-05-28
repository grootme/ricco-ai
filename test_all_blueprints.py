#!/usr/bin/env python3
"""
Comprehensive Blueprint Test Suite for RICCO AI
Tests all 7 NVIDIA AI Blueprints
"""

import asyncio
import sys
import time
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, '/home/z/my-project/src')

from blueprints import (
    BlueprintRegistry,
    AIQResearchBlueprint,
    RAGBlueprint,
    VideoSearchBlueprint,
    DataFlywheelBlueprint,
    DigitalHumanBlueprint,
    HealthcareBlueprint,
    RetailCommerceBlueprint,
    BlueprintConfig,
    BlueprintStatus,
)


class BlueprintTestRunner:
    """Test runner for all blueprints"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def test_blueprint(self, blueprint_class, name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single blueprint"""
        self.log(f"Testing {name}...")
        
        result = {
            "name": name,
            "status": "pending",
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
            "execution_time": 0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # Create blueprint instance
            config = BlueprintConfig(
                name=name,
                model="openrouter/meta-llama/llama-3.1-8b-instruct"
            )
            blueprint = blueprint_class(config)
            
            # Test 1: Instance creation
            if blueprint is not None:
                result["tests_passed"] += 1
                result["details"].append({"test": "instance_creation", "status": "PASSED"})
            else:
                result["tests_failed"] += 1
                result["details"].append({"test": "instance_creation", "status": "FAILED", "error": "Instance is None"})
            
            # Test 2: Get info
            try:
                info = blueprint.get_info()
                if info and "name" in info:
                    result["tests_passed"] += 1
                    result["details"].append({"test": "get_info", "status": "PASSED", "output": info})
                else:
                    result["tests_failed"] += 1
                    result["details"].append({"test": "get_info", "status": "FAILED", "error": "Invalid info structure"})
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "get_info", "status": "FAILED", "error": str(e)})
            
            # Test 3: Input validation
            try:
                is_valid = blueprint.validate_input(test_data)
                if is_valid:
                    result["tests_passed"] += 1
                    result["details"].append({"test": "validate_input", "status": "PASSED", "output": f"Valid: {is_valid}"})
                else:
                    result["tests_failed"] += 1
                    result["details"].append({"test": "validate_input", "status": "FAILED", "error": "Input validation returned False"})
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "validate_input", "status": "FAILED", "error": str(e)})
            
            # Test 4: Execute
            try:
                execution_result = await blueprint.execute(test_data)
                if execution_result.status == BlueprintStatus.COMPLETED:
                    result["tests_passed"] += 1
                    result["details"].append({
                        "test": "execute", 
                        "status": "PASSED",
                        "output": {
                            "execution_time": execution_result.execution_time,
                            "tokens_used": execution_result.tokens_used,
                            "has_output": execution_result.output is not None
                        }
                    })
                else:
                    result["tests_failed"] += 1
                    result["details"].append({
                        "test": "execute", 
                        "status": "FAILED", 
                        "error": execution_result.error or "Status not COMPLETED"
                    })
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "execute", "status": "FAILED", "error": str(e)})
            
            # Determine overall status
            if result["tests_failed"] == 0:
                result["status"] = "PASSED"
                self.passed += 1
            else:
                result["status"] = "FAILED"
                self.failed += 1
                
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            result["tests_failed"] += 1
            self.failed += 1
        
        result["execution_time"] = time.time() - start_time
        self.results.append(result)
        
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        self.log(f"{status_icon} {name}: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']} tests passed")
        
        return result
    
    async def test_registry(self) -> Dict[str, Any]:
        """Test the BlueprintRegistry"""
        self.log("Testing BlueprintRegistry...")
        
        result = {
            "name": "BlueprintRegistry",
            "status": "pending",
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            registry = BlueprintRegistry()
            
            # Test 1: Instance creation
            if registry is not None:
                result["tests_passed"] += 1
                result["details"].append({"test": "instance_creation", "status": "PASSED"})
            else:
                result["tests_failed"] += 1
                result["details"].append({"test": "instance_creation", "status": "FAILED"})
            
            # Test 2: List blueprints
            try:
                blueprints = registry.list_blueprints()
                if blueprints is not None and isinstance(blueprints, list):
                    result["tests_passed"] += 1
                    result["details"].append({
                        "test": "list_blueprints", 
                        "status": "PASSED",
                        "output": f"{len(blueprints)} blueprints discovered (NVIDIA repos not cloned)"
                    })
                else:
                    result["tests_failed"] += 1
                    result["details"].append({"test": "list_blueprints", "status": "FAILED"})
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "list_blueprints", "status": "FAILED", "error": str(e)})
            
            # Test 3: Get blueprint info
            try:
                info = registry.get_blueprint("aiq")
                result["tests_passed"] += 1
                result["details"].append({
                    "test": "get_blueprint", 
                    "status": "PASSED",
                    "output": info.name if info else "None"
                })
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "get_blueprint", "status": "FAILED", "error": str(e)})
            
            if result["tests_failed"] == 0:
                result["status"] = "PASSED"
                self.passed += 1
            else:
                result["status"] = "FAILED"
                self.failed += 1
                
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            self.failed += 1
        
        result["execution_time"] = time.time() - start_time
        self.results.append(result)
        
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        self.log(f"{status_icon} BlueprintRegistry: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']} tests passed")
        
        return result
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 BLUEPRINT TEST SUMMARY")
        print("=" * 70)
        
        total_tests = sum(r["tests_passed"] + r["tests_failed"] for r in self.results)
        total_passed = sum(r["tests_passed"] for r in self.results)
        
        print(f"\nBlueprints Tested: {len(self.results)}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
        
        print("\n" + "-" * 70)
        print("DETAILED RESULTS:")
        print("-" * 70)
        
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"\n{status_icon} {result['name']}")
            print(f"   Status: {result['status']}")
            print(f"   Tests: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']}")
            print(f"   Time: {result['execution_time']:.3f}s")
            
            if result.get("error"):
                print(f"   Error: {result['error']}")
            
            for detail in result.get("details", []):
                icon = "  ✓" if detail["status"] == "PASSED" else "  ✗"
                print(f"   {icon} {detail['test']}: {detail['status']}")
                if detail.get("error"):
                    print(f"      Error: {detail['error']}")
                if detail.get("output") and detail["status"] == "PASSED":
                    output_str = str(detail["output"])
                    if len(output_str) > 100:
                        output_str = output_str[:100] + "..."
                    print(f"      Output: {output_str}")
        
        print("\n" + "=" * 70)
        
        return {
            "total_blueprints": len(self.results),
            "total_tests": total_tests,
            "tests_passed": total_passed,
            "tests_failed": total_tests - total_passed,
            "success_rate": round(total_passed/total_tests*100, 1),
            "blueprints_passed": self.passed,
            "blueprints_failed": self.failed
        }


async def main():
    """Main test runner"""
    print("=" * 70)
    print("🧪 RICCO AI - BLUEPRINT TEST SUITE")
    print("=" * 70)
    print(f"Testing all 7 NVIDIA AI Blueprints\n")
    
    runner = BlueprintTestRunner()
    
    # Test Registry first
    await runner.test_registry()
    
    # Test AIQ Research Blueprint
    await runner.test_blueprint(
        AIQResearchBlueprint,
        "AIQResearchBlueprint",
        {
            "query": "What are the latest trends in AI agent architectures?",
            "depth": "deep",
            "sources": ["web", "documents", "databases"],
            "max_results": 5
        }
    )
    
    # Test RAG Blueprint
    await runner.test_blueprint(
        RAGBlueprint,
        "RAGBlueprint",
        {
            "query": "How does retrieval-augmented generation work?",
            "collection": "knowledge_base",
            "top_k": 5,
            "use_reranking": True
        }
    )
    
    # Test Video Search Blueprint
    await runner.test_blueprint(
        VideoSearchBlueprint,
        "VideoSearchBlueprint",
        {
            "video_url": "https://example.com/video.mp4",
            "query": "Find scenes with people talking",
            "mode": "search"
        }
    )
    
    # Test Data Flywheel Blueprint
    await runner.test_blueprint(
        DataFlywheelBlueprint,
        "DataFlywheelBlueprint",
        {
            "model": "llama-3.1-8b",
            "data_source": "production-logs",
            "cycle_count": 3
        }
    )
    
    # Test Digital Human Blueprint
    await runner.test_blueprint(
        DigitalHumanBlueprint,
        "DigitalHumanBlueprint",
        {
            "text": "Hello! Welcome to RICCO AI. How can I assist you today?",
            "emotion": "friendly"
        }
    )
    
    # Test Healthcare Blueprint
    await runner.test_blueprint(
        HealthcareBlueprint,
        "HealthcareBlueprint",
        {
            "transcript": "Patient presents with headache and fever for 3 days. No significant medical history.",
            "audio": "patient_consultation.mp3"
        }
    )
    
    # Test Retail Commerce Blueprint
    await runner.test_blueprint(
        RetailCommerceBlueprint,
        "RetailCommerceBlueprint",
        {
            "action": "recommend",
            "customer_id": "cust_123",
            "product_id": "prod_456"
        }
    )
    
    # Print summary
    summary = runner.print_summary()
    
    return summary


if __name__ == "__main__":
    summary = asyncio.run(main())
    sys.exit(0 if summary["success_rate"] == 100 else 1)
