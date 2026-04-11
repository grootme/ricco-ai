"""
RICCO Ecosystem - Flowise AI Integration
Low-code LLM flow builder para el ecosistema
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class FlowiseConfig:
    """Configuración de Flowise"""
    base_url: str = os.getenv("FLOWISE_URL", "http://localhost:3001")
    api_key: str = os.getenv("FLOWISE_API_KEY", "")
    username: str = os.getenv("FLOWISE_USERNAME", "admin")
    password: str = os.getenv("FLOWISE_PASSWORD", "")


class FlowiseClient:
    """
    Cliente para interactuar con Flowise AI.
    
    Proporciona:
    - Chat completions con flujos personalizados
    - Gestión de chatflows
    - Streaming responses
    - Integración con RAG
    """
    
    def __init__(self, config: Optional[FlowiseConfig] = None):
        self.config = config or FlowiseConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        if self.config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}"
            })
    
    # ========================================
    # CHAT OPERATIONS
    # ========================================
    
    def chat(
        self,
        chatflow_id: str,
        message: str,
        history: Optional[List[Dict]] = None,
        override_config: Optional[Dict] = None
    ) -> Dict:
        """
        Envía un mensaje a un chatflow específico.
        
        Args:
            chatflow_id: ID del chatflow en Flowise
            message: Mensaje del usuario
            history: Historial de conversación
            override_config: Configuración para sobrescribir
            
        Returns:
            Respuesta del chatflow
        """
        url = f"{self.config.base_url}/api/v1/prediction/{chatflow_id}"
        
        payload = {
            "question": message,
            "history": history or [],
        }
        
        if override_config:
            payload["overrideConfig"] = override_config
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    async def chat_stream(
        self,
        chatflow_id: str,
        message: str,
        history: Optional[List[Dict]] = None,
        override_config: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streaming de respuesta desde un chatflow.
        
        Args:
            chatflow_id: ID del chatflow
            message: Mensaje del usuario
            history: Historial de conversación
            override_config: Configuración para sobrescribir
            
        Yields:
            Chunks de la respuesta
        """
        url = f"{self.config.base_url}/api/v1/prediction/{chatflow_id}"
        
        payload = {
            "question": message,
            "history": history or [],
            "streaming": True
        }
        
        if override_config:
            payload["overrideConfig"] = override_config
        
        async with asyncio.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                async for line in response.content:
                    if line:
                        yield line.decode("utf-8")
    
    # ========================================
    # CHATFLOW MANAGEMENT
    # ========================================
    
    def list_chatflows(self) -> List[Dict]:
        """Lista todos los chatflows"""
        url = f"{self.config.base_url}/api/v1/chatflows"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_chatflow(self, chatflow_id: str) -> Dict:
        """Obtiene un chatflow específico"""
        url = f"{self.config.base_url}/api/v1/chatflows/{chatflow_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_chatflow(self, chatflow_data: Dict) -> Dict:
        """Crea un nuevo chatflow"""
        url = f"{self.config.base_url}/api/v1/chatflows"
        response = self.session.post(url, json=chatflow_data)
        response.raise_for_status()
        return response.json()
    
    def update_chatflow(self, chatflow_id: str, chatflow_data: Dict) -> Dict:
        """Actualiza un chatflow existente"""
        url = f"{self.config.base_url}/api/v1/chatflows/{chatflow_id}"
        response = self.session.put(url, json=chatflow_data)
        response.raise_for_status()
        return response.json()
    
    def delete_chatflow(self, chatflow_id: str) -> bool:
        """Elimina un chatflow"""
        url = f"{self.config.base_url}/api/v1/chatflows/{chatflow_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        return True


# ========================================
# RICCO CHATFLOWS PREDEFINIDOS
# ========================================

