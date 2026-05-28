#!/usr/bin/env python3
"""
Comprehensive Blueprint Test Suite for RICCO AI
Tests all 19 NVIDIA AI Blueprints (7 core + 12 extended)
"""

import asyncio
import sys
import time
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, '/home/z/my-project/src')

from blueprints import (
    BlueprintRegistry,
    BlueprintConfig,
    BlueprintStatus,
    BlueprintType,
    # Core blueprints (7)
    AIQResearchBlueprint,
    RAGBlueprint,
    VideoSearchBlueprint,
    DataFlywheelBlueprint,
    DigitalHumanBlueprint,
    HealthcareBlueprint,
    RetailCommerceBlueprint,
    # Extended blueprints (12)
    AmbientPatientBlueprint,
    BiomedicalResearchBlueprint,
    FinancialDistillationBlueprint,
    GenomicsBlueprint,
    IndustrialBlueprint,
    IntelligentWarehouseBlueprint,
    MultiAgentBlueprint,
    PortfolioOptimizationBlueprint,
    RetailShoppingBlueprint,
    StreamingRAGBlueprint,
    VirtualAssistantBlueprint,
    VoiceAgentBlueprint,
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
                        "output": f"{len(blueprints)} blueprints discovered"
                    })
                else:
                    result["tests_failed"] += 1
                    result["details"].append({"test": "list_blueprints", "status": "FAILED"})
            except Exception as e:
                result["tests_failed"] += 1
                result["details"].append({"test": "list_blueprints", "status": "FAILED", "error": str(e)})
            
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
    
    async def test_blueprint_types(self) -> Dict[str, Any]:
        """Test BlueprintType enum"""
        self.log("Testing BlueprintType enum...")
        
        result = {
            "name": "BlueprintType",
            "status": "pending",
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Test all types exist
            expected_types = [
                "AIQ_RESEARCH", "RAG", "VIDEO_SEARCH", "DATA_FLYWHEEL",
                "DIGITAL_HUMAN", "HEALTHCARE", "RETAIL_COMMERCE",
                "AMBIENT_PATIENT", "BIOMEDICAL_RESEARCH", "FINANCIAL_DISTILLATION",
                "GENOMICS", "INDUSTRIAL", "INTELLIGENT_WAREHOUSE",
                "MULTI_AGENT", "PORTFOLIO_OPTIMIZATION", "RETAIL_SHOPPING",
                "STREAMING_RAG", "VIRTUAL_ASSISTANT", "VOICE_AGENT"
            ]
            
            for type_name in expected_types:
                if hasattr(BlueprintType, type_name):
                    result["tests_passed"] += 1
                    result["details"].append({"test": f"type_{type_name}", "status": "PASSED"})
                else:
                    result["tests_failed"] += 1
                    result["details"].append({"test": f"type_{type_name}", "status": "FAILED", "error": "Type not found"})
            
            result["status"] = "PASSED" if result["tests_failed"] == 0 else "FAILED"
            if result["status"] == "PASSED":
                self.passed += 1
            else:
                self.failed += 1
                
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            self.failed += 1
        
        result["execution_time"] = time.time() - start_time
        self.results.append(result)
        
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        self.log(f"{status_icon} BlueprintType: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']} types verified")
        
        return result
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 BLUEPRINT TEST SUMMARY - ALL 19 BLUEPRINTS")
        print("=" * 70)
        
        total_tests = sum(r["tests_passed"] + r["tests_failed"] for r in self.results)
        total_passed = sum(r["tests_passed"] for r in self.results)
        
        print(f"\nBlueprints Tested: {len(self.results)}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
        
        # Separate core and extended
        core_results = [r for r in self.results if r["name"] in [
            "AIQResearchBlueprint", "RAGBlueprint", "VideoSearchBlueprint",
            "DataFlywheelBlueprint", "DigitalHumanBlueprint", "HealthcareBlueprint",
            "RetailCommerceBlueprint", "BlueprintRegistry", "BlueprintType"
        ]]
        extended_results = [r for r in self.results if r not in core_results]
        
        print("\n" + "-" * 70)
        print("CORE BLUEPRINTS (7 + Registry + Types):")
        print("-" * 70)
        
        for result in core_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['name']}: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']} tests")
        
        print("\n" + "-" * 70)
        print("EXTENDED BLUEPRINTS (12):")
        print("-" * 70)
        
        for result in extended_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['name']}: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']} tests")
        
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
    print("🧪 RICCO AI - COMPLETE BLUEPRINT TEST SUITE")
    print("=" * 70)
    print(f"Testing all 19 NVIDIA AI Blueprints (7 core + 12 extended)\n")
    
    runner = BlueprintTestRunner()
    
    # Test Registry
    await runner.test_registry()
    
    # Test BlueprintType enum
    await runner.test_blueprint_types()
    
    # ========== CORE BLUEPRINTS (7) ==========
    
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
    
    # ========== EXTENDED BLUEPRINTS (12) ==========
    
    # Test Ambient Patient Blueprint
    await runner.test_blueprint(
        AmbientPatientBlueprint,
        "AmbientPatientBlueprint",
        {
            "action": "intake",
            "agent_type": "full",
            "patient_info": {"name": "John Doe", "age": 45}
        }
    )
    
    # Test Biomedical Research Blueprint
    await runner.test_blueprint(
        BiomedicalResearchBlueprint,
        "BiomedicalResearchBlueprint",
        {
            "query": "Latest advances in CRISPR gene editing for cancer treatment",
            "research_topic": "CRISPR oncology"
        }
    )
    
    # Test Financial Distillation Blueprint
    await runner.test_blueprint(
        FinancialDistillationBlueprint,
        "FinancialDistillationBlueprint",
        {
            "model_name": "risk-model-v2",
            "data_source": "market_data",
            "analysis_type": "risk_assessment"
        }
    )
    
    # Test Genomics Blueprint
    await runner.test_blueprint(
        GenomicsBlueprint,
        "GenomicsBlueprint",
        {
            "analysis_type": "variant_calling",
            "vcf_file": "sample.vcf",
            "reference_genome": "GRCh38"
        }
    )
    
    # Test Industrial Blueprint
    await runner.test_blueprint(
        IndustrialBlueprint,
        "IndustrialBlueprint",
        {
            "equipment_id": "pump-001",
            "operation_type": "predictive_maintenance",
            "sensor_data": {"vibration": 0.5, "temperature": 75}
        }
    )
    
    # Test Intelligent Warehouse Blueprint
    await runner.test_blueprint(
        IntelligentWarehouseBlueprint,
        "IntelligentWarehouseBlueprint",
        {
            "warehouse_id": "WH-001",
            "operation": "inventory_check",
            "sku": "SKU-12345"
        }
    )
    
    # Test Multi-Agent Blueprint
    await runner.test_blueprint(
        MultiAgentBlueprint,
        "MultiAgentBlueprint",
        {
            "task": "Analyze market trends and generate investment report",
            "pattern": "hierarchical",
            "agents": ["researcher", "analyst", "writer"]
        }
    )
    
    # Test Portfolio Optimization Blueprint
    await runner.test_blueprint(
        PortfolioOptimizationBlueprint,
        "PortfolioOptimizationBlueprint",
        {
            "optimization_target": "sharpe_ratio",
            "assets": ["AAPL", "GOOGL", "MSFT", "AMZN"],
            "risk_tolerance": "moderate"
        }
    )
    
    # Test Retail Shopping Blueprint
    await runner.test_blueprint(
        RetailShoppingBlueprint,
        "RetailShoppingBlueprint",
        {
            "user_id": "user-001",
            "search_query": "wireless headphones",
            "cart": ["item-1", "item-2"]
        }
    )
    
    # Test Streaming RAG Blueprint
    await runner.test_blueprint(
        StreamingRAGBlueprint,
        "StreamingRAGBlueprint",
        {
            "query": "Explain quantum computing in simple terms",
            "conversation_id": "conv-001",
            "stream": True
        }
    )
    
    # Test Virtual Assistant Blueprint
    await runner.test_blueprint(
        VirtualAssistantBlueprint,
        "VirtualAssistantBlueprint",
        {
            "command": "schedule_meeting",
            "task_type": "calendar",
            "query": "What's on my schedule today?"
        }
    )
    
    # Test Voice Agent Blueprint
    await runner.test_blueprint(
        VoiceAgentBlueprint,
        "VoiceAgentBlueprint",
        {
            "session_id": "voice-session-001",
            "audio": "audio_stream",
            "text": "Hello, how can I help?"
        }
    )
    
    # Print summary
    summary = runner.print_summary()
    
    return summary


if __name__ == "__main__":
    summary = asyncio.run(main())
    sys.exit(0 if summary["success_rate"] == 100 else 1)
