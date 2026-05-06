# Plataforma de Gestión de Restaurantes y Delivery - Ricco Food

## 1. Visión General
Una solución integral para la industria gastronómica que unifica la gestión de sala, cocina, inventarios y el canal de ventas online (delivery y pickup), ofreciendo una experiencia sin costuras tanto para el restaurador como para el comensal.

## 2. Arquitectura Técnica
- **Core Engine:** Frappe Framework + ERPNext + `tmp_apps/erpnext-restaurant`.
- **Canal de Venta Online:** MedusaJS (para el Storefront de pedidos y menús digitales).
- **Interfaz de Operación:** POSNext optimizado para hostelería.
- **Dominio Sugerido:** `food.ricco.com`

## 3. Aplicaciones de Frappe Recomendadas (incluyendo tmp_apps/)
- **erpnext-restaurant (tmp_apps/):** Gestión de mesas, división de cuentas, comandas de cocina y menús por horario.
- **URY (marketplace_docs/):** Interfaz POS avanzada para restaurantes con soporte para múltiples terminales.
- **inventory (ERPNext core):** Control de mermas, recetas (BOM de platillos) y compras a proveedores.
- **erpnext-shipping (tmp_apps/):** Coordinación con repartidores propios o externos para el delivery.
- **newsletter:** Envío de menús del día y promociones especiales.

## 4. Funcionalidades Gastronómicas
- **Menú Digital & QR:** Los comensales escanean un código en la mesa para ver el menú y pedir directamente desde su móvil (`Scan_Me`).
- **Kitchen Display System (KDS):** Pantallas en cocina que muestran los pedidos en tiempo real con tiempos de preparación.
- **Gestión de Delivery:** Portal para que los repartidores reciban órdenes, calculen rutas y marquen entregas.
- **Control de Insumos:** Descuento automático de ingredientes del inventario al vender un platillo (basado en recetas).

## 5. Integración de IA Agéntica
- **n8n / Flowise:**
    - **Recomendador de Platos:** IA que sugiere platos basados en pedidos anteriores y preferencias dietéticas del usuario en `Ricco Social`.
    - **Optimizador de Inventario:** Agente que predice la demanda de ingredientes según el día de la semana y eventos locales para evitar desperdicios.
    - **Gestión de Reservas Inteligente:** Chatbot que gestiona reservas de mesas y optimiza la ocupación de la sala.
- **Evo-AI:** Análisis de reseñas de clientes (`Product Reviews`) para identificar áreas de mejora en el servicio o la comida.

## 6. Estrategias de Monetización y FOMO
- **Tarifa por Pedido de Delivery:** Comisión por el uso del canal de ventas online.
- **Suscripciones para Negocios:** Planes mensuales para el uso del software de gestión y POS.
- **Publicidad de Restaurantes:** Posicionamiento destacado en la app de `Ricco SuperApp`.
- **FOMO (Platos de Edición Limitada):** Ofertas de "Sólo por hoy" o "Quedan 5 porciones de este especial" enviadas vía notificación push.

## 7. Flujo de Trabajo (Workflow)
1. El restaurante configura su menú y recetas en `erpnext-restaurant`.
2. El cliente pide vía `food.ricco.com` (delivery) o escaneando QR en mesa (comedor).
3. La comanda aparece instantáneamente en el KDS de cocina.
4. El POS registra la venta y descuenta insumos.
5. Se procesa el pago (integrado con `payments`) y se acumulan puntos en el sistema de gamificación.
