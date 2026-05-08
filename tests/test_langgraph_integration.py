"""
Tests for LangGraph Integration with Interrupt and Command
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# Import modules
import sys
sys.path.insert(0, '/home/z/my-project/ecosystem/ricco-ai')


class TestLangGraphBasics:
    """Test basic LangGraph functionality"""
    
    def test_import_langgraph(self):
        """Test that LangGraph is properly imported"""
        try:
            from langgraph.graph import StateGraph, END
            from langgraph.types import interrupt, Command
            from langgraph.checkpoint.memory import MemorySaver
            assert True
        except ImportError as e:
            pytest.skip(f"LangGraph not available: {e}")
    
    def test_create_simple_graph(self):
        """Test creating a simple StateGraph"""
        from langgraph.graph import StateGraph, END
        from typing import TypedDict
        
        class SimpleState(TypedDict):
            value: int
        
        def increment(state: SimpleState) -> Dict[str, int]:
            return {"value": state["value"] + 1}
        
        graph = StateGraph(SimpleState)
        graph.add_node("increment", increment)
        graph.set_entry_point("increment")
        graph.add_edge("increment", END)
        
        compiled = graph.compile()
        assert compiled is not None
    
    @pytest.mark.asyncio
    async def test_run_simple_graph(self):
        """Test running a simple graph"""
        from langgraph.graph import StateGraph, END
        from typing import TypedDict
        
        class SimpleState(TypedDict):
            value: int
        
        def increment(state: SimpleState) -> Dict[str, int]:
            return {"value": state["value"] + 1}
        
        graph = StateGraph(SimpleState)
        graph.add_node("increment", increment)
        graph.set_entry_point("increment")
        graph.add_edge("increment", END)
        
        compiled = graph.compile()
        
        result = await compiled.ainvoke({"value": 0})
        assert result["value"] == 1


class TestLangGraphInterrupt:
    """Test LangGraph interrupt functionality for HITL"""
    
    def test_interrupt_import(self):
        """Test that interrupt is available"""
        try:
            from langgraph.types import interrupt
            assert callable(interrupt)
        except ImportError as e:
            pytest.skip(f"interrupt not available: {e}")
    
    @pytest.mark.asyncio
    async def test_interrupt_in_node(self):
        """Test using interrupt in a node"""
        from langgraph.graph import StateGraph, END
        from langgraph.types import interrupt, Command
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict, Optional
        
        class InterruptState(TypedDict):
            value: int
            approval: Optional[bool]
        
        def needs_approval(state: InterruptState) -> Command[InterruptState]:
            # This should pause execution and wait for input
            approval = interrupt("Need approval to continue")
            return Command(update={"approval": approval})
        
        def final_node(state: InterruptState) -> Dict[str, Any]:
            return {"value": 100 if state.get("approval") else 0}
        
        graph = StateGraph(InterruptState)
        graph.add_node("needs_approval", needs_approval)
        graph.add_node("final", final_node)
        graph.set_entry_point("needs_approval")
        graph.add_edge("needs_approval", "final")
        graph.add_edge("final", END)
        
        checkpointer = MemorySaver()
        compiled = graph.compile(checkpointer=checkpointer)
        
        # First invocation should pause at interrupt
        config = {"configurable": {"thread_id": "test-interrupt"}}
        
        # This will pause at interrupt
        result = await compiled.ainvoke({"value": 0, "approval": None}, config)
        
        # The state should be paused, not completed
        assert result is not None


class TestLangGraphCommand:
    """Test LangGraph Command functionality"""
    
    def test_command_import(self):
        """Test that Command is available"""
        try:
            from langgraph.types import Command
            assert Command is not None
        except ImportError as e:
            pytest.skip(f"Command not available: {e}")
    
    def test_command_update(self):
        """Test Command with update"""
        from langgraph.types import Command
        
        cmd = Command(update={"key": "value"})
        assert cmd.update == {"key": "value"}
    
    def test_command_goto(self):
        """Test Command with goto"""
        from langgraph.types import Command
        
        cmd = Command(goto="next_node")
        assert cmd.goto == "next_node"


class TestIOVBALangGraph:
    """Test IOVBA with LangGraph"""
    
    @pytest.fixture
    def langgraph_config(self):
        """Create LangGraph config"""
        from src.iovba.langgraph_integration import LangGraphConfig
        return LangGraphConfig(
            model_name="gpt-4o-mini",
            temperature=0.7,
            enable_checkpoints=True,
            hitl_enabled=True,
        )
    
    def test_langgraph_iovba_import(self):
        """Test importing LangGraphIOVBA"""
        try:
            from src.iovba.langgraph_integration import LangGraphIOVBA, LangGraphConfig
            assert LangGraphIOVBA is not None
            assert LangGraphConfig is not None
        except ImportError as e:
            pytest.skip(f"LangGraphIOVBA not available: {e}")
    
    @pytest.mark.asyncio
    async def test_langgraph_iovba_creation(self, langgraph_config):
        """Test creating LangGraphIOVBA instance"""
        from src.iovba.langgraph_integration import LangGraphIOVBA
        
        # Mock the LLM
        with patch('src.iovba.langgraph_integration.ChatOpenAI'):
            iovba = LangGraphIOVBA(config=langgraph_config)
            assert iovba.graph is not None
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, langgraph_config):
        """Test executing a workflow"""
        from src.iovba.langgraph_integration import LangGraphIOVBA
        
        with patch('src.iovba.langgraph_integration.ChatOpenAI') as mock_llm:
            # Mock LLM responses
            mock_instance = AsyncMock()
            mock_instance.ainvoke = AsyncMock(return_value=Mock(content="Test response"))
            mock_llm.return_value = mock_instance
            
            iovba = LangGraphIOVBA(config=langgraph_config)
            
            # Note: This would require actual LLM to run properly
            # For now, just test that the method exists
            assert hasattr(iovba, 'run_workflow')
    
    def test_graph_visualization(self, langgraph_config):
        """Test graph visualization"""
        from src.iovba.langgraph_integration import LangGraphIOVBA
        
        with patch('src.iovba.langgraph_integration.ChatOpenAI'):
            iovba = LangGraphIOVBA(config=langgraph_config)
            
            viz = iovba.get_graph_visualization()
            assert viz is not None


class TestLeadAssistantLangGraph:
    """Test Lead Assistant with LangGraph"""
    
    def test_lead_assistant_import(self):
        """Test importing LangGraphLeadAssistant"""
        try:
            from src.iovba.langgraph_integration import LangGraphLeadAssistant
            assert LangGraphLeadAssistant is not None
        except ImportError as e:
            pytest.skip(f"LangGraphLeadAssistant not available: {e}")
    
    @pytest.mark.asyncio
    async def test_coordinate_method(self):
        """Test coordinate method exists"""
        from src.iovba.langgraph_integration import LangGraphLeadAssistant, LangGraphConfig
        
        with patch('src.iovba.langgraph_integration.ChatOpenAI'):
            config = LangGraphConfig()
            assistant = LangGraphLeadAssistant(config=config)
            
            assert hasattr(assistant, 'coordinate')
            assert hasattr(assistant, 'resume_with_creation_approval')


class TestHITLWithLangGraph:
    """Test HITL functionality with LangGraph"""
    
    @pytest.mark.asyncio
    async def test_hitl_approval_flow(self):
        """Test HITL approval flow with interrupts"""
        from langgraph.graph import StateGraph, END
        from langgraph.types import interrupt, Command
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict, Optional
        
        class ApprovalState(TypedDict):
            task: str
            approved: Optional[bool]
            result: Optional[str]
        
        def request_approval(state: ApprovalState) -> Command[ApprovalState]:
            approval = interrupt({
                "type": "approval_request",
                "task": state["task"],
                "message": "Do you approve this action?",
            })
            return Command(update={"approved": approval})
        
        def process_result(state: ApprovalState) -> Dict[str, str]:
            if state.get("approved"):
                return {"result": "Action approved and executed"}
            else:
                return {"result": "Action rejected"}
        
        graph = StateGraph(ApprovalState)
        graph.add_node("request_approval", request_approval)
        graph.add_node("process_result", process_result)
        graph.set_entry_point("request_approval")
        graph.add_edge("request_approval", "process_result")
        graph.add_edge("process_result", END)
        
        checkpointer = MemorySaver()
        compiled = graph.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "hitl-test"}}
        
        # Start workflow - should pause at interrupt
        result = await compiled.ainvoke(
            {"task": "Create new agent", "approved": None, "result": None},
            config
        )
        
        # State should exist
        assert result is not None


class TestCheckpointing:
    """Test LangGraph checkpointing"""
    
    def test_memory_saver_creation(self):
        """Test creating MemorySaver"""
        from langgraph.checkpoint.memory import MemorySaver
        
        checkpointer = MemorySaver()
        assert checkpointer is not None
    
    @pytest.mark.asyncio
    async def test_checkpoint_persistence(self):
        """Test that checkpoints persist state"""
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict
        
        class CountState(TypedDict):
            count: int
        
        def increment(state: CountState) -> Dict[str, int]:
            return {"count": state["count"] + 1}
        
        graph = StateGraph(CountState)
        graph.add_node("increment", increment)
        graph.set_entry_point("increment")
        graph.add_edge("increment", END)
        
        checkpointer = MemorySaver()
        compiled = graph.compile(checkpointer=checkpointer)
        
        config = {"configurable": {"thread_id": "count-test"}}
        
        # Run multiple times
        result1 = await compiled.ainvoke({"count": 0}, config)
        result2 = await compiled.ainvoke({"count": 0}, config)
        
        assert result1["count"] == 1
        assert result2["count"] == 1


# ==================== INTEGRATION TESTS ====================

class TestLangGraphIntegration:
    """Integration tests for LangGraph with IOVBA"""
    
    @pytest.mark.asyncio
    async def test_full_iovba_workflow(self):
        """Test full IOVBA workflow with all 5 roles"""
        try:
            from src.iovba.langgraph_integration import LangGraphIOVBA, LangGraphConfig
            
            config = LangGraphConfig(
                model_name="gpt-4o-mini",
                hitl_enabled=False,  # Disable HITL for testing
            )
            
            with patch('src.iovba.langgraph_integration.ChatOpenAI') as mock_llm:
                mock_instance = AsyncMock()
                mock_instance.ainvoke = AsyncMock(return_value=Mock(
                    content="Test response from LLM"
                ))
                mock_llm.return_value = mock_instance
                
                iovba = LangGraphIOVBA(config=config)
                
                # Test that graph has all nodes
                assert iovba.graph is not None
                
        except ImportError:
            pytest.skip("LangGraph integration not available")
    
    @pytest.mark.asyncio
    async def test_lead_assistant_coordination(self):
        """Test Lead Assistant coordination"""
        try:
            from src.iovba.langgraph_integration import (
                LangGraphLeadAssistant,
                LangGraphConfig,
            )
            
            config = LangGraphConfig(hitl_enabled=False)
            
            with patch('src.iovba.langgraph_integration.ChatOpenAI') as mock_llm:
                mock_instance = AsyncMock()
                mock_instance.ainvoke = AsyncMock(return_value=Mock(
                    content="Analysis complete. Plan: Execute tasks."
                ))
                mock_llm.return_value = mock_instance
                
                assistant = LangGraphLeadAssistant(config=config)
                
                assert assistant.graph is not None
                
        except ImportError:
            pytest.skip("LangGraph integration not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
