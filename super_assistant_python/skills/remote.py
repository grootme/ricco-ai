"""
Integración con Repositorios Remotos de Skills
==============================================

Conectores para fuentes de skills remotas:
- DeerFlow: Framework de flujos de trabajo de agentes
- NVIDIA NIM: Modelos y tools optimizados
- LangChain: Herramientas y chains
- GitHub: Repositorios de código
- HuggingFace: Modelos y datasets
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import yaml


class RemoteSkillConnector(ABC):
    """Clase base para conectores de skills remotas"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Listar skills disponibles"""
        pass
    
    @abstractmethod
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de una skill"""
        pass
    
    @abstractmethod
    async def download_skill(self, skill_id: str) -> Optional[str]:
        """Descargar código de una skill"""
        pass


class DeerFlowConnector(RemoteSkillConnector):
    """
    Conector para DeerFlow - Framework de flujos de trabajo de agentes.
    
    DeerFlow proporciona flujos de trabajo pre-construidos para agentes
    que pueden ser utilizados como skills.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key, "https://api.deerflow.ai/v1")
    
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Listar flujos de trabajo disponibles en DeerFlow"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with session.get(
                    f"{self.base_url}/workflows",
                    headers=headers,
                    params={"limit": limit}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_workflows(data.get("workflows", []))
                    return []
        except Exception as e:
            print(f"DeerFlow list error: {e}")
            return []
    
    async def get_skill(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un flujo de trabajo"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with session.get(
                    f"{self.base_url}/workflows/{workflow_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_workflow(data)
                    return None
        except Exception as e:
            print(f"DeerFlow get error: {e}")
            return None
    
    async def download_skill(self, workflow_id: str) -> Optional[str]:
        """Descargar código de un flujo de trabajo"""
        workflow = await self.get_skill(workflow_id)
        if workflow:
            return workflow.get("code")
        return None
    
    def _parse_workflows(self, workflows: List[Dict]) -> List[Dict[str, Any]]:
        """Parsear lista de flujos de trabajo"""
        return [
            {
                "id": w.get("id"),
                "name": w.get("name"),
                "description": w.get("description"),
                "category": w.get("category", "AUTOMATION"),
                "tags": w.get("tags", []),
                "source": "DEERFLOW"
            }
            for w in workflows
        ]
    
    def _parse_workflow(self, data: Dict) -> Dict[str, Any]:
        """Parsear un flujo de trabajo individual"""
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "category": data.get("category", "AUTOMATION"),
            "tags": data.get("tags", []),
            "code": data.get("definition", {}).get("code", ""),
            "config": data.get("config", {}),
            "source": "DEERFLOW"
        }


