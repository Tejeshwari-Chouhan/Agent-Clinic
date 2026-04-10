"""Base agent class for LLM-based agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import os
import json

# Load .env before importing OpenAI
from dotenv import load_dotenv
load_dotenv()


class BaseAgent(ABC):
    """Base class for all LLM-based agents. Falls back gracefully when no API key is set."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.model = 'gpt-4o-mini'
        self.conversation_history: List[Dict] = []
        self.client = None
        self._api_available = False

        api_key = os.getenv('OPENAI_API_KEY', '')
        if api_key and api_key != 'your_openai_api_key_here':
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self._api_available = True
            except Exception:
                pass

    def add_message(self, role: str, content: str):
        self.conversation_history.append({'role': role, 'content': content})

    def get_response(self, user_message: str) -> str:
        """Get LLM response; falls back to rule-based stub if API unavailable."""
        self.add_message('user', user_message)

        if self._api_available and self.client:
            try:
                messages = [
                    {'role': 'system', 'content': self.system_prompt},
                    *self.conversation_history
                ]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )
                reply = response.choices[0].message.content
                self.add_message('assistant', reply)
                return reply
            except Exception as e:
                # Fall through to rule-based fallback on API error
                pass

        # Rule-based fallback — subclasses can override _fallback_response
        fallback = self._fallback_response(user_message)
        self.add_message('assistant', fallback)
        return fallback

    def _fallback_response(self, user_message: str) -> str:
        """Override in subclasses to provide domain-specific fallbacks."""
        return json.dumps({
            "error": "LLM unavailable",
            "message": "OpenAI API key not configured. Set OPENAI_API_KEY in backend/.env"
        })

    def clear_history(self):
        self.conversation_history = []

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
