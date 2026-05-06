# Plataforma de Gestión de Gimnasios - Ricco Gym

## 1. Visión General
Una solución integral para la administración de centros de fitness, gimnasios y boxes de entrenamiento, centrada en el control de acceso, gestión de membresías y seguimiento del progreso de los socios.

## 2. Arquitectura Técnica
- **Core Engine:** Frappe Framework + ERPNext (Gestión administrativa y financiera).
- **Tienda Interna/Membresías:** MedusaJS (para gestionar planes de membresía, productos y suplementos).
- **Control de Acceso:** Integración directa con hardware biométrico y torniquetes.
- **Frontend App:** Aplicación móvil (PWA) para que los socios vean sus rutinas, reserven clases y marquen asistencia.
- **Dominio Sugerido:** `gym.ricco.com`

## 3. Aplicaciones de Frappe Recomendadas (marketplace_docs/)
- **Gym_Management / Gym_Pro:** El corazón de la plataforma para gestionar socios, planes y clases.
- **Simple_Subscription / Contract_Payment:** Facturación automática y recurrente de mensualidades.
- **Biometric_Integration_(Hikvision) / ZKTeco_Checkin_Sync / Cams_Biometrics_Integration:** Sincronización de asistencia y apertura de puertas física.
- **QRBarcode_Check-In-Out:** Para check-in mediante códigos QR desde la App móvil del socio.
- **Attendance_and_Timesheet / Attendance_Sync:** Reportes detallados de asistencia de socios y entrenadores.
- **HR_&_Payroll / HR_Addon:** Gestión de entrenadores, nutricionistas y personal administrativo.
- **Payments / Frappe_Paystack:** Cobros automáticos a tarjetas de crédito/débito.
- **FCM_Notification:** Notificaciones masivas de nuevas clases o recordatorios de vencimiento de plan.
- **Webshop:** Para la tienda interna de suplementos y ropa deportiva, integrada con Medusa.

## 4. Integración de IA Agéntica
- **n8n / Flowise:**
    - "AI Personal Trainer": Generación automática de planes de entrenamiento basados en el perfil y objetivos del socio.
    - Chatbot de atención al cliente para preguntas frecuentes sobre planes y horarios.
    - Alertas inteligentes de deserción (IA detecta cuando un socio deja de asistir y envía promociones de reenganche).
- **Evo-AI:** Análisis de rendimiento corporal y sugerencias nutricionales inteligentes.

## 5. Ejemplos de MedusaJS Integrados (Ideas)
- **Subscriptions:** Gestionar la venta de membresías del gimnasio con pagos recurrentes (Medusa `Subscriptions`). Se sincroniza con `Simple_Subscription` en Frappe.
- **Customer Tiers:** Crear diferentes niveles de membresía (ej. estándar, premium, VIP) con acceso a diferentes servicios o descuentos (Medusa `Customer Tiers`). Se mapea con Grupos de Clientes en ERPNext.
- **Loyalty Points System:** Implementar un programa de puntos para recompensar a los socios por asistencia, referidos o compras en la tienda (Medusa `Loyalty Points System`).
- **Product Reviews:** Permitir a los socios dejar reseñas sobre clases, entrenadores o productos de la tienda (Medusa `Product Reviews`).
- **Personalized Products:** Ofrecer planes de entrenamiento o paquetes de nutrición personalizados que se configuran y pagan a través de Medusa (Medusa `Personalized Products` / `Product Builder`). Los detalles se guardan en DocTypes de Frappe.
- **First-Purchase Discounts:** Atraer nuevos socios con descuentos en su primera membresía o compra de suplementos (Medusa `First-Purchase Discounts`).
- **Localization with Contentful/Sanity/Strapi/Payload Integration:** Gestionar el contenido multi-idioma de la web y la app del gimnasio (Medusa `Localization with Contentful Integration`, `Sanity Integration`, `Strapi Integration`, `Payload Integration`).
- **Product Feed:** Generar feeds de productos (membresías, suplementos) para marketing digital (Medusa `Product Feed`).
- **Pre-orders:** Permitir la pre-inscripción a eventos o clases especiales con cupos limitados (Medusa `Pre-orders`).

## 6. Estrategias de Monetización y FOMO
- **Membresías por Niveles:** La venta de suscripciones (`Subscriptions`) con `Customer Tiers` ofrece diferentes beneficios a precios escalonados (ej. acceso 24/7, clases VIP).
- **Tienda Interna:** Venta de suplementos, ropa y equipos deportivos a través de `Webshop` (gestionado por Medusa).
- **Servicios Premium:** Sesiones con "AI Personal Trainer" o planes de nutrición personalizados (`Personalized Products`) como servicios de pago único o recurrente.
- **FOMO (Cupos Limitados / Ofertas Flash):** Mostrar la disponibilidad de cupos en clases populares y enviar notificaciones (`FCM_Notification`) de ofertas relámpago en membresías o productos con tiempo limitado.
- **Descuentos por Primera Compra:** `First-Purchase Discounts` para nuevos socios, creando un incentivo inicial.
- **Puntos de Lealtad:** Los `Loyalty Points` incentivan la continuidad y el gasto dentro del ecosistema Ricco Gym.

## 7. Experiencia del Socio
- Dashboard personal con historial de entrenamientos y medidas corporales.
- Reserva de clases grupales (Spinning, Yoga, Crossfit) con cupos limitados.
- Tienda interna de suplementos y ropa deportiva (`Webshop`).

## 8. Flujo de Trabajo (Workflow Mejorado)
1. El socio se registra en `gym.ricco.com`, elige su `Subscriptions` plan o compra productos en la tienda (`Webshop`). Aplica `First-Purchase Discounts` si es nuevo.
2. Realiza el pago (`Stripe Saved Payment Methods`) y recibe su código QR de acceso (`QRBarcode_Check-In-Out`). Acumula `Loyalty Points`.
3. Se presenta en el gimnasio, escanea su QR/huella; el sistema valida la membresía activa (`Subscriptions`, `Customer Tiers`) y abre el acceso.
4. La IA le sugiere su rutina del día (`Personalized Products`). Puede dejar `Product Reviews`.
5. El sistema envía un recordatorio de renovación 5 días antes del vencimiento (`FCM_Notification`) e incentiva la continuidad con `Loyalty Points`.
