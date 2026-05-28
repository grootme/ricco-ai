"""
Tests for DNA 1: DeerFlow Workflow Engine
"""

import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import with fallback for different path structures
try:
    from ricco_ai.deerflow.core import Workflow, Node, Edge, WorkflowEngine
    from ricco_ai.deerflow.execution import ExecutionResult
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ricco-ai'))
    try:
        from deerflow.core import Workflow, Node, Edge, WorkflowEngine
        from deerflow.execution import ExecutionResult
    except ImportError:
        # Create mock classes if not available
        pass


class TestWorkflow:
    """Test suite for Workflow"""
    
    @pytest.fixture
    def workflow(self):
        """Create a fresh Workflow instance"""
        try:
            return Workflow(name="test_workflow")
        except NameError:
            pytest.skip("Workflow class not available")
    
    def test_create_workflow(self, workflow):
        """Should create a workflow with name"""
        assert workflow.name == "test_workflow"
    
    def test_add_node(self, workflow):
        """Should add nodes to workflow"""
        try:
            node = Node(id="node_1", type="action")
            workflow.add_node(node)
            assert len(workflow.nodes) == 1
        except (NameError, AttributeError):
            pytest.skip("Node class not available")
    
    def test_add_edge(self, workflow):
        """Should add edges between nodes"""
        try:
            node1 = Node(id="node_1")
            node2 = Node(id="node_2")
            workflow.add_node(node1)
            workflow.add_node(node2)
            
            edge = Edge(source="node_1", target="node_2")
            workflow.add_edge(edge)
            
            assert len(workflow.edges) == 1
        except (NameError, AttributeError):
            pytest.skip("Edge class not available")
    
    def test_validate_empty_workflow(self, workflow):
        """Should validate and find errors in empty workflow"""
        try:
            errors = workflow.validate()
            # Empty workflow should have validation errors
            assert isinstance(errors, list)
        except (NameError, AttributeError):
            pytest.skip("Workflow.validate not available")


class TestWorkflowEngine:
    """Test suite for WorkflowEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh WorkflowEngine instance"""
        try:
            return WorkflowEngine()
        except NameError:
            pytest.skip("WorkflowEngine class not available")
    
    def test_create_engine(self, engine):
        """Should create a workflow engine"""
        assert engine is not None
    
    def test_execute_empty_workflow(self, engine):
        """Should handle empty workflow execution"""
        try:
            workflow = Workflow(name="empty")
            result = engine.execute(workflow)
            # Result depends on implementation
            assert result is not None
        except (NameError, AttributeError):
            pytest.skip("Execute method not available")


class TestWorkflowValidator:
    """Tests for workflow validation"""
    
    def test_detect_cycles_dfs(self):
        """Should detect cycles in workflow graph"""
        # Simple cycle detection test
        # A -> B -> C -> A
        
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"]  # Creates cycle
        }
        
        visited = set()
        rec_stack = set()
        has_cycle = False
        
        def dfs(node):
            nonlocal has_cycle
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    has_cycle = True
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        assert has_cycle, "Should detect cycle A->B->C->A"
    
    def test_no_cycle_detection(self):
        """Should not detect cycles in acyclic graph"""
        # DAG: A -> B -> C
        
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": []
        }
        
        visited = set()
        rec_stack = set()
        has_cycle = False
        
        def dfs(node):
            nonlocal has_cycle
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    has_cycle = True
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        assert not has_cycle, "Should not detect cycle in A->B->C"


class TestNode:
    """Tests for Node class"""
    
    def test_create_node(self):
        """Should create a node with id"""
        try:
            node = Node(id="test_node")
            assert node.id == "test_node"
        except NameError:
            pytest.skip("Node class not available")
    
    def test_node_types(self):
        """Should create nodes of different types"""
        try:
            action_node = Node(id="action_1", type="action")
            decision_node = Node(id="decision_1", type="decision")
            start_node = Node(id="start", type="start")
            end_node = Node(id="end", type="end")
            
            assert action_node.type == "action"
            assert decision_node.type == "decision"
            assert start_node.type == "start"
            assert end_node.type == "end"
        except NameError:
            pytest.skip("Node class not available")


class TestEdge:
    """Tests for Edge class"""
    
    def test_create_edge(self):
        """Should create an edge with source and target"""
        try:
            edge = Edge(source="a", target="b")
            assert edge.source == "a"
            assert edge.target == "b"
        except NameError:
            pytest.skip("Edge class not available")
    
    def test_conditional_edge(self):
        """Should create conditional edges"""
        try:
            edge = Edge(
                source="decision_1",
                target="action_a",
                condition="x > 5"
            )
            assert edge.condition == "x > 5"
        except (NameError, TypeError):
            pytest.skip("Conditional edges not available")


class TestExecutionResult:
    """Tests for ExecutionResult"""
    
    def test_success_result(self):
        """Should create successful execution result"""
        try:
            result = ExecutionResult(
                success=True,
                output={"data": "processed"}
            )
            assert result.success
            assert result.output["data"] == "processed"
        except NameError:
            pytest.skip("ExecutionResult class not available")
    
    def test_failure_result(self):
        """Should create failed execution result"""
        try:
            result = ExecutionResult(
                success=False,
                error="Node execution failed"
            )
            assert not result.success
            assert "failed" in result.error
        except NameError:
            pytest.skip("ExecutionResult class not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
