from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Dict, Any

class AgentResponse(BaseModel):
    agent_name: str
    content: str
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Used by the Orchestrator to route the query."""
        pass

    @abstractmethod
    async def invoke(self, session_id: str, query: str, context: List[Dict], **kwargs: Any) -> AgentResponse:
        pass
