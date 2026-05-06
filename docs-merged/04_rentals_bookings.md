# Plataforma de Rentas y Reservas (Spaces, Car Wash, Eventos, Belleza) - Ricco Booking

## 1. Visión General
Una plataforma unificada para el agendamiento de servicios (salones de belleza, lavaderos de autos) y la renta de espacios (salas de reuniones, locales, eventos), con gestión de calendarios en tiempo real y pagos integrados.

## 2. Arquitectura Técnica
- **Core Engine:** Frappe Framework con módulos especializados de Reservas y Activos, y MedusaJS para gestión de ofertas y suscripciones.
- **Gestor de Calendarios:** FullCalendar integrado en Frappe o integración externa con Google/Outlook Calendar.
- **Frontend App:** PWA móvil para usuarios finales y dashboard para proveedores de servicios.
- **CMS Corporativo:** Go1_CMS.
- **Dominio Sugerido:** `booking.ricco.com`

## 3. Aplicaciones de Frappe Recomendadas (marketplace_docs/)
- **Rental_Management:** Base para la renta de activos físicos o espacios.
- **Property_Management:** Específica para la gestión de locales, oficinas y salas de eventos.
- **Appointment_Booking_Management / Frappe_Appointment:** Motor para agendar turnos en salones de belleza y consultorios.
- **Car_Reservation:** Ideal para el servicio de lavadero de carros y renta de vehículos.
- **Utility_&_Rental_Billing:** Facturación recurrente para rentas a largo plazo.
- **Payroll_LavaDo:** Gestión de nómina y productividad para el personal operativo (lavadores, estilistas).
- **Holidays / Working_Time:** Configuración de horarios de apertura y disponibilidad de staff.
- **Payments / IPCONNEX_Stripe_Payment:** Cobro de adelantos para asegurar la reserva.
- **FCM_Notification / Twilio / Frappe_WhatsApp:** Recordatorios automáticos para evitar inasistencias (no-shows).

## 4. Integración de IA Agéntica
- **n8n / Flowise:**
    - Asistente virtual vía WhatsApp para agendar turnos de forma conversacional (sin intervención humana).
    - Optimización inteligente de calendarios (IA sugiere llenar "huecos" vacíos con promociones).
    - Detección automática de conflictos de horarios.
- **Evo-AI:** Análisis de demanda predictiva para ajustar precios dinámicamente según la hora y el día.

## 5. Ejemplos de MedusaJS Integrados (Ideas)
- **Product Rentals:** Utilizar Medusa para definir y gestionar los productos o servicios que se pueden rentar o reservar, con control de disponibilidad y tarifas (Medusa `Product Rentals`). Se integra con `Rental_Management` y `Property_Management` de Frappe.
- **Ticket Booking System:** Implementar un sistema para la venta y gestión de tickets para eventos, clases o entradas a espacios (Medusa `Ticket Booking System`). Complementa `Appointment_Booking_Management`.
- **Subscriptions:** Ofrecer planes de membresía para acceso ilimitado a ciertas reservas o descuentos exclusivos (Medusa `Subscriptions`). Se sincroniza con el módulo de suscripciones de Frappe (`Simple_Subscription`).
- **Customer Tiers:** Crear niveles de clientes (ej. cliente frecuente, VIP) para ofrecer beneficios como prioridad en reservas o descuentos (Medusa `Customer Tiers`). Se mapea con Grupos de Clientes en ERPNext.
- **Loyalty Points System:** Recompensar a los clientes por cada reserva o renta, permitiendo acumular puntos canjeables (Medusa `Loyalty Points System`).
- **Personalized Products:** Permitir personalización en la reserva (ej. agregar servicios extra al lavadero de autos, configurar el setup de un salón de eventos) (Medusa `Personalized Products`). Los detalles se guardan en el DocType de Reserva en Frappe.
- **Pre-orders:** Facilitar reservas anticipadas para eventos o espacios muy demandados con pago fraccionado o depósito (Medusa `Pre-orders`). Se gestiona en ERPNext con órdenes de venta.
- **Localization with Contentful/Sanity/Strapi/Payload Integration:** Gestionar el contenido multilingüe de las descripciones de servicios y políticas de reserva (Medusa `Localization with Contentful Integration`, `Sanity Integration`, `Strapi Integration`, `Payload Integration`).
- **Product Reviews:** Permitir a los usuarios calificar y reseñar los servicios o espacios rentados (Medusa `Product Reviews`).

## 6. Estrategias de Monetización y FOMO
- **Servicios Pagados Integrados:** Además del costo base de la renta/reserva, ofrecer "add-ons" o servicios premium (ej. lavado ecológico, decoración especial para eventos) que se seleccionan y pagan en el flujo de Medusa.
- **Membresías Premium:** Planes de suscripción (`Subscriptions`) que otorgan descuentos, acceso anticipado o reservas prioritarias.
- **FOMO (Cupos Limitados / Ofertas Flash):** Mostrar en tiempo real los cupos restantes para una clase o la disponibilidad de un espacio. Usar notificaciones push (`FCM_Notification`) para ofertas de última hora en reservas canceladas o no ocupadas.
- **Bonos por Fidelidad:** Los `Loyalty Points` crean un incentivo para reservar repetidamente y no perder los puntos acumulados.

## 7. Segmentación de Servicios
- **Lavadero de Carros:** Seguimiento del estado del servicio (Lavando -> En Secado -> Listo) integrado con el workflow de Frappe.
- **Eventos:** Gestión de listas de invitados y requerimientos adicionales (catering, luces) vía `Project_Management_System`.
- **Belleza:** Asignación de especialistas preferidos por el cliente con gestión de horarios en Frappe.

## 8. Flujo de Trabajo (Workflow Mejorado)
1. El cliente selecciona el servicio o espacio en la web/app (`booking.ricco.com`), personaliza su reserva (`Personalized Products`) o compra un ticket (`Ticket Booking System`).
2. Elige fecha y hora disponible (verificado por Frappe Calendar) y ve los `Product Rentals` disponibles.
3. Realiza el pago del depósito, posiblemente con un descuento por `Customer Tiers` o canje de `Loyalty Points`.
4. Se recibe confirmación por WhatsApp (`Frappe_WhatsApp`) y se asigna el staff automáticamente. Notificaciones de FOMO (`FCM_Notification`) en ofertas.
5. Tras el servicio, se procesa el pago final en el POS integrado. El cliente puede dejar `Product Reviews`.