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
        llm_service,
        model: str = "llama-3",
        max_iterations: int = 10,
        temperature: float = 0.7
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            llm_service: LLMService instance for local inference
            model: Model identifier
            max_iterations: Maximum tool calling iterations
            temperature: Generation temperature
        """
        self.llm_service = llm_service
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        
        # Initialize conversation history
        self.messages: List[Dict[str, Any]] = []
        self._initialize_system_prompt()
    
    def _initialize_system_prompt(self):
        """Initialize the system prompt for Q&A (no tool calling)."""
        system_prompt = get_system_prompt()
        # Tools are now accessed via UI, not LLM function calling
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
        Call the LLM with current messages for Q&A (no tool calling).
        
        Returns:
            LLM response in OpenAI-compatible format
        """
        if not self.llm_service.is_loaded:
            raise RuntimeError("LLM model not loaded. Call await llm_service.load_model() first.")
        
        # Call the local LLM with messages for Q&A only
        try:
            response_text = await self.llm_service.complete(
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=None,
                stop=["<|eot_id|>"]
            )
            
            # Parse response for tool calls
            tool_calls = self._parse_tool_calls(response_text)
            
            # Format response in OpenAI-compatible format
            if tool_calls:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": tool_calls
                        },
                        "finish_reason": "tool_calls"
                    }]
                }
            else:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }]
                }
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    def _format_tools_for_prompt(self, tool_names: Optional[List[str]] = None) -> str:
        """Format tool definitions for the system prompt in compact format.
        
        Args:
            tool_names: List of tool names to include. If None, includes all tools.
                       If empty list, includes no tools.
        """
        # If tool_names is explicitly an empty list, return empty string
        if tool_names is not None and len(tool_names) == 0:
            return ""
        
        # Filter tools if specific names provided
        tools_to_include = TOOL_DEFINITIONS
        if tool_names is not None:
            tools_to_include = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in tool_names]
        
        if not tools_to_include:
            return ""
        
        # Compact single-line format: tool_name(params) - brief description
        tools = []
        for tool in tools_to_include:
            func = tool["function"]
            name = func["name"]
            params = func.get("parameters", {}).get("properties", {})
            param_str = ', '.join(params.keys()) if params else ''
            # Extract first sentence only from description
            desc = func["description"].split('.')[0]
            tools.append(f"{name}({param_str}) - {desc}")
        
        tools_text = "\n\nAvailable tools: " + " | ".join(tools)
        tools_text += "\nUsage: TOOL_CALL: tool_name({\"arg\": \"value\"})"
        
        return tools_text
    
    def _parse_tool_calls(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse tool calls from model response.
        
        Expects tool calls in the format: TOOL_CALL: tool_name({"arg": "value"})
        Arguments must be valid JSON (double quotes required, as per JSON spec).
        Handles escape sequences (\n, \t, \", \\, etc.) correctly.
        
        Note: Malformed tool calls are logged as warnings and skipped. The agent
        will continue processing valid tool calls and may try again in the next
        iteration if the LLM detects the tool call was not executed.
        """
        tool_calls = []
        
        # Process line by line looking for TOOL_CALL: pattern
        for line in response_text.split('\n'):
            line = line.strip()
            if not line.startswith('TOOL_CALL:'):
                continue
            
            # Extract tool name and arguments
            try:
                # Remove TOOL_CALL: prefix
                call_str = line[len('TOOL_CALL:'):].strip()
                
                # Find tool name (before opening paren)
                paren_idx = call_str.find('(')
                if paren_idx == -1:
                    logger.warning(f"Invalid tool call format (no parentheses): {line}")
                    continue
                
                tool_name = call_str[:paren_idx].strip()
                
                # Extract JSON arguments (between parentheses)
                # Use JSON-aware parsing to handle nested structures and strings with special chars
                args_start = paren_idx + 1
                
                # Simple approach: find the JSON object/dict by looking for balanced braces
                # This works because our format requires JSON args wrapped in parens
                brace_count = 0
                in_string = False
                escape_next = False
                end_idx = -1
                
                for i in range(args_start, len(call_str)):
                    char = call_str[i]
                    
                    # Handle escape sequences in strings
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    # Track string boundaries
                    if char == '"':
                        in_string = not in_string
                        continue
                    
                    # Only count braces/parens outside of strings
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                        elif char == ')' and brace_count == 0:
                            # Found the closing paren for the function call
                            end_idx = i
                            break
                
                if end_idx == -1:
                    logger.warning(f"Invalid tool call format (unmatched parentheses): {line}")
                    continue
                
                args_str = call_str[args_start:end_idx].strip()
                
                # Parse JSON arguments
                if args_str:
                    arguments = json.loads(args_str)
                else:
                    arguments = {}
                
                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments)
                    }
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool arguments in '{line}': {e}")
            except Exception as e:
                logger.warning(f"Failed to parse tool call '{line}': {e}")
        
        return tool_calls if tool_calls else None
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any], db=None) -> Any:
        """
        Execute a single tool call.
        
        Args:
            tool_call: Tool call specification
            db: Database session to pass to tools
            
        Returns:
            Tool execution result
        """
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments_str = function.get("arguments", "{}")
        
        try:
            arguments = json.loads(arguments_str)
            # Add db session to arguments if not present
            if db is not None and 'db' not in arguments:
                arguments['db'] = db
            result = await execute_tool(tool_name, arguments)
            logger.info(f"Executed tool {tool_name} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def process_message(self, user_message: str, db=None) -> str:
        """
        Process a user message for Q&A (no tool calling).
        
        Args:
            user_message: User's input message
            db: Database session (unused now that tools are UI-driven)
            
        Returns:
            Assistant response
        """
        self.add_user_message(user_message)
        
        # Call LLM for Q&A
        response = await self._call_llm()
        choice = response["choices"][0]
        message = choice["message"]
        
        # Extract content from response
        content = message.get("content", "")
        self.add_assistant_message(content=content)
        return content
    
    async def stream_message(self, user_message: str, db=None) -> AsyncIterator[str]:
        """
        Process a user message with streaming response.
        
        This is a simplified streaming wrapper that delegates to process_message.
        The user message is added to conversation history by process_message.
        
        TODO: Implement true chunk-by-chunk streaming by directly calling
        llm_service.stream_complete() instead of delegating to process_message.
        This would require handling tool calls in a streaming context.
        
        Args:
            user_message: User's input message
            db: Database session for tool execution
            
        Yields:
            Response chunks as they're generated
        """
        response = await self.process_message(user_message, db=db)
        yield response
    
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
    llm_service,
    model: str = "llama-3",
    **kwargs
) -> AgentOrchestrator:
    """
    Factory function to create an agent orchestrator.
    
    Args:
        llm_service: LLMService instance for local inference
        model: Model identifier
        **kwargs: Additional arguments for AgentOrchestrator
        
    Returns:
        Configured AgentOrchestrator instance
    """
    return AgentOrchestrator(llm_service=llm_service, model=model, **kwargs)
