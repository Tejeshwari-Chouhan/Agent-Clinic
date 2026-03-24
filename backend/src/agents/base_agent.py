"""Base agent class for LLM-based agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import os
from openai import OpenAI

class BaseAgent(ABC):
    """Base class for all LLM-based agents"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = 'gpt-4'
        self.conversation_history = []
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            'role': role,
            'content': content
        })
    
    def get_response(self, user_message: str) -> str:
        """Get response from LLM"""
        self.add_message('user', user_message)
        
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            *self.conversation_history
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message.content
        self.add_message('assistant', assistant_message)
        
        return assistant_message
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output - to be implemented by subclasses"""
        pass
