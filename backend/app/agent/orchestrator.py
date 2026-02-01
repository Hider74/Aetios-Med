"""
Agent orchestrator for Aetios medical tutor.
Handles the main agent loop with tool calling and response generation.
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import json
import logging
from datetime import datetime

from .tools import TOOL_DEFINITIONS, execute_tool
from .prompts import get_system_prompt

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the Aetios agent with tool calling capabilities.
    Manages conversation flow, tool execution, and response generation.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        max_iterations: int = 10,
        temperature: float = 0.7
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Model to use for generation
            max_iterations: Maximum tool calling iterations
            temperature: Generation temperature
        """
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.api_key = api_key
        
        # Initialize conversation history
        self.messages: List[Dict[str, Any]] = []
        self._initialize_system_prompt()
    
    def _initialize_system_prompt(self):
        """Initialize the system prompt."""
        system_prompt = get_system_prompt()
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]
    
    def add_user_message(self, content: str):
        """
        Add a user message to the conversation.
        
        Args:
            content: User message content
        """
        self.messages.append({
            "role": "user",
            "content": content
        })
    
    def add_assistant_message(self, content: Optional[str] = None, tool_calls: Optional[List[Dict]] = None):
        """
        Add an assistant message to the conversation.
        
        Args:
            content: Assistant message content
            tool_calls: List of tool calls made by assistant
        """
        message = {"role": "assistant"}
        
        if content:
            message["content"] = content
        
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.messages.append(message)
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: Any):
        """
        Add a tool execution result to the conversation.
        
        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result
        """
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result)
        })
    
    async def _call_llm(self) -> Dict[str, Any]:
        """
        Call the LLM with current messages and tools.
        
        Returns:
            LLM response
        """
        # This would use the actual OpenAI API
        # For now, returning a mock response structure
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Mock response"
                },
                "finish_reason": "stop"
            }]
        }
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        """
        Execute a single tool call.
        
        Args:
            tool_call: Tool call specification
            
        Returns:
            Tool execution result
        """
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments_str = function.get("arguments", "{}")
        
        try:
            arguments = json.loads(arguments_str)
            result = execute_tool(tool_name, arguments)
            logger.info(f"Executed tool {tool_name} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def process_message(self, user_message: str) -> str:
        """
        Process a user message through the agent loop.
        
        Args:
            user_message: User's input message
            
        Returns:
            Final assistant response
        """
        self.add_user_message(user_message)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Call LLM
            response = await self._call_llm()
            choice = response["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason")
            
            # Check if assistant wants to call tools
            tool_calls = message.get("tool_calls")
            
            if tool_calls:
                # Add assistant message with tool calls
                self.add_assistant_message(
                    content=message.get("content"),
                    tool_calls=tool_calls
                )
                
                # Execute each tool call
                for tool_call in tool_calls:
                    tool_call_id = tool_call.get("id")
                    function_name = tool_call.get("function", {}).get("name")
                    
                    result = self._execute_tool_call(tool_call)
                    self.add_tool_result(tool_call_id, function_name, result)
                
                # Continue loop to get next response
                continue
            
            # No tool calls, we have final response
            content = message.get("content", "")
            self.add_assistant_message(content=content)
            return content
        
        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return "I apologize, but I need to break this down into smaller steps. Could you please rephrase your question?"
    
    async def stream_message(self, user_message: str) -> AsyncIterator[str]:
        """
        Process a user message with streaming response.
        
        Args:
            user_message: User's input message
            
        Yields:
            Response chunks as they're generated
        """
        self.add_user_message(user_message)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # In a real implementation, this would stream from OpenAI
            # For now, yielding the full response
            response = await self.process_message(user_message)
            yield response
            break
    
    def reset(self):
        """Reset the conversation, keeping only the system prompt."""
        self._initialize_system_prompt()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the full conversation history.
        
        Returns:
            List of all messages
        """
        return self.messages.copy()
    
    def export_conversation(self) -> str:
        """
        Export conversation to JSON string.
        
        Returns:
            JSON string of conversation
        """
        return json.dumps({
            "model": self.model,
            "timestamp": datetime.utcnow().isoformat(),
            "messages": self.messages
        }, indent=2)
    
    def load_conversation(self, conversation_json: str):
        """
        Load a conversation from JSON string.
        
        Args:
            conversation_json: JSON string of conversation
        """
        data = json.loads(conversation_json)
        self.messages = data.get("messages", [])
        self.model = data.get("model", self.model)


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""
    pass


def create_agent(
    api_key: Optional[str] = None,
    model: str = "gpt-4-turbo-preview",
    **kwargs
) -> AgentOrchestrator:
    """
    Factory function to create an agent orchestrator.
    
    Args:
        api_key: OpenAI API key
        model: Model to use
        **kwargs: Additional arguments for AgentOrchestrator
        
    Returns:
        Configured AgentOrchestrator instance
    """
    return AgentOrchestrator(api_key=api_key, model=model, **kwargs)