class RICCOChatflows:
    """
    Chatflows predefinidos para el ecosistema RICCO.
    Cada chatflow está optimizado para un caso de uso específico.
    """
    
    # IDs de chatflows (se configuran en Flowise)
    CHATFLOWS = {
        "commerce_assistant": "COMMERCE_CHATFLOW_ID",
        "booking_assistant": "BOOKING_CHATFLOW_ID",
        "support_agent": "SUPPORT_CHATFLOW_ID",
        "business_analyst": "ANALYST_CHATFLOW_ID",
        "trust_verifier": "TRUST_CHATFLOW_ID",
        "onboarding_guide": "ONBOARDING_CHATFLOW_ID",
    }
    
    def __init__(self, client: Optional[FlowiseClient] = None):
        self.client = client or FlowiseClient()
    
    async def commerce_assistant(
        self,
        user_id: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Asistente de comercio con contexto personalizado.
        
        Args:
            user_id: ID del usuario RICCO
            query: Consulta del usuario
            context: Contexto adicional (productos, historial, etc.)
            
        Returns:
            Respuesta del asistente
        """
        chatflow_id = os.getenv(self.CHATFLOWS["commerce_assistant"])
        
        override_config = {
            "userId": user_id,
            "context": context or {},
            "systemPrompt": self._build_commerce_system_prompt(context)
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    async def booking_assistant(
        self,
        user_id: str,
        query: str,
        industry: Optional[str] = None
    ) -> Dict:
        """
        Asistente de reservas especializado por industria.
        
        Args:
            user_id: ID del usuario
            query: Consulta de reserva
            industry: Industria (car_wash, beauty, health, etc.)
            
        Returns:
            Respuesta con opciones de reserva
        """
        chatflow_id = os.getenv(self.CHATFLOWS["booking_assistant"])
        
        override_config = {
            "userId": user_id,
            "industry": industry,
            "systemPrompt": self._build_booking_system_prompt(industry)
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    async def support_agent(
        self,
        user_id: str,
        query: str,
        ticket_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Agente de soporte con acceso a conocimiento.
        
        Args:
            user_id: ID del usuario
            query: Consulta o problema
            ticket_history: Historial de tickets previos
            
        Returns:
            Respuesta de soporte
        """
        chatflow_id = os.getenv(self.CHATFLOWS["support_agent"])
        
        override_config = {
            "userId": user_id,
            "ticketHistory": ticket_history or [],
            "systemPrompt": self._build_support_system_prompt()
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    async def business_analyst(
        self,
        business_id: str,
        query: str,
        data_context: Optional[Dict] = None
    ) -> Dict:
        """
        Analista de negocios con datos del negocio.
        
        Args:
            business_id: ID del negocio
            query: Consulta analítica
            data_context: Datos del negocio (ventas, productos, etc.)
            
        Returns:
            Análisis y recomendaciones
        """
        chatflow_id = os.getenv(self.CHATFLOWS["business_analyst"])
        
        override_config = {
            "businessId": business_id,
            "dataContext": data_context or {},
            "systemPrompt": self._build_analyst_system_prompt(data_context)
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    async def trust_verifier(
        self,
        entity_id: str,
        entity_type: str,
        verification_data: Dict
    ) -> Dict:
        """
        Verificador de confianza con análisis de riesgo.
        
        Args:
            entity_id: ID de la entidad (usuario o negocio)
            entity_type: Tipo (user, business)
            verification_data: Datos para verificación
            
        Returns:
            Análisis de confianza y recomendaciones
        """
        chatflow_id = os.getenv(self.CHATFLOWS["trust_verifier"])
        
        query = f"Verificar entidad {entity_type} con ID {entity_id}"
        
        override_config = {
            "entityId": entity_id,
            "entityType": entity_type,
            "verificationData": verification_data,
            "systemPrompt": self._build_trust_system_prompt()
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    async def onboarding_guide(
        self,
        user_id: str,
        step: int,
        user_type: str = "merchant"
    ) -> Dict:
        """
        Guía de onboarding personalizada.
        
        Args:
            user_id: ID del usuario
            step: Paso actual del onboarding
            user_type: Tipo de usuario (merchant, customer, agent)
            
        Returns:
            Guía del paso actual
        """
        chatflow_id = os.getenv(self.CHATFLOWS["onboarding_guide"])
        
        query = f"Guía paso {step} para {user_type}"
        
        override_config = {
            "userId": user_id,
            "step": step,
            "userType": user_type,
            "systemPrompt": self._build_onboarding_system_prompt(user_type, step)
        }
        
        return self.client.chat(chatflow_id, query, override_config=override_config)
    
    # ========================================
    # SYSTEM PROMPTS
    # ========================================
    
    def _build_commerce_system_prompt(self, context: Optional[Dict]) -> str:
        """Construye el prompt del sistema para comercio"""
        return """Eres el Asistente de Comercio RICCO, un experto en ayudar a usuarios 
        a encontrar productos, comparar opciones y realizar compras en el ecosistema RICCO.
        
        Capacidades:
        - Búsqueda inteligente de productos
        - Comparación de precios y características
        - Recomendaciones personalizadas basadas en historial
        - Asistencia en proceso de checkout
        - Información sobre Energy Points y descuentos
        
        Reglas:
        - Siempre verificar la disponibilidad antes de recomendar
        - Ofrecer alternativas si el producto no está disponible
        - Mencionar beneficios de suscripción cuando sea relevante
        - Ser amable y servicial
        """
    
    def _build_booking_system_prompt(self, industry: Optional[str]) -> str:
        """Construye el prompt del sistema para reservas"""
        industry_prompts = {
            "car_wash": "Eres experto en servicios de lavado de autos.",
            "beauty": "Eres experto en servicios de belleza y peluquería.",
            "health": "Eres experto en servicios de salud y consultas médicas.",
            "repairs": "Eres experto en servicios de reparaciones técnicas.",
            "gym": "Eres experto en servicios de gimnasio y fitness.",
            "parking": "Eres experto en servicios de estacionamiento.",
            "rentals_auto": "Eres experto en renta de vehículos.",
            "rentals_space": "Eres experto en renta de espacios y locales.",
            "lodging": "Eres experto en hospedaje y hotelería.",
        }
        
        base_prompt = f"""
        Eres el Asistente de Reservas RICCO. {industry_prompts.get(industry, '')}
        
        Capacidades:
        - Verificar disponibilidad de horarios
        - Calcular precios según la fórmula: (Precio Base × Factor Tiempo) + Extras
        - Explicar políticas de cancelación
        - Confirmar reservas
        - Gestionar modificaciones
        
        Fórmula de precio universal:
        Valor Total = (Precio Base × Factor Tiempo) + Extras
        """
        
        return base_prompt
    
    def _build_support_system_prompt(self) -> str:
        """Construye el prompt del sistema para soporte"""
        return """Eres el Agente de Soporte RICCO, especializado en resolver problemas 
        de usuarios del ecosistema RICCO.
        
        Capacidades:
        - Resolución de problemas técnicos
        - Gestión de reclamos
        - Información sobre políticas
        - Escalamiento a humanos cuando sea necesario
        - Seguimiento de tickets
        
        Reglas:
        - Siempre ser empático y paciente
        - Verificar identidad antes de dar información sensible
        - Documentar cada interacción
        - Ofrecer soluciones, no solo excusas
        - Escalar problemas complejos al equipo especializado
        """
    
    def _build_analyst_system_prompt(self, data_context: Optional[Dict]) -> str:
        """Construye el prompt del sistema para análisis"""
        return """Eres el Analista de Negocios RICCO, un experto en análisis de datos 
        y estrategias comerciales para comerciantes del ecosistema.
        
        Capacidades:
        - Análisis de ventas y tendencias
        - Recomendaciones de pricing
        - Optimización de inventario
        - Estrategias de marketing
        - Predicción de demanda
        
        Tipos de análisis:
        - Ventas por período
        - Productos más vendidos
        - Clientes recurrentes
        - Margen de ganancia
        - Oportunidades de crecimiento
        """
    
    def _build_trust_system_prompt(self) -> str:
        """Construye el prompt del sistema para verificación"""
        return """Eres el Verificador de Confianza RICCO, especializado en evaluar 
        la confiabilidad de usuarios y negocios en el ecosistema.
        
        Factores de evaluación:
        - Historial de transacciones
        - Reseñas y calificaciones
        - Verificación de identidad
        - Tiempo en la plataforma
        - Cumplimiento de políticas
        
        Niveles de Trust Score:
        - 0-30: Riesgo alto - Requiere precaución
        - 31-50: Riesgo medio - Verificación recomendada
        - 51-70: Confianza básica - Transacciones normales
        - 71-85: Buena reputación - Beneficios adicionales
        - 86-100: Excelente reputación - Máxima confianza
        """
    
    def _build_onboarding_system_prompt(self, user_type: str, step: int) -> str:
        """Construye el prompt del sistema para onboarding"""
        return f"""Eres la Guía de Onboarding RICCO, especializada en ayudar a nuevos 
        {user_type}s a configurar su cuenta y comenzar a usar el ecosistema.
        
        Pasos de onboarding para {user_type}:
        1. Bienvenida y explicación del ecosistema
        2. Configuración de perfil
        3. Verificación de identidad
        4. Configuración de pagos
        5. Primer producto/servicio
        6. Tutorial de uso
        
        Estás en el paso {step}. Sé claro, paciente y motivador.
        """


# ========================================
# FLOWISE CHATFLOW TEMPLATES
# ========================================

CHATFLOW_TEMPLATES = {
    "commerce_assistant": {
        "name": "RICCO Commerce Assistant",
        "description": "Asistente de compras para el marketplace RICCO",
        "nodes": [
            {
                "type": "chatInput",
                "id": "chatInput",
                "position": {"x": 100, "y": 200}
            },
            {
                "type": "openRouter",
                "id": "llm",
                "position": {"x": 400, "y": 200},
                "data": {
                    "model": "anthropic/claude-3.5-sonnet",
                    "temperature": 0.7
                }
            },
            {
                "type": "qdrant",
                "id": "vectorStore",
                "position": {"x": 400, "y": 400},
                "data": {
                    "collection": "ricco_products"
                }
            },
            {
                "type": "chatOutput",
                "id": "chatOutput",
                "position": {"x": 700, "y": 200}
            }
        ],
        "edges": [
            {"source": "chatInput", "target": "llm"},
            {"source": "vectorStore", "target": "llm"},
            {"source": "llm", "target": "chatOutput"}
        ]
    },
    
    "booking_assistant": {
        "name": "RICCO Booking Assistant",
        "description": "Asistente de reservas multi-industria",
        "nodes": [
            {
                "type": "chatInput",
                "id": "chatInput",
                "position": {"x": 100, "y": 200}
            },
            {
                "type": "openRouter",
                "id": "llm",
                "position": {"x": 400, "y": 200},
                "data": {
                    "model": "anthropic/claude-3.5-sonnet",
                    "temperature": 0.5
                }
            },
            {
                "type": "customTool",
                "id": "availabilityChecker",
                "position": {"x": 400, "y": 400},
                "data": {
                    "functionName": "check_availability",
                    "description": "Verifica disponibilidad de slots"
                }
            },
            {
                "type": "chatOutput",
                "id": "chatOutput",
                "position": {"x": 700, "y": 200}
            }
        ],
        "edges": [
            {"source": "chatInput", "target": "llm"},
            {"source": "availabilityChecker", "target": "llm"},
            {"source": "llm", "target": "chatOutput"}
        ]
    }
}


# CLI para testing
if __name__ == "__main__":
    client = FlowiseClient()
    
    # Listar chatflows
    try:
        chatflows = client.list_chatflows()
        print(f"Chatflows disponibles: {len(chatflows)}")
        for cf in chatflows:
            print(f"  - {cf.get('name')}: {cf.get('id')}")
    except Exception as e:
        print(f"Error conectando a Flowise: {e}")
        print("Asegúrate de que Flowise esté corriendo en http://localhost:3001")
