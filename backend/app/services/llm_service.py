"""
LLM Service
Wrapper for llama-cpp-python with Metal optimization.
"""
from pathlib import Path
from typing import List, Optional, AsyncIterable, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor


class LLMService:
    """Service for LLM inference using llama-cpp-python."""
    
    # Llama 3 special tokens that must be sanitized from user input
    SPECIAL_TOKENS = [
        "<|begin_of_text|>",
        "<|end_of_text|>",
        "<|eot_id|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
    ]
    
    def __init__(self, model_path: Path, n_ctx: int = 8192, n_gpu_layers: int = -1):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.model = None
        self.is_loaded = False
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def load_model(self):
        """Load the LLM model."""
        if self.is_loaded:
            return
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        # Import llama-cpp-python only when needed
        from llama_cpp import Llama
        
        # Load model in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            self.executor,
            lambda: Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
        )
        
        self.is_loaded = True
    
    async def unload(self):
        """Unload the model to free memory."""
        if self.model:
            self.model = None
            self.is_loaded = False
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate a completion."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        # Convert messages to prompt format
        prompt = self._format_messages(messages)
        
        # Generate in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or [],
                echo=False
            )
        )
        
        return response["choices"][0]["text"].strip()
    
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncIterable[str]:
        """Stream a completion."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        prompt = self._format_messages(messages)
        
        # Stream in thread pool
        loop = asyncio.get_event_loop()
        
        for chunk in self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        ):
            text = chunk["choices"][0]["text"]
            if text:
                yield text
    
    def _sanitize_content(self, content: str) -> str:
        """Remove special tokens from content to prevent prompt injection."""
        sanitized = content
        for token in self.SPECIAL_TOKENS:
            sanitized = sanitized.replace(token, "")
        return sanitized
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Llama 3 prompt format."""
        prompt = "<|begin_of_text|>"
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Sanitize content for user and assistant roles to prevent prompt injection
            if role in ("user", "assistant"):
                content = self._sanitize_content(content)
            
            if role == "system":
                prompt += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "user":
                prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
        
        # Add assistant prefix for completion
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        
        return prompt
    
    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate with tool calling support."""
        # TODO: Implement tool calling
        # For now, return basic completion
        content = await self.complete(messages, temperature=temperature)
        
        return {
            "content": content,
            "tool_calls": []
        }