class NIMConnector(RemoteSkillConnector):
    """
    Conector para NVIDIA NIM - NeMo Inference Microservices.
    
    NIM proporciona modelos optimizados y herramientas que pueden
    ser utilizadas como skills de inferencia.
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://integrate.api.nvidia.com/v1")
    
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Listar modelos y herramientas disponibles en NIM"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_models(data.get("data", []))
                    return []
        except Exception as e:
            print(f"NIM list error: {e}")
            return []
    
    async def get_skill(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un modelo"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(
                    f"{self.base_url}/models/{model_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_model(data)
                    return None
        except Exception as e:
            print(f"NIM get error: {e}")
            return None
    
    async def download_skill(self, model_id: str) -> Optional[str]:
        """Generar código de wrapper para el modelo"""
        model = await self.get_skill(model_id)
        if model:
            return self._generate_wrapper_code(model)
        return None
    
    def _parse_models(self, models: List[Dict]) -> List[Dict[str, Any]]:
        """Parsear lista de modelos"""
        return [
            {
                "id": m.get("id"),
                "name": m.get("id").split("/")[-1] if "/" in m.get("id", "") else m.get("id"),
                "description": f"NVIDIA NIM model: {m.get('id')}",
                "category": "TRANSFORM",
                "tags": ["nvidia", "nim", "inference"],
                "source": "NIM"
            }
            for m in models
        ]
    
    def _parse_model(self, data: Dict) -> Dict[str, Any]:
        """Parsear un modelo individual"""
        model_id = data.get("id", "")
        return {
            "id": model_id,
            "name": model_id.split("/")[-1] if "/" in model_id else model_id,
            "description": f"NVIDIA NIM model: {model_id}",
            "category": "TRANSFORM",
            "tags": ["nvidia", "nim", "inference"],
            "config": {
                "model": model_id,
                "endpoint": self.base_url
            },
            "source": "NIM"
        }
    
    def _generate_wrapper_code(self, model: Dict) -> str:
        """Generar código wrapper para el modelo"""
        model_id = model.get("id", "")
        return f'''
import aiohttp
import json

async def execute(input):
    """
    Execute NVIDIA NIM model: {model_id}
    
    Args:
        input: {{"prompt": str, "max_tokens": int, "temperature": float}}
    
    Returns:
        {{"response": str, "model": str}}
    """
    api_key = config.get("api_key", "")
    prompt = input.get("prompt", "")
    max_tokens = input.get("max_tokens", 512)
    temperature = input.get("temperature", 0.7)
    
    async with aiohttp.ClientSession() as session:
        headers = {{
            "Authorization": f"Bearer {{api_key}}",
            "Content-Type": "application/json"
        }}
        
        payload = {{
            "model": "{model_id}",
            "messages": [{{"role": "user", "content": prompt}}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }}
        
        async with session.post(
            "{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
    
    return {{
        "response": result.get("choices", [{{}}])[0].get("message", {{}}).get("content", ""),
        "model": "{model_id}"
    }}
'''


class LangChainConnector(RemoteSkillConnector):
    """
    Conector para LangChain Hub - Herramientas y chains.
    
    LangChain Hub proporciona prompts, chains y herramientas
    que pueden ser utilizadas como skills.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key, "https://api.hub.langchain.com")
    
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Listar herramientas disponibles en LangChain Hub"""
        # LangChain Hub tiene una API pública
        try:
            async with aiohttp.ClientSession() as session:
                # Listar prompts y chains populares
                async with session.get(
                    f"{self.base_url}/repos",
                    params={"limit": limit}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_repos(data.get("repos", []))
                    return []
        except Exception as e:
            print(f"LangChain list error: {e}")
            return []
    
    async def get_skill(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un repositorio"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/repos/{repo_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_repo(data)
                    return None
        except Exception as e:
            print(f"LangChain get error: {e}")
            return None
    
    async def download_skill(self, repo_id: str) -> Optional[str]:
        """Descargar contenido del repositorio"""
        repo = await self.get_skill(repo_id)
        if repo:
            return repo.get("code")
        return None
    
    def _parse_repos(self, repos: List[Dict]) -> List[Dict[str, Any]]:
        """Parsear lista de repositorios"""
        return [
            {
                "id": r.get("full_name", r.get("id")),
                "name": r.get("name"),
                "description": r.get("description", ""),
                "category": "AUTOMATION",
                "tags": r.get("tags", ["langchain"]),
                "source": "LANGCHAIN"
            }
            for r in repos
        ]
    
    def _parse_repo(self, data: Dict) -> Dict[str, Any]:
        """Parsear un repositorio individual"""
        return {
            "id": data.get("full_name", data.get("id")),
            "name": data.get("name"),
            "description": data.get("description", ""),
            "category": "AUTOMATION",
            "tags": data.get("tags", ["langchain"]),
            "code": data.get("content", ""),
            "config": data.get("config", {}),
            "source": "LANGCHAIN"
        }


class GitHubConnector(RemoteSkillConnector):
    """
    Conector para GitHub - Repositorios de código.
    
    Permite descubrir y descargar skills desde repositorios
    de GitHub que sigan una estructura definida.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key, "https://api.github.com")
    
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Buscar repositorios con skills"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"token {self.api_key}"
                
                # Buscar repositorios con skills
                query = "topic:ai-skill topic:agent-skill topic:llm-tool"
                
                async with session.get(
                    f"{self.base_url}/search/repositories",
                    headers=headers,
                    params={"q": query, "per_page": limit}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_repos(data.get("items", []))
                    return []
        except Exception as e:
            print(f"GitHub list error: {e}")
            return []
    
    async def get_skill(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un repositorio"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"token {self.api_key}"
                
                # Obtener info del repo
                async with session.get(
                    f"{self.base_url}/repos/{repo_full_name}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        
                        # Intentar obtener skill.yaml
                        skill_content = await self._get_file_content(
                            session, headers, repo_full_name, "skill.yaml"
                        )
                        
                        if skill_content:
                            skill_data = yaml.safe_load(skill_content)
                            return self._parse_repo(repo_data, skill_data)
                        
                        return self._parse_repo(repo_data)
                    return None
        except Exception as e:
            print(f"GitHub get error: {e}")
            return None
    
    async def download_skill(self, repo_full_name: str) -> Optional[str]:
        """Descargar código principal del repositorio"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"token {self.api_key}"
                
                # Intentar obtener main.py o index.py
                for filename in ["main.py", "index.py", "skill.py", "src/main.py"]:
                    content = await self._get_file_content(
                        session, headers, repo_full_name, filename
                    )
                    if content:
                        return content
                
                return None
        except Exception as e:
            print(f"GitHub download error: {e}")
            return None
    
    async def _get_file_content(
        self,
        session: aiohttp.ClientSession,
        headers: Dict,
        repo_full_name: str,
        filepath: str
    ) -> Optional[str]:
        """Obtener contenido de un archivo"""
        try:
            async with session.get(
                f"{self.base_url}/repos/{repo_full_name}/contents/{filepath}",
                headers=headers
            ) as response:
                if response.status == 200:
                    import base64
                    data = await response.json()
                    content = data.get("content", "")
                    return base64.b64decode(content).decode("utf-8")
                return None
        except Exception:
            return None
    
    def _parse_repos(self, repos: List[Dict]) -> List[Dict[str, Any]]:
        """Parsear lista de repositorios"""
        return [
            {
                "id": r.get("full_name"),
                "name": r.get("name"),
                "description": r.get("description", ""),
                "category": "CUSTOM",
                "tags": r.get("topics", ["github"]),
                "source": "GITHUB",
                "stars": r.get("stargazers_count", 0)
            }
            for r in repos
        ]
    
    def _parse_repo(self, repo_data: Dict, skill_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Parsear un repositorio individual"""
        result = {
            "id": repo_data.get("full_name"),
            "name": repo_data.get("name"),
            "description": repo_data.get("description", ""),
            "category": "CUSTOM",
            "tags": repo_data.get("topics", ["github"]),
            "source": "GITHUB",
            "config": {
                "repo_url": repo_data.get("html_url"),
                "stars": repo_data.get("stargazers_count", 0)
            }
        }
        
        if skill_data:
            result.update({
                "name": skill_data.get("name", result["name"]),
                "description": skill_data.get("description", result["description"]),
                "category": skill_data.get("category", result["category"]),
                "tags": skill_data.get("tags", result["tags"]),
                "code": skill_data.get("code", ""),
                "config": {**result["config"], **skill_data.get("config", {})}
            })
        
        return result


class HuggingFaceConnector(RemoteSkillConnector):
    """
    Conector para HuggingFace - Modelos y datasets.
    
    Permite usar modelos de HuggingFace como skills.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key, "https://huggingface.co/api")
    
    async def list_skills(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Listar modelos populares para tareas de agentes"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                # Buscar modelos con tags relevantes
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    params={
                        "filter": "text-generation,instruct,agent",
                        "limit": limit
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_models(data)
                    return []
        except Exception as e:
            print(f"HuggingFace list error: {e}")
            return []
    
    async def get_skill(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles de un modelo"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with session.get(
                    f"{self.base_url}/models/{model_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_model(data)
                    return None
        except Exception as e:
            print(f"HuggingFace get error: {e}")
            return None
    
    async def download_skill(self, model_id: str) -> Optional[str]:
        """Generar código wrapper para el modelo"""
        model = await self.get_skill(model_id)
        if model:
            return self._generate_inference_code(model)
        return None
    
    def _parse_models(self, models: List[Dict]) -> List[Dict[str, Any]]:
        """Parsear lista de modelos"""
        return [
            {
                "id": m.get("id") or m.get("modelId"),
                "name": (m.get("id") or m.get("modelId", "")).split("/")[-1],
                "description": m.get("description", f"HuggingFace model: {m.get('id', m.get('modelId', ''))}"),
                "category": "TRANSFORM",
                "tags": m.get("tags", ["huggingface"]),
                "source": "HUGGINGFACE",
                "downloads": m.get("downloads", 0)
            }
            for m in models
        ]
    
    def _parse_model(self, data: Dict) -> Dict[str, Any]:
        """Parsear un modelo individual"""
        model_id = data.get("id") or data.get("modelId", "")
        return {
            "id": model_id,
            "name": model_id.split("/")[-1],
            "description": data.get("description", f"HuggingFace model: {model_id}"),
            "category": "TRANSFORM",
            "tags": data.get("tags", ["huggingface"]),
            "config": {
                "model_id": model_id,
                "task": data.get("pipeline_tag", "text-generation")
            },
            "source": "HUGGINGFACE"
        }
    
    def _generate_inference_code(self, model: Dict) -> str:
        """Generar código de inferencia para el modelo"""
        model_id = model.get("id", "")
        return f'''
import requests

def execute(input):
    """
    Execute HuggingFace model: {model_id}
    
    Args:
        input: {{"prompt": str, "parameters": dict}}
    
    Returns:
        {{"response": str, "model": str}}
    """
    api_key = config.get("api_key", "")
    prompt = input.get("prompt", "")
    parameters = input.get("parameters", {{}})
    
    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json"
    }}
    
    payload = {{
        "inputs": prompt,
        "parameters": parameters
    }}
    
    response = requests.post(
        "https://api-inference.huggingface.co/models/{model_id}",
        headers=headers,
        json=payload
    )
    
    result = response.json()
    
    if isinstance(result, list):
        text = result[0].get("generated_text", "")
    else:
        text = result.get("generated_text", str(result))
    
    return {{
        "response": text,
        "model": "{model_id}"
    }}
'''


# ============================================
# REGISTRY DE CONECTORES
# ============================================

class RemoteSkillRegistry:
    """
    Registro de conectores para fuentes remotas de skills.
    """
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {}
        self._connectors: Dict[str, RemoteSkillConnector] = {}
        
        # Inicializar conectores con API keys
        self._init_connectors()
    
    def _init_connectors(self):
        """Inicializar conectores disponibles"""
        if "nvidia_api_key" in self.config:
            self._connectors["NIM"] = NIMConnector(self.config["nvidia_api_key"])
        
        if "deerflow_api_key" in self.config:
            self._connectors["DEERFLOW"] = DeerFlowConnector(self.config["deerflow_api_key"])
        
        if "langchain_api_key" in self.config:
            self._connectors["LANGCHAIN"] = LangChainConnector(self.config["langchain_api_key"])
        
        if "github_api_key" in self.config:
            self._connectors["GITHUB"] = GitHubConnector(self.config["github_api_key"])
        else:
            self._connectors["GITHUB"] = GitHubConnector()  # Works without key
        
        if "huggingface_api_key" in self.config:
            self._connectors["HUGGINGFACE"] = HuggingFaceConnector(self.config["huggingface_api_key"])
        else:
            self._connectors["HUGGINGFACE"] = HuggingFaceConnector()
    
    def get_connector(self, source: str) -> Optional[RemoteSkillConnector]:
        """Obtener conector por fuente"""
        return self._connectors.get(source.upper())
    
    async def discover_all_skills(self, limit_per_source: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Descubrir skills de todas las fuentes"""
        results = {}
        
        tasks = []
        for source, connector in self._connectors.items():
            tasks.append(self._fetch_skills(source, connector, limit_per_source))
        
        skill_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (source, _), skills in zip(self._connectors.items(), skill_lists):
            if isinstance(skills, Exception):
                results[source] = []
            else:
                results[source] = skills
        
        return results
    
    async def _fetch_skills(
        self,
        source: str,
        connector: RemoteSkillConnector,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch skills de un conector"""
        try:
            return await connector.list_skills(limit)
        except Exception as e:
            print(f"Error fetching from {source}: {e}")
            return []
