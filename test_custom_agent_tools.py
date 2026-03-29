#!/usr/bin/env python3
"""
Test script for custom agent tools loading.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from deerflow.config.paths import get_paths
from deerflow.tools.tools import load_agent_tools, get_available_tools


def test_load_agent_tools_without_tools_py():
    """Test load_agent_tools when tools.py doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.tools.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = Path(tmpdir) / "agents" / "test-agent"
            mock_get_paths.return_value = mock_paths
            
            # Call load_agent_tools
            tools = load_agent_tools("test-agent")
            
            # Should return empty list
            assert len(tools) == 0


def test_load_agent_tools_with_valid_tools_py():
    """Test load_agent_tools with a valid tools.py file."""
    test_script = """
from langchain_core.tools import tool

@tool
def say_hello(name: str) -> str:
    '''Say hello to someone.'''
    return f"Hello, {name}!"

@tool
def calculate_sum(a: int, b: int) -> str:
    '''Calculate the sum of two numbers.'''
    return f"The sum is {a + b}"
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent directory and tools.py file
        agent_dir = Path(tmpdir) / "agents" / "test-agent"
        agent_dir.mkdir(parents=True)
        tools_file = agent_dir / "tools.py"
        tools_file.write_text(test_script)
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.tools.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = agent_dir
            mock_get_paths.return_value = mock_paths
            
            # Call load_agent_tools
            tools = load_agent_tools("test-agent")
            
            # Should return 2 tools
            assert len(tools) == 2
            tool_names = [tool.name for tool in tools]
            assert "say_hello" in tool_names
            assert "calculate_sum" in tool_names


def test_load_agent_tools_with_invalid_tools_py():
    """Test load_agent_tools with an invalid tools.py file."""
    invalid_script = """
from langchain_core.tools import tool

@tool
def say_hello(name: str) -> str:
    '''Say hello to someone.'''
    return f"Hello, {name}!"

# Syntax error here
invalid code
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent directory and tools.py file with syntax error
        agent_dir = Path(tmpdir) / "agents" / "test-agent"
        agent_dir.mkdir(parents=True)
        tools_file = agent_dir / "tools.py"
        tools_file.write_text(invalid_script)
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.tools.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = agent_dir
            mock_get_paths.return_value = mock_paths
            
            # Call load_agent_tools - should not raise exception
            tools = load_agent_tools("test-agent")
            
            # Should return empty list due to error
            assert len(tools) == 0


def test_get_available_tools_with_agent_name():
    """Test get_available_tools with agent_name parameter."""
    test_script = """
from langchain_core.tools import tool

@tool
def test_tool() -> str:
    '''Test tool.'''
    return "Test tool result"
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent directory and tools.py file
        agent_dir = Path(tmpdir) / "agents" / "test-agent"
        agent_dir.mkdir(parents=True)
        tools_file = agent_dir / "tools.py"
        tools_file.write_text(test_script)
        
        # Mock get_paths to return our temporary directory
        with patch('deerflow.tools.tools.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.agent_dir.return_value = agent_dir
            mock_get_paths.return_value = mock_paths
            
            # Mock get_app_config to return minimal config
            with patch('deerflow.tools.tools.get_app_config') as mock_get_app_config:
                mock_config = Mock()
                mock_config.tools = []
                mock_config.models = []
                mock_config.tool_search.enabled = False
                mock_get_app_config.return_value = mock_config
                
                # Call get_available_tools with agent_name
                tools = get_available_tools(agent_name="test-agent")
                
                # Should include the custom tool
                tool_names = [tool.name for tool in tools]
                assert "test_tool" in tool_names


def test_get_available_tools_without_agent_name():
    """Test get_available_tools without agent_name parameter."""
    # Mock get_app_config to return minimal config
    with patch('deerflow.tools.tools.get_app_config') as mock_get_app_config:
        mock_config = Mock()
        mock_config.tools = []
        mock_config.models = []
        mock_config.tool_search.enabled = False
        mock_get_app_config.return_value = mock_config
        
        # Call get_available_tools without agent_name
        tools = get_available_tools()
        
        # Should work normally (no custom tools)
        assert isinstance(tools, list)


if __name__ == "__main__":
    print("Testing load_agent_tools without tools.py...")
    test_load_agent_tools_without_tools_py()
    print("✓ Passed")
    
    print("\nTesting load_agent_tools with valid tools.py...")
    test_load_agent_tools_with_valid_tools_py()
    print("✓ Passed")
    
    print("\nTesting load_agent_tools with invalid tools.py...")
    test_load_agent_tools_with_invalid_tools_py()
    print("✓ Passed")
    
    print("\nTesting get_available_tools with agent_name...")
    test_get_available_tools_with_agent_name()
    print("✓ Passed")
    
    print("\nTesting get_available_tools without agent_name...")
    test_get_available_tools_without_agent_name()
    print("✓ Passed")
    
    print("\nAll tests passed!")
