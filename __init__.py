"""
RICCO AI Service - Integración completa
ERPNext + NebulaGraph + Flowise + n8n
"""

from typing import Dict, List, Optional, Any
import asyncio

# Importar clientes
from .erpnext_integration.erpnext_service import (
    ERPNextIntegration,
    ERPNextConfig,
    RICCOWebhooks
)
from .nebula.nebula_client import (
    NebulaGraphClient,
    NebulaConfig,
    get_nebula_client
)
from .flowise.flowise_client import (
    FlowiseClient,
    FlowiseConfig,
    RICCOChatflows
)


class RICCOAIOrchestrator:
    """
    Orquestador principal de IA para el ecosistema RICCO.
    
    Coordina:
    - ERPNext: Gestión empresarial y ERP
    - NebulaGraph: Social Graph y relaciones
    - Flowise: LLM flows y chatbots
    - n8n: Automatizaciones y workflows
    """
    
    def __init__(self):
        # Inicializar clientes
        self.erpnext = ERPNextIntegration()
        self.nebula: Optional[NebulaGraphClient] = None
        self.flowise = FlowiseClient()
        self.chatflows = RICCOChatflows(self.flowise)
        self.webhooks = RICCOWebhooks()
    
    async def initialize(self):
        """Inicializa todas las conexiones"""
        # Conectar a NebulaGraph
        self.nebula = await get_nebula_client()
        print("✓ NebulaGraph conectado")
        print("✓ ERPNext configurado")
        print("✓ Flowise configurado")
    
    # ========================================
    # OPERACIONES DE USUARIO
    # ========================================
    
    async def register_user(self, user_data: Dict) -> Dict:
        """
        Registro completo de usuario en todo el ecosistema.
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            Resultado del registro
        """
        results = {}
        
        # 1. Crear en NebulaGraph (Social Graph)
        try:
            await self.nebula.create_user(user_data)
            results["nebula"] = {"status": "created", "ricco_id": user_data["ricco_id"]}
        except Exception as e:
            results["nebula"] = {"status": "error", "message": str(e)}
        
        # 2. Sincronizar con ERPNext (Customer)
        try:
            customer = self.erpnext.sync_user_to_customer(user_data)
            results["erpnext"] = {"status": "synced", "customer_id": customer.get("name")}
        except Exception as e:
            results["erpnext"] = {"status": "error", "message": str(e)}
        
        # 3. Crear suscripción inicial (Peón)
        try:
            subscription = self.erpnext.create_customer_subscription(
                user_data["ricco_id"],
                "peon"
            )
            results["subscription"] = {"status": "created", "tier": "peon"}
        except Exception as e:
            results["subscription"] = {"status": "error", "message": str(e)}
        
        return results
    
    async def register_business(self, business_data: Dict, owner_id: str) -> Dict:
        """
        Registro completo de negocio en el ecosistema.
        
        Args:
            business_data: Datos del negocio
            owner_id: RICCO ID del propietario
            
        Returns:
            Resultado del registro
        """
        results = {}
        
        # 1. Crear nodo de negocio en NebulaGraph
        try:
            await self.nebula.create_business(business_data)
            results["nebula_business"] = {"status": "created"}
        except Exception as e:
            results["nebula_business"] = {"status": "error", "message": str(e)}
        
        # 2. Crear relación de propiedad
        try:
            await self.nebula.create_relationship(
                owner_id,
                business_data["business_id"],
                "owns",
                {"role": "owner"}
            )
            results["nebula_relation"] = {"status": "created"}
        except Exception as e:
            results["nebula_relation"] = {"status": "error", "message": str(e)}
        
        # 3. Sincronizar con ERPNext (Supplier)
        try:
            supplier = self.erpnext.sync_business_to_supplier(business_data)
            results["erpnext"] = {"status": "synced", "supplier_id": supplier.get("name")}
        except Exception as e:
            results["erpnext"] = {"status": "error", "message": str(e)}
        
        return results
    
    # ========================================
    # OPERACIONES DE COMERCIO
    # ========================================
    
    async def process_order(self, order_data: Dict) -> Dict:
        """
        Procesa una orden en todo el ecosistema.
        
        Args:
            order_data: Datos de la orden
            
        Returns:
            Resultado del procesamiento
        """
        results = {}
        
        # 1. Crear transacción en NebulaGraph
        try:
            await self.nebula.create_relationship(
                order_data["user_id"],
                order_data["order_id"],
                "made_transaction",
                {"role": "buyer"}
            )
            results["nebula"] = {"status": "recorded"}
        except Exception as e:
            results["nebula"] = {"status": "error", "message": str(e)}
        
        # 2. Crear Sales Order en ERPNext
        try:
            sales_order = self.erpnext.create_sales_order_from_ricco(order_data)
            results["erpnext"] = {"status": "created", "order_id": sales_order.get("name")}
        except Exception as e:
            results["erpnext"] = {"status": "error", "message": str(e)}
        
        # 3. Si es dropshipping, crear Purchase Orders
        if order_data.get("is_dropshipping"):
            try:
                po_list = self.erpnext.create_purchase_order_for_dropshipping(order_data)
                results["purchase_orders"] = {
                    "status": "created",
                    "count": len(po_list),
                    "po_ids": [po.get("name") for po in po_list]
                }
            except Exception as e:
                results["purchase_orders"] = {"status": "error", "message": str(e)}
        
        return results
    
    # ========================================
    # OPERACIONES DE BOOKING
    # ========================================
    
    async def process_booking(self, booking_data: Dict) -> Dict:
        """
        Procesa una reserva en todo el ecosistema.
        
        Args:
            booking_data: Datos de la reserva
            
        Returns:
            Resultado del procesamiento
        """
        results = {}
        
        # 1. Registrar en NebulaGraph
        try:
            await self.nebula.create_relationship(
                booking_data["user_id"],
                booking_data["service_id"],
                "booked_by",
                {
                    "slot_start": booking_data.get("slot_start"),
                    "slot_end": booking_data.get("slot_end"),
                    "status": "confirmed"
                }
            )
            results["nebula"] = {"status": "recorded"}
        except Exception as e:
            results["nebula"] = {"status": "error", "message": str(e)}
        
        # 2. Crear Sales Order en ERPNext
        try:
            sales_order = self.erpnext.create_booking_as_sales_order(booking_data)
            results["erpnext"] = {"status": "created", "order_id": sales_order.get("name")}
        except Exception as e:
            results["erpnext"] = {"status": "error", "message": str(e)}
        
        return results
    
    # ========================================
    # OPERACIONES DE TRUST
    # ========================================
    
    async def calculate_trust_score(self, ricco_id: str) -> Dict:
        """
        Calcula y actualiza el Trust Score de un usuario.
        
        Args:
            ricco_id: ID del usuario
            
        Returns:
            Trust score calculado
        """
        # Obtener score desde NebulaGraph
        trust_score = await self.nebula.calculate_trust_score(ricco_id)
        
        # Actualizar en ERPNext
        try:
            self.webhooks.on_user_updated({
                "ricco_id": ricco_id,
                "trust_score": trust_score
            })
        except Exception:
            pass
        
        return {
            "ricco_id": ricco_id,
            "trust_score": trust_score,
            "level": self._get_trust_level(trust_score)
        }
    
    async def establish_trust(
        self,
        from_user: str,
        to_user: str,
        trust_score: int,
        reason: str = ""
    ) -> Dict:
        """
        Establece una relación de confianza entre usuarios.
        
        Args:
            from_user: Usuario que otorga confianza
            to_user: Usuario que recibe confianza
            trust_score: Score de confianza (1-100)
            reason: Razón de la confianza
            
        Returns:
            Resultado de la operación
        """
        # Crear edge de confianza en NebulaGraph
        await self.nebula.create_relationship(
            from_user,
            to_user,
            "trusts",
            {
                "trust_score": trust_score,
                "reason": reason
            }
        )
        
        # Recalcular trust score del destinatario
        new_score = await self.nebula.calculate_trust_score(to_user)
        
        return {
            "status": "established",
            "from": from_user,
            "to": to_user,
            "granted_score": trust_score,
            "new_trust_score": new_score
        }
    
    # ========================================
    # OPERACIONES DE RECOMENDACIÓN
    # ========================================
    
    async def get_personalized_recommendations(
        self,
        ricco_id: str,
        recommendation_type: str = "users"
    ) -> List[Dict]:
        """
        Obtiene recomendaciones personalizadas basadas en el Social Graph.
        
        Args:
            ricco_id: ID del usuario
            recommendation_type: Tipo (users, products, businesses)
            
        Returns:
            Lista de recomendaciones
        """
        # Obtener recomendaciones del grafo
        recommendations = await self.nebula.get_recommendations(
            ricco_id,
            recommendation_type
        )
        
        # Enriquecer con IA
        if recommendations:
            enriched = await self.chatflows.business_analyst(
                ricco_id,
                f"Personalizar recomendaciones de tipo {recommendation_type}",
                {"recommendations": recommendations}
            )
            return {
                "graph_recommendations": recommendations,
                "ai_insights": enriched
            }
        
        return {"recommendations": recommendations}
    
    # ========================================
    # CHAT INTELIGENTE
    # ========================================
    
    async def smart_chat(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Chat inteligente que usa contexto del usuario.
        
        Args:
            user_id: ID del usuario
            message: Mensaje del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta del chat
        """
        # Obtener contexto del usuario desde NebulaGraph
        user_data = await self.nebula.get_user(user_id)
        trust_network = await self.nebula.get_trust_network(user_id)
        
        # Construir contexto completo
        full_context = {
            "user": user_data,
            "trust_network": trust_network,
            "custom_context": context or {}
        }
        
        # Determinar el tipo de chatflow a usar
        chatflow_type = self._determine_chatflow(message, context)
        
        # Ejecutar chatflow apropiado
        if chatflow_type == "commerce":
            return await self.chatflows.commerce_assistant(
                user_id, message, full_context
            )
        elif chatflow_type == "booking":
            return await self.chatflows.booking_assistant(
                user_id, message, context.get("industry")
            )
        elif chatflow_type == "support":
            return await self.chatflows.support_agent(
                user_id, message, context.get("ticket_history")
            )
        elif chatflow_type == "analyst":
            return await self.chatflows.business_analyst(
                user_id, message, full_context
            )
        else:
            return await self.chatflows.commerce_assistant(
                user_id, message, full_context
            )
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    
    def _get_trust_level(self, score: int) -> str:
        """Obtiene el nivel de confianza basado en el score"""
        if score < 30:
            return "riesgo_alto"
        elif score < 50:
            return "riesgo_medio"
        elif score < 70:
            return "confianza_basica"
        elif score < 85:
            return "buena_reputacion"
        else:
            return "excelente_reputacion"
    
    def _determine_chatflow(self, message: str, context: Optional[Dict]) -> str:
        """Determina el tipo de chatflow basado en el mensaje"""
        message_lower = message.lower()
        
        # Palabras clave para cada tipo
        commerce_keywords = ["comprar", "producto", "precio", "oferta", "tienda"]
        booking_keywords = ["reservar", "cita", "turno", "hora", "disponible"]
        support_keywords = ["ayuda", "problema", "error", "no funciona", "soporte"]
        analyst_keywords = ["ventas", "análisis", "reporte", "estadísticas", "métricas"]
        
        if any(kw in message_lower for kw in commerce_keywords):
            return "commerce"
        elif any(kw in message_lower for kw in booking_keywords):
            return "booking"
        elif any(kw in message_lower for kw in support_keywords):
            return "support"
        elif any(kw in message_lower for kw in analyst_keywords):
            return "analyst"
        else:
            return "commerce"


# Singleton
_orchestrator: Optional[RICCOAIOrchestrator] = None


async def get_orchestrator() -> RICCOAIOrchestrator:
    """Obtiene el orquestador de IA (singleton)"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RICCOAIOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


# Exportar todo
__all__ = [
    "RICCOAIOrchestrator",
    "ERPNextIntegration",
    "NebulaGraphClient",
    "FlowiseClient",
    "RICCOChatflows",
    "get_orchestrator",
    "get_nebula_client",
]
