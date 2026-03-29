#!/usr/bin/env python3
"""
Test script for setup_agent tool with extra parameter support.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from deerflow.tools.builtins.setup_agent_tool import setup_agent
from langgraph.prebuilt import ToolRuntime


def test_setup_agent_without_extra():
    """Test setup_agent without extra parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock runtime
        mock_runtime = Mock(spec=ToolRuntime)
        mock_runtime.context = {"agent_name": "test-agent"}
        mock_runtime.tool_call_id = "test-call-id"
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.builtins.setup_agent_tool.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = Path(tmpdir) / "agents" / "test-agent"
            mock_get_paths.return_value = mock_paths
            
            # Call setup_agent
            result = setup_agent(
                soul="You are a test agent.",
                description="Test agent",
                runtime=mock_runtime
            )
            
            # Check that the result is a Command object
            assert hasattr(result, 'update')
            assert 'created_agent_name' in result.update
            assert result.update['created_agent_name'] == 'test-agent'
            
            # Check that SOUL.md was created
            agent_dir = Path(tmpdir) / "agents" / "test-agent"
            soul_file = agent_dir / "SOUL.md"
            assert soul_file.exists()
            assert soul_file.read_text() == "You are a test agent."
            
            # Check that tools.py was NOT created
            tools_file = agent_dir / "tools.py"
            assert not tools_file.exists()


def test_setup_agent_with_script():
    """Test setup_agent with script parameter."""
    test_script = """
from langchain_core.tools import tool

@tool
def hello(name: str) -> str:
    '''Say hello to someone.'''
    return f"Hello, {name}!"
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock runtime
        mock_runtime = Mock(spec=ToolRuntime)
        mock_runtime.context = {"agent_name": "test-agent-with-tools"}
        mock_runtime.tool_call_id = "test-call-id-2"
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.builtins.setup_agent_tool.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = Path(tmpdir) / "agents" / "test-agent-with-tools"
            mock_get_paths.return_value = mock_paths
            
            # Call setup_agent with extra parameter
            result = setup_agent(
                soul="You are a test agent with tools.",
                description="Test agent with tools",
                extra={"script": test_script},
                runtime=mock_runtime
            )
            
            # Check that the result is a Command object
            assert hasattr(result, 'update')
            assert 'created_agent_name' in result.update
            assert result.update['created_agent_name'] == 'test-agent-with-tools'
            
            # Check that SOUL.md was created
            agent_dir = Path(tmpdir) / "agents" / "test-agent-with-tools"
            soul_file = agent_dir / "SOUL.md"
            assert soul_file.exists()
            assert soul_file.read_text() == "You are a test agent with tools."
            
            # Check that tools.py was created with the correct content
            tools_file = agent_dir / "tools.py"
            assert tools_file.exists()
            assert tools_file.read_text() == test_script


def test_setup_agent_with_extra_other_keys():
    """Test setup_agent with extra parameter containing other keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock runtime
        mock_runtime = Mock(spec=ToolRuntime)
        mock_runtime.context = {"agent_name": "test-agent-other"}
        mock_runtime.tool_call_id = "test-call-id-3"
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.builtins.setup_agent_tool.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = Path(tmpdir) / "agents" / "test-agent-other"
            mock_get_paths.return_value = mock_paths
            
            # Call setup_agent with extra parameter containing other keys
            result = setup_agent(
                soul="You are a test agent with other extra keys.",
                description="Test agent with other extra keys",
                extra={"key1": "value1", "key2": "value2"},
                runtime=mock_runtime
            )
            
            # Check that the result is a Command object
            assert hasattr(result, 'update')
            assert 'created_agent_name' in result.update
            assert result.update['created_agent_name'] == 'test-agent-other'
            
            # Check that SOUL.md was created
            agent_dir = Path(tmpdir) / "agents" / "test-agent-other"
            soul_file = agent_dir / "SOUL.md"
            assert soul_file.exists()
            assert soul_file.read_text() == "You are a test agent with other extra keys."
            
            # Check that tools.py was NOT created
            tools_file = agent_dir / "tools.py"
            assert not tools_file.exists()


if __name__ == "__main__":
    print("Testing setup_agent without extra parameter...")
    test_setup_agent_without_extra()
    print("✓ Passed")
    
    print("\nTesting setup_agent with script parameter...")
    test_setup_agent_with_script()
    print("✓ Passed")
    
    print("\nTesting setup_agent with extra parameter containing other keys...")
    test_setup_agent_with_extra_other_keys()
    print("✓ Passed")
    
    print("\nAll tests passed!")
