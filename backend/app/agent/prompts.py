"""
Prompt management for Aetios agent.
Loads and manages prompt templates from data/prompts/ directory.
"""
from pathlib import Path
from typing import Dict, Optional
import os


class PromptManager:
    """Manages loading and accessing prompt templates."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Path to prompts directory. If None, uses default location.
        """
        if prompts_dir is None:
            # Default to data/prompts relative to this file
            base_dir = Path(__file__).parent.parent
            prompts_dir = base_dir / "data" / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates from the prompts directory."""
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}"
            )
        
        # Load all .txt files in the prompts directory
        for prompt_file in self.prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self._prompts[prompt_name] = f.read().strip()
    
    def get_prompt(self, name: str) -> str:
        """
        Get a prompt template by name.
        
        Args:
            name: Name of the prompt (without .txt extension)
            
        Returns:
            Prompt template content
            
        Raises:
            KeyError: If prompt not found
        """
        if name not in self._prompts:
            raise KeyError(
                f"Prompt '{name}' not found. Available prompts: {list(self._prompts.keys())}"
            )
        return self._prompts[name]
    
    def get_system_prompt(self) -> str:
        """Get the main system prompt for Aetios tutor."""
        return self.get_prompt("tutor_system")
    
    def get_quiz_generation_prompt(self) -> str:
        """Get the quiz generation prompt."""
        return self.get_prompt("quiz_generation")
    
    def get_study_plan_prompt(self) -> str:
        """Get the study plan generation prompt."""
        return self.get_prompt("study_plan")
    
    def format_prompt(self, name: str, **kwargs) -> str:
        """
        Get a prompt and format it with variables.
        
        Args:
            name: Name of the prompt
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt
        """
        template = self.get_prompt(name)
        return template.format(**kwargs)
    
    def list_prompts(self) -> list:
        """Get list of available prompt names."""
        return list(self._prompts.keys())
    
    def reload(self):
        """Reload all prompts from disk."""
        self._prompts.clear()
        self._load_prompts()


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    Get the global prompt manager instance.
    
    Returns:
        Global PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


# Convenience functions
def get_system_prompt() -> str:
    """Get the main system prompt for Aetios tutor."""
    return get_prompt_manager().get_system_prompt()


def get_quiz_generation_prompt() -> str:
    """Get the quiz generation prompt."""
    return get_prompt_manager().get_quiz_generation_prompt()


def get_study_plan_prompt() -> str:
    """Get the study plan generation prompt."""
    return get_prompt_manager().get_study_plan_prompt()
