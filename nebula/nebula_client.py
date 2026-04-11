"""
RICCO Ecosystem - NebulaGraph Integration Service
Social Graph para relaciones, confianza y recomendaciones
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

# NebulaGraph Python client
try:
    from nebula3.gclient.net import ConnectionPool
    from nebula3.Config import Config as NebulaConfig
    NEBULA_AVAILABLE = True
except ImportError:
    NEBULA_AVAILABLE = False


@dataclass
class NebulaConfig:
    """Configuración de conexión NebulaGraph"""
    host: str = os.getenv("NEBULA_HOST", "localhost")
    port: int = int(os.getenv("NEBULA_PORT", "9669"))
    user: str = os.getenv("NEBULA_USER", "root")
    password: str = os.getenv("NEBULA_PASSWORD", "nebula")
    space: str = os.getenv("NEBULA_SPACE", "ricco_ecosystem")
    max_connections: int = 10


class NebulaGraphClient:
    """
    Cliente de NebulaGraph para el Social Graph de RICCO.
    
    Maneja:
    - Identidades y perfiles
    - Relaciones de confianza
    - Recomendaciones basadas en grafo
    - Análisis de influencia
    """
    
    def __init__(self, config: Optional[NebulaConfig] = None):
        self.config = config or NebulaConfig()
        self.pool = None
        self.session = None
        
    async def connect(self):
        """Establece conexión con NebulaGraph"""
        if not NEBULA_AVAILABLE:
            raise ImportError("nebula3-python no está instalado")
        
        config = NebulaConfig()
        config.max_connection_pool_size = self.config.max_connections
        
        self.pool = ConnectionPool()
        ok = self.pool.init([(self.config.host, self.config.port)], config)
        if not ok:
            raise ConnectionError("No se pudo conectar a NebulaGraph")
        
        self.session = self.pool.get_session(
            self.config.user,
            self.config.password
        )
        
        # Asegurar que el espacio existe
        await self._ensure_space()
    
    async def close(self):
        """Cierra la conexión"""
        if self.session:
            self.session.release()
        if self.pool:
            self.pool.close()
    
    async def _ensure_space(self):
        """Asegura que el espacio de grafos existe"""
        query = f"""
        CREATE SPACE IF NOT EXISTS {self.config.space} (
            partition_num = 10,
            replica_factor = 1,
            vid_type = FIXED_STRING(64)
        );
        """
        await self.execute(query)
    
    async def execute(self, query: str) -> Any:
        """Ejecuta una consulta nGQL"""
        if not self.session:
            await self.connect()
        
        result = self.session.execute(query)
        if not result.is_succeeded():
            raise Exception(f"Query failed: {result.error_msg()}")
        return result
    
    # ========================================
    # GESTIÓN DE USUARIOS (Nodos)
    # ========================================
    
    async def create_user(self, user_data: Dict) -> bool:
        """
        Crea un nodo de usuario en el grafo.
        
        Args:
            user_data: Datos del usuario (ricco_id, email, trust_score, etc.)
            
        Returns:
            True si se creó exitosamente
        """
        vid = self._sanitize_vid(user_data["ricco_id"])
        
        query = f"""
        USE {self.config.space};
        INSERT VERTEX user (
            ricco_id, email, phone, trust_score, verification_level,
            created_at, last_active, energy_points, subscription_tier
        ) VALUES "{vid}": (
            "{user_data.get('ricco_id', '')}",
            "{user_data.get('email', '')}",
            "{user_data.get('phone', '')}",
            {user_data.get('trust_score', 0)},
            {user_data.get('verification_level', 0)},
            timestamp(),
            timestamp(),
            {user_data.get('energy_points', 0)},
            "{user_data.get('subscription_tier', 'peon')}"
        );
        """
        
        await self.execute(query)
        return True
    
    async def update_user(self, ricco_id: str, updates: Dict) -> bool:
        """
        Actualiza propiedades de un usuario.
        
        Args:
            ricco_id: ID del usuario
            updates: Campos a actualizar
            
        Returns:
            True si se actualizó exitosamente
        """
        vid = self._sanitize_vid(ricco_id)
        set_clauses = []
        
        for key, value in updates.items():
            if isinstance(value, str):
                set_clauses.append(f'{key} = "{value}"')
            elif isinstance(value, (int, float)):
                set_clauses.append(f'{key} = {value}')
        
        if not set_clauses:
            return False
        
        query = f"""
        USE {self.config.space};
        UPDATE VERTEX ON user "{vid}" SET {', '.join(set_clauses)};
        """
        
        await self.execute(query)
        return True
    
    async def get_user(self, ricco_id: str) -> Optional[Dict]:
        """Obtiene datos de un usuario"""
        vid = self._sanitize_vid(ricco_id)
        
        query = f"""
        USE {self.config.space};
        FETCH PROP ON user "{vid}" YIELD vertex as v;
        """
        
        result = await self.execute(query)
        return self._parse_vertex_result(result)
    
    # ========================================
    # GESTIÓN DE NEGOCIOS
    # ========================================
    
    async def create_business(self, business_data: Dict) -> bool:
        """Crea un nodo de negocio/empresa"""
        vid = self._sanitize_vid(business_data["business_id"])
        
        query = f"""
        USE {self.config.space};
        INSERT VERTEX business (
            business_id, name, rut, industry, trust_score,
            verification_status, created_at, subscription_tier
        ) VALUES "{vid}": (
            "{business_data.get('business_id', '')}",
            "{business_data.get('name', '')}",
            "{business_data.get('rut', '')}",
            "{business_data.get('industry', '')}",
            {business_data.get('trust_score', 0)},
            {business_data.get('verification_status', 0)},
            timestamp(),
            "{business_data.get('subscription_tier', 'peon')}"
        );
        """
        
        await self.execute(query)
        return True
    
    # ========================================
    # RELACIONES (Edges)
    # ========================================
    
    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        properties: Optional[Dict] = None
    ) -> bool:
        """
        Crea una relación entre dos entidades.
        
        Args:
            from_id: ID de origen
            to_id: ID de destino
            edge_type: Tipo de edge (follows, friends_with, owns, etc.)
            properties: Propiedades del edge
            
        Returns:
            True si se creó exitosamente
        """
        from_vid = self._sanitize_vid(from_id)
        to_vid = self._sanitize_vid(to_id)
        props = properties or {}
        
        # Construir propiedades
        if edge_type == "follows":
            props_str = f'since: timestamp()'
        elif edge_type == "friends_with":
            props_str = f'since: timestamp(), closeness_score: {props.get("closeness_score", 50)}'
        elif edge_type == "owns":
            props_str = f'role: "{props.get("role", "owner")}", since: timestamp()'
        elif edge_type == "trusts":
            props_str = f'trust_score: {props.get("trust_score", 50)}, reason: "{props.get("reason", "")}", since: timestamp()'
        elif edge_type == "referred_by":
            props_str = f'reward_claimed: {str(props.get("reward_claimed", False)).lower()}, reward_amount: {props.get("reward_amount", 0)}'
        else:
            props_str = ''
        
        query = f"""
        USE {self.config.space};
        INSERT EDGE {edge_type} ({self._get_edge_props(edge_type)}) 
        VALUES "{from_vid}"->"{to_vid}": ({props_str});
        """
        
        await self.execute(query)
        return True
    
    async def delete_relationship(
        self,
        from_id: str,
        to_id: str,
        edge_type: str
    ) -> bool:
        """Elimina una relación"""
        from_vid = self._sanitize_vid(from_id)
        to_vid = self._sanitize_vid(to_id)
        
        query = f"""
        USE {self.config.space};
        DELETE EDGE {edge_type} "{from_vid}"->"{to_vid}";
        """
        
        await self.execute(query)
        return True
    
    # ========================================
    # CONSULTAS DE SOCIAL GRAPH
    # ========================================
    
    async def get_user_network(
        self,
        ricco_id: str,
        depth: int = 2,
        limit: int = 100
    ) -> Dict:
        """
        Obtiene la red de contactos de un usuario.
        
        Args:
            ricco_id: ID del usuario
            depth: Profundidad de búsqueda (1 o 2)
            limit: Límite de resultados
            
        Returns:
            Diccionario con nodos y edges
        """
        vid = self._sanitize_vid(ricco_id)
        
        if depth == 1:
            query = f"""
            USE {self.config.space};
            GO FROM "{vid}" OVER follows, friends_with BIDIRECT
            YIELD dst(edge) as vid, type(edge) as edge_type
            | LIMIT {limit};
            """
        else:
            query = f"""
            USE {self.config.space};
            GO 2 STEPS FROM "{vid}" OVER follows, friends_with BIDIRECT
            YIELD dst(edge) as vid, type(edge) as edge_type
            | LIMIT {limit};
            """
        
        result = await self.execute(query)
        return self._parse_path_result(result)
    
    async def get_trust_network(self, ricco_id: str) -> Dict:
        """
        Obtiene la red de confianza de un usuario.
        
        Args:
            ricco_id: ID del usuario
            
        Returns:
            Red de confianza con scores
        """
        vid = self._sanitize_vid(ricco_id)
        
        query = f"""
        USE {self.config.space};
        GO FROM "{vid}" OVER trusts BIDIRECT
        YIELD dst(edge) as vid, trusts.trust_score as score
        | ORDER BY $-.score DESC
        | LIMIT 50;
        """
        
        result = await self.execute(query)
        return self._parse_trust_result(result)
    
    async def get_mutual_connections(
        self,
        user1_id: str,
        user2_id: str
    ) -> List[Dict]:
        """
        Encuentra conexiones mutuas entre dos usuarios.
        
        Args:
            user1_id: ID del primer usuario
            user2_id: ID del segundo usuario
            
        Returns:
            Lista de conexiones mutuas
        """
        vid1 = self._sanitize_vid(user1_id)
        vid2 = self._sanitize_vid(user2_id)
        
        query = f"""
        USE {self.config.space};
        (GO FROM "{vid1}" OVER follows, friends_with YIELD dst(edge) as vid)
        INTERSECTION
        (GO FROM "{vid2}" OVER follows, friends_with YIELD dst(edge) as vid);
        """
        
        result = await self.execute(query)
        return self._parse_list_result(result)
    
    async def get_recommendations(
        self,
        ricco_id: str,
        recommendation_type: str = "users",
        limit: int = 10
    ) -> List[Dict]:
        """
        Genera recomendaciones basadas en el grafo social.
        
        Args:
            ricco_id: ID del usuario
            recommendation_type: Tipo de recomendación (users, products, businesses)
            limit: Límite de resultados
            
        Returns:
            Lista de recomendaciones con scores
        """
        vid = self._sanitize_vid(ricco_id)
        
        if recommendation_type == "users":
            # "Friends of friends" que no son ya amigos
            query = f"""
            USE {self.config.space};
            GO FROM "{vid}" OVER follows YIELD dst(edge) as friend
            | GO FROM $-.friend OVER follows YIELD dst(edge) as fof
            | WHERE $-.fof != "{vid}" 
              AND $-.fof NOT IN (GO FROM "{vid}" OVER follows YIELD dst(edge))
            | GROUP BY $-.fof YIELD $-.fof as recommended, COUNT(*) as mutual_count
            | ORDER BY $-.mutual_count DESC
            | LIMIT {limit};
            """
        elif recommendation_type == "businesses":
            # Negocios populares en la red del usuario
            query = f"""
            USE {self.config.space};
            GO FROM "{vid}" OVER follows YIELD dst(edge) as friend
            | GO FROM $-.friend OVER owns YIELD dst(edge) as biz
            | GROUP BY $-.biz YIELD $-.biz as business, COUNT(*) as owner_friends
            | ORDER BY $-.owner_friends DESC
            | LIMIT {limit};
            """
        else:
            return []
        
        result = await self.execute(query)
        return self._parse_recommendation_result(result)
    
    async def calculate_trust_score(
        self,
        ricco_id: str,
        depth: int = 2
    ) -> int:
        """
        Calcula el trust score basado en la red de confianza.
        
        Args:
            ricco_id: ID del usuario
            depth: Profundidad para calcular
            
        Returns:
            Trust score calculado (0-100)
        """
        vid = self._sanitize_vid(ricco_id)
        
        # Obtener trust scores de la red
        query = f"""
        USE {self.config.space};
        GO {depth} STEPS FROM "{vid}" OVER trusts BIDIRECT
        YIELD dst(edge) as vid, trusts.trust_score as score
        | GROUP BY $-.vid YIELD AVG($-.score) as avg_trust;
        """
        
        result = await self.execute(query)
        scores = self._parse_score_result(result)
        
        if scores:
            return int(scores[0].get("avg_trust", 50))
        return 50  # Default score
    
    async def get_influencers(
        self,
        industry: Optional[str] = None,
        min_followers: int = 100,
        limit: int = 20
    ) -> List[Dict]:
        """
        Encuentra usuarios influyentes en el grafo.
        
        Args:
            industry: Filtrar por industria (opcional)
            min_followers: Mínimo de seguidores
            limit: Límite de resultados
            
        Returns:
            Lista de influencers con métricas
        """
        if industry:
            query = f"""
            USE {self.config.space};
            MATCH (u:user)-[:owns]->(b:business WHERE b.industry == "{industry}")
            WITH u, COUNT{(f:user)-[:follows]->(u)} as followers
            WHERE followers >= {min_followers}
            RETURN u.ricco_id as ricco_id, u.trust_score as trust_score, followers
            ORDER BY followers DESC
            LIMIT {limit};
            """
        else:
            query = f"""
            USE {self.config.space};
            MATCH (u:user)
            WITH u, COUNT{{(f:user)-[:follows]->(u)}} as followers
            WHERE followers >= {min_followers}
            RETURN u.ricco_id as ricco_id, u.trust_score as trust_score, followers
            ORDER BY followers DESC
            LIMIT {limit};
            """
        
        result = await self.execute(query)
        return self._parse_influencer_result(result)
    
    async def shortest_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 4
    ) -> Optional[List[str]]:
        """
        Encuentra el camino más corto entre dos usuarios.
        
        Args:
            from_id: ID de origen
            to_id: ID de destino
            max_depth: Profundidad máxima
            
        Returns:
            Lista de IDs en el camino, o None si no hay camino
        """
        from_vid = self._sanitize_vid(from_id)
        to_vid = self._sanitize_vid(to_id)
        
        query = f"""
        USE {self.config.space};
        FIND SHORTEST PATH FROM "{from_vid}" TO "{to_vid}"
        OVER follows, friends_with BIDIRECT UPTO {max_depth} STEPS
        YIELD path as p;
        """
        
        result = await self.execute(query)
        return self._parse_path_nodes(result)
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    
    def _sanitize_vid(self, vid: str) -> str:
        """Sanitiza un Vertex ID"""
        return vid.replace('"', '\\"').replace("'", "\\'")
    
    def _get_edge_props(self, edge_type: str) -> str:
        """Obtiene las propiedades de un tipo de edge"""
        props_map = {
            "follows": "since",
            "friends_with": "since, closeness_score",
            "owns": "role, since",
            "trusts": "trust_score, reason, since",
            "referred_by": "reward_claimed, reward_amount",
            "made_transaction": "role",
            "wrote_review": "entity_type",
            "belongs_to_category": "",
            "sold_by": "commission_rate",
            "located_at": "",
            "has_subscription": "plan, started_at, expires_at, active",
            "promotes": "commission_rate, sales_count, total_commission",
            "verified_by": "verification_type, verified_at, expires_at",
            "contains": "quantity, unit_price, total_price",
            "booked_by": "slot_start, slot_end, status",
        }
        return props_map.get(edge_type, "")
    
    def _parse_vertex_result(self, result) -> Optional[Dict]:
        """Parsea resultado de vértice"""
        if not result or not result.is_succeeded():
            return None
        # Implementar parsing según estructura de NebulaGraph
        return {}
    
    def _parse_path_result(self, result) -> Dict:
        """Parsea resultado de path"""
        return {"nodes": [], "edges": []}
    
    def _parse_trust_result(self, result) -> Dict:
        """Parsea resultado de trust network"""
        return {"trust_network": []}
    
    def _parse_list_result(self, result) -> List[Dict]:
        """Parsea resultado de lista"""
        return []
    
    def _parse_recommendation_result(self, result) -> List[Dict]:
        """Parsea resultado de recomendaciones"""
        return []
    
    def _parse_score_result(self, result) -> List[Dict]:
        """Parsea resultado de scores"""
        return []
    
    def _parse_influencer_result(self, result) -> List[Dict]:
        """Parsea resultado de influencers"""
        return []
    
    def _parse_path_nodes(self, result) -> Optional[List[str]]:
        """Parsea nodos de un path"""
        return None


# Singleton para uso global
_nebula_client: Optional[NebulaGraphClient] = None


async def get_nebula_client() -> NebulaGraphClient:
    """Obtiene el cliente de NebulaGraph (singleton)"""
    global _nebula_client
    if _nebula_client is None:
        _nebula_client = NebulaGraphClient()
        await _nebula_client.connect()
    return _nebula_client


# CLI para testing
if __name__ == "__main__":
    async def test():
        client = NebulaGraphClient()
        await client.connect()
        
        # Crear usuario de prueba
        await client.create_user({
            "ricco_id": "RICCO-001",
            "email": "test@ricco.com",
            "trust_score": 85,
            "verification_level": 2,
            "energy_points": 1000,
            "subscription_tier": "torre"
        })
        
        print("Usuario creado exitosamente")
        
        await client.close()
    
    asyncio.run(test())
