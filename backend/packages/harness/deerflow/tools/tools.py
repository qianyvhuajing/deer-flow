import importlib.util
import logging
import sys
from pathlib import Path

from langchain.tools import BaseTool

from deerflow.config import get_app_config
from deerflow.config.paths import get_paths
from deerflow.reflection import resolve_variable
from deerflow.tools.builtins import ask_clarification_tool, present_file_tool, task_tool, view_image_tool
from deerflow.tools.builtins.tool_search import reset_deferred_registry

logger = logging.getLogger(__name__)

BUILTIN_TOOLS = [
    present_file_tool,
    ask_clarification_tool,
]

SUBAGENT_TOOLS = [
    task_tool,
    # task_status_tool is no longer exposed to LLM (backend handles polling internally)
]

def load_agent_tools(agent_name: str | None) -> list[BaseTool]:
    """Load custom tools from an agent's tools.py file.

    Args:
        agent_name: The name of the agent.

    Returns:
        List of BaseTool objects loaded from the agent's tools.py file.
    """
    if not agent_name:
        return []

    try:
        agent_dir = get_paths().agent_dir(agent_name)
        tools_file = agent_dir / "tools.py"

        if not tools_file.exists():
            return []

        # Create a module spec from the file
        spec = importlib.util.spec_from_file_location(f"agent_tools_{agent_name}", str(tools_file))
        if not spec or not spec.loader:
            logger.warning(f"Failed to create module spec for {tools_file}")
            return []

        # Create a module from the spec
        module = importlib.util.module_from_spec(spec)
        
        # Add the module to sys.modules to avoid import issues
        module_name = f"agent_tools_{agent_name}"
        sys.modules[module_name] = module

        # Execute the module to load the tools
        spec.loader.exec_module(module)

        # Extract all BaseTool instances from the module
        tools = []
        for name, obj in module.__dict__.items():
            if isinstance(obj, BaseTool):
                tools.append(obj)

        logger.info(f"Loaded {len(tools)} custom tool(s) from {tools_file}")
        return tools

    except Exception as e:
        logger.warning(f"Failed to load agent tools for '{agent_name}': {e}")
        return []
    finally:
        # Clean up the temporary module from sys.modules
        module_name = f"agent_tools_{agent_name}"
        if module_name in sys.modules:
            del sys.modules[module_name]


def get_available_tools(
    groups: list[str] | None = None,
    include_mcp: bool = True,
    model_name: str | None = None,
    subagent_enabled: bool = False,
    agent_name: str | None = None,
) -> list[BaseTool]:
    """Get all available tools from config.

    Note: MCP tools should be initialized at application startup using
    `initialize_mcp_tools()` from deerflow.mcp module.

    Args:
        groups: Optional list of tool groups to filter by.
        include_mcp: Whether to include tools from MCP servers (default: True).
        model_name: Optional model name to determine if vision tools should be included.
        subagent_enabled: Whether to include subagent tools (task, task_status).
        agent_name: Optional agent name to load custom tools from tools.py.

    Returns:
        List of available tools.
    """
    config = get_app_config()
    loaded_tools = [resolve_variable(tool.use, BaseTool) for tool in config.tools if groups is None or tool.group in groups]

    # Conditionally add tools based on config
    builtin_tools = BUILTIN_TOOLS.copy()

    # Add subagent tools only if enabled via runtime parameter
    if subagent_enabled:
        builtin_tools.extend(SUBAGENT_TOOLS)
        logger.info("Including subagent tools (task)")

    # If no model_name specified, use the first model (default)
    if model_name is None and config.models:
        model_name = config.models[0].name

    # Add view_image_tool only if the model supports vision
    model_config = config.get_model_config(model_name) if model_name else None
    if model_config is not None and model_config.supports_vision:
        builtin_tools.append(view_image_tool)
        logger.info(f"Including view_image_tool for model '{model_name}' (supports_vision=True)")

    # Get cached MCP tools if enabled
    # NOTE: We use ExtensionsConfig.from_file() instead of config.extensions
    # to always read the latest configuration from disk. This ensures that changes
    # made through the Gateway API (which runs in a separate process) are immediately
    # reflected when loading MCP tools.
    mcp_tools = []
    # Reset deferred registry upfront to prevent stale state from previous calls
    reset_deferred_registry()
    if include_mcp:
        try:
            from deerflow.config.extensions_config import ExtensionsConfig
            from deerflow.mcp.cache import get_cached_mcp_tools

            extensions_config = ExtensionsConfig.from_file()
            if extensions_config.get_enabled_mcp_servers():
                mcp_tools = get_cached_mcp_tools()
                if mcp_tools:
                    logger.info(f"Using {len(mcp_tools)} cached MCP tool(s)")

                    # When tool_search is enabled, register MCP tools in the
                    # deferred registry and add tool_search to builtin tools.
                    if config.tool_search.enabled:
                        from deerflow.tools.builtins.tool_search import DeferredToolRegistry, set_deferred_registry
                        from deerflow.tools.builtins.tool_search import tool_search as tool_search_tool

                        registry = DeferredToolRegistry()
                        for t in mcp_tools:
                            registry.register(t)
                        set_deferred_registry(registry)
                        builtin_tools.append(tool_search_tool)
                        logger.info(f"Tool search active: {len(mcp_tools)} tools deferred")
        except ImportError:
            logger.warning("MCP module not available. Install 'langchain-mcp-adapters' package to enable MCP tools.")
        except Exception as e:
            logger.error(f"Failed to get cached MCP tools: {e}")

    # Add invoke_acp_agent tool if any ACP agents are configured
    acp_tools: list[BaseTool] = []
    try:
        from deerflow.config.acp_config import get_acp_agents
        from deerflow.tools.builtins.invoke_acp_agent_tool import build_invoke_acp_agent_tool

        acp_agents = get_acp_agents()
        if acp_agents:
            acp_tools.append(build_invoke_acp_agent_tool(acp_agents))
            logger.info(f"Including invoke_acp_agent tool ({len(acp_agents)} agent(s): {list(acp_agents.keys())})")
    except Exception as e:
        logger.warning(f"Failed to load ACP tool: {e}")

    # Load custom agent tools if agent_name is provided
    agent_tools = load_agent_tools(agent_name)

    logger.info(f"Total tools loaded: {len(loaded_tools)}, built-in tools: {len(builtin_tools)}, MCP tools: {len(mcp_tools)}, ACP tools: {len(acp_tools)}, agent tools: {len(agent_tools)}")
    return loaded_tools + builtin_tools + mcp_tools + acp_tools + agent_tools
