# Sistema de Gamificación y Lealtad Transversal - Ricco Rewards

## 1. Visión General
El motor de incentivos que conecta todas las plataformas del ecosistema Ricco, utilizando mecánicas de juego para aumentar la retención de usuarios, fomentar comportamientos positivos y unificar la experiencia de marca a través de "Energy Points" y niveles de usuario.

## 2. Arquitectura Técnica
- **Core Engine:** `tmp_apps/eps` (Energy Points System) integrado en Frappe.
- **Base de Datos de Usuarios:** Compartida por todo el ecosistema (Frappe Multi-tenant).
- **Frontend:** Dashboard de usuario en `Ricco SuperApp` para visualizar puntos, medallas y beneficios.
- **Dominio Sugerido:** `rewards.ricco.com`

## 3. Aplicaciones de Frappe Recomendadas (incluyendo tmp_apps/)
- **eps (tmp_apps/):** Gestión de la lógica de asignación y redención de puntos por acciones específicas.
- **Pocket_Wallet:** Billetera digital donde se reflejan los beneficios económicos derivados de los puntos.
- **FCM_Notification:** Envío de alertas de "subida de nivel" o "puntos por vencer".
- **newsletter:** Boletines personalizados con ofertas basadas en el nivel del usuario.

## 4. Mecánicas de Gamificación por Plataforma
- **Ricco Mall/Wholesale:** Puntos por volumen de compra y por dejar reseñas (`Product Reviews`).
- **Ricco Gym:** Puntos por asistencia diaria y cumplimiento de metas de entrenamiento.
- **Ricco Social:** Puntos por creación de contenido de valor y engagement con la comunidad.
- **Ricco Health:** Puntos por completar chequeos preventivos o seguir planes de tratamiento.
- **Ricco Business:** Puntos por reclutamiento exitoso o participación en proyectos colaborativos.

## 5. Integración de IA Agéntica
- **n8n / Flowise:**
    - **Personalizador de Recompensas:** IA que analiza el perfil del usuario para sugerir premios que realmente le interesen (ej. un descuento en `Ricco Food` para un usuario foodie).
    - **Detección de Fraude en Puntos:** Agente que monitorea patrones inusuales para evitar la generación artificial de puntos.
    - **Motivador Virtual:** Bot que envía mensajes de ánimo y "desafíos" personalizados para que el usuario alcance el siguiente nivel.

## 6. Estrategias de FOMO y Retención
- **Niveles Exclusivos (Tiered Loyalty):** Acceso a preventas en `Ricco Mall` solo para niveles "Diamante".
- **Puntos con Caducidad:** "Tienes 100 puntos que vencen en 48 horas" (`FOMO`).
- **Tableros de Líderes (Leaderboards):** Rankings públicos por ciudad o categoría en `Ricco Social`.
- **Badges y Medallas:** Reconocimiento social visible en el perfil del usuario.

## 7. Flujo de Trabajo (Workflow de Recompensa)
1. El usuario realiza una acción (ej. compra en `Ricco Mall`).
2. El sistema `eps` detecta el evento y asigna "Energy Points" automáticamente.
3. El usuario recibe una notificación push celebrando la ganancia.
4. Al acumular puntos suficientes, la IA le sugiere canjearlos por una suscripción premium en `Ricco SuperApp` o un cupón de descuento.
5. El beneficio se aplica instantáneamente en la próxima transacción.
