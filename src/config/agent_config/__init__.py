"""
Agent Configuration Package

Configuration-driven agent system that eliminates hardcoded values.
All domains, roles, and branding are loaded from JSON configuration files.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Configuration directory
CONFIG_DIR = Path(__file__).parent


class ConfigLoader:
    """
    Configuration loader that reads JSON files and provides
    dynamic access to configuration values.
    
    Implements the Singleton pattern to ensure configuration is loaded only once.
    """
    
    _instance: Optional['ConfigLoader'] = None
    
    def __new__(cls) -> 'ConfigLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._domains: Dict[str, Any] = {}
        self._roles: Dict[str, Any] = {}
        self._platform: Dict[str, Any] = {}
        self._loaded = False
        self._initialized = True
    
    def load(self) -> None:
        """Load all configuration files."""
        if self._loaded:
            return
            
        self._load_domains()
        self._load_roles()
        self._load_platform()
        self._loaded = True
        logger.info("Agent configuration loaded successfully")
    
    def _load_domains(self) -> None:
        """Load domains configuration."""
        domains_file = CONFIG_DIR / "domains.json"
        try:
            with open(domains_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._domains = data.get("domains", {})
            logger.info(f"Loaded {len(self._domains)} domains from configuration")
        except FileNotFoundError:
            logger.warning(f"Domains configuration file not found: {domains_file}")
            self._domains = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing domains configuration: {e}")
            self._domains = {}
    
    def _load_roles(self) -> None:
        """Load roles configuration."""
        roles_file = CONFIG_DIR / "roles.json"
        try:
            with open(roles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._roles = data.get("roles", {})
            logger.info(f"Loaded {len(self._roles)} roles from configuration")
        except FileNotFoundError:
            logger.warning(f"Roles configuration file not found: {roles_file}")
            self._roles = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing roles configuration: {e}")
            self._roles = {}
    
    def _load_platform(self) -> None:
        """Load platform configuration."""
        platform_file = CONFIG_DIR / "platform.json"
        try:
            with open(platform_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._platform = data
            logger.info("Platform configuration loaded")
        except FileNotFoundError:
            logger.warning(f"Platform configuration file not found: {platform_file}")
            self._platform = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing platform configuration: {e}")
            self._platform = {}
    
    def get_domains(self) -> Dict[str, Any]:
        """Get all domains configuration."""
        if not self._loaded:
            self.load()
        return self._domains
    
    def get_domain(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific domain configuration."""
        if not self._loaded:
            self.load()
        return self._domains.get(domain_id)
    
    def get_roles(self) -> Dict[str, Any]:
        """Get all roles configuration."""
        if not self._loaded:
            self.load()
        return self._roles
    
    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific role configuration."""
        if not self._loaded:
            self.load()
        return self._roles.get(role_id)
    
    def get_platform(self) -> Dict[str, Any]:
        """Get platform configuration."""
        if not self._loaded:
            self.load()
        return self._platform.get("platform", {})
    
    def get_nexus_config(self) -> Dict[str, Any]:
        """Get NEXUS specific configuration."""
        if not self._loaded:
            self.load()
        return self._platform.get("nexus", {})
    
    def get_features(self) -> Dict[str, Any]:
        """Get feature flags configuration."""
        if not self._loaded:
            self.load()
        return self._platform.get("features", {})
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default values configuration."""
        if not self._loaded:
            self.load()
        return self._platform.get("defaults", {})
    
    def get_domain_keywords(self, domain_id: str) -> List[str]:
        """Get keywords for a specific domain."""
        domain = self.get_domain(domain_id)
        return domain.get("keywords", []) if domain else []
    
    def get_role_keywords(self, role_id: str) -> List[str]:
        """Get keywords for a specific role."""
        role = self.get_role(role_id)
        return role.get("keywords", []) if role else []
    
    def get_mcp_servers_for_domain(self, domain_id: str) -> List[str]:
        """Get MCP servers for a specific domain."""
        domain = self.get_domain(domain_id)
        return domain.get("mcp_servers", []) if domain else []
    
    def get_role_skills(self, role_id: str) -> List[str]:
        """Get skills for a specific role."""
        role = self.get_role(role_id)
        return role.get("skills", []) if role else []
    
    def get_role_tools(self, role_id: str) -> List[str]:
        """Get tools for a specific role."""
        role = self.get_role(role_id)
        return role.get("tools", []) if role else []
    
    def detect_domain(self, query: str) -> tuple:
        """
        Detect the most appropriate domain for a query.
        
        Returns:
            Tuple of (domain_id, confidence)
        """
        if not self._loaded:
            self.load()
            
        query_lower = query.lower()
        scores: Dict[str, int] = {}
        
        for domain_id, domain_config in self._domains.items():
            keywords = domain_config.get("keywords", [])
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[domain_id] = score
        
        if not scores:
            defaults = self.get_defaults()
            return defaults.get("domain", "custom"), defaults.get("confidence_threshold", 0.3)
        
        best_domain = max(scores, key=scores.get)
        total_matches = scores[best_domain]
        max_possible = len(self._domains.get(best_domain, {}).get("keywords", []))
        
        defaults = self.get_defaults()
        base_confidence = defaults.get("base_confidence", 0.4)
        keyword_weight = defaults.get("keyword_weight", 0.5)
        max_confidence = defaults.get("max_confidence", 0.95)
        
        confidence = min(max_confidence, base_confidence + (total_matches / max(max_possible, 1)) * keyword_weight)
        
        return best_domain, confidence
    
    def detect_roles(self, query: str, specific_role: Optional[str] = None) -> List[str]:
        """
        Detect appropriate roles for a query.
        
        Returns:
            List of role IDs
        """
        if not self._loaded:
            self.load()
            
        if specific_role:
            return [specific_role]
        
        query_lower = query.lower()
        roles: List[str] = []
        
        for role_id, role_config in self._roles.items():
            keywords = role_config.get("keywords", [])
            if any(kw in query_lower for kw in keywords):
                roles.append(role_id)
        
        # If no roles detected, use defaults
        if not roles:
            # Get default roles from config
            roles_file = CONFIG_DIR / "roles.json"
            try:
                with open(roles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    roles = data.get("default_roles", ["assistant", "investigator"])
            except:
                roles = ["assistant", "investigator"]
        
        return roles
    
    def reload(self) -> None:
        """Reload all configuration files."""
        self._loaded = False
        self.load()


# Global configuration loader instance
config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get the global configuration loader instance."""
    return config_loader


def load_config() -> None:
    """Load the configuration."""
    config_loader.load()


# Export commonly used functions
__all__ = [
    'ConfigLoader',
    'config_loader',
    'get_config',
    'load_config',
]
