"""
Aetios Agent Package

Provides the AI medical tutor agent with tool calling capabilities,
prompt management, and orchestration for personalized learning.
"""
from .orchestrator import AgentOrchestrator, create_agent
from .tools import (
    TOOL_DEFINITIONS,
    TOOL_FUNCTIONS,
    execute_tool,
)
from .prompts import (
    PromptManager,
    get_prompt_manager,
    get_system_prompt,
    get_quiz_generation_prompt,
    get_study_plan_prompt,
)

__all__ = [
    # Orchestrator
    "AgentOrchestrator",
    "create_agent",
    # Tools
    "TOOL_DEFINITIONS",
    "TOOL_FUNCTIONS",
    "execute_tool",
    # Prompts
    "PromptManager",
    "get_prompt_manager",
    "get_system_prompt",
    "get_quiz_generation_prompt",
    "get_study_plan_prompt",
]
