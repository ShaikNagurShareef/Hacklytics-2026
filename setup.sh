#!/bin/bash

# Define the root project name
PROJECT_NAME="health-agent-orchestrator"

echo "🚀 Bootstrapping project scaffold: $PROJECT_NAME..."

# 1. Create root directory and navigate into it
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME" || exit

# Create Root level config files
touch docker-compose.yml .env

# ==========================================
# 2. BACKEND FOLDERS & FILES
# ==========================================
echo "📁 Setting up FastAPI Backend..."

# Create core directories
mkdir -p backend/app/core
mkdir -p backend/app/api/routes
mkdir -p backend/app/db
mkdir -p backend/app/services

# Create specific agent workspaces for the 3 developers
AGENT_WORKSPACES=("oculomics" "wellbeing" "insurance" "diagnostic" "virtual_doctor" "dietary" "visualization")
for workspace in "${AGENT_WORKSPACES[@]}"; do
    mkdir -p "backend/app/agents/$workspace"
    # Create an empty init file for each workspace to make it a module
    touch "backend/app/agents/$workspace/__init__.py"
done

# Create core backend files
touch backend/Dockerfile
touch backend/requirements.txt
touch backend/app/main.py
touch backend/app/api/dependencies.py
touch backend/app/db/postgres.py backend/app/db/chroma.py backend/app/db/sqlite.py
touch backend/app/services/llm_client.py backend/app/services/search.py backend/app/services/vision.py
touch backend/app/agents/__init__.py backend/app/agents/orchestrator.py

# Inject the BaseAgent boilerplate contract
cat << 'EOF' > backend/app/agents/base.py
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
    async def invoke(self, session_id: str, query: str, context: List[Dict]) -> AgentResponse:
        pass
EOF

# ==========================================
# 3. FRONTEND FOLDERS & FILES
# ==========================================
echo "📁 Setting up React/TypeScript Frontend..."

mkdir -p frontend/src/components/Chat
mkdir -p frontend/src/components/Dashboard
mkdir -p frontend/src/components/Visuals
mkdir -p frontend/src/hooks
mkdir -p frontend/src/pages
mkdir -p frontend/src/services
mkdir -p frontend/src/store

# Create core frontend files
touch frontend/Dockerfile
touch frontend/package.json

echo "✅ Scaffold generation complete! Project is ready in the './$PROJECT_NAME' directory."