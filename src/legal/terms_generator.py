"""
RICCO Terms Generator
Generador de términos y condiciones basado en ubicación y contexto del usuario
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import os

from .models import (
    LegalDocument, 
    DocumentType, 
    Language, 
    Jurisdiction
)


class TermsGenerator:
    """Generador de documentos legales contextualizados"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or self._get_default_templates_dir()
        self._cache: Dict[str, LegalDocument] = {}
    
    def _get_default_templates_dir(self) -> str:
        """Obtiene el directorio de plantillas por defecto"""
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        return str(base_dir / "apps" / "we" / "assets" / "legal")
    
    def get_terms_for_user(
        self,
        user_location: str = "CU",
        language: Language = Language.ES,
        document_type: DocumentType = DocumentType.TERMS_OF_SERVICE
    ) -> LegalDocument:
        """
        Obtiene los términos apropiados para un usuario basado en su ubicación
        
        Args:
            user_location: Código de país del usuario (ISO 3166-1 alpha-2)
            language: Idioma preferido del usuario
            document_type: Tipo de documento a obtener
            
        Returns:
            LegalDocument con los términos apropiados
        """
        # Determinar jurisdicción
        jurisdiction = self._determine_jurisdiction(user_location)
        
        # Generar clave de caché
        cache_key = f"{document_type.value}_{language.value}_{jurisdiction.value}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Cargar documento desde archivo
        document = self._load_document(document_type, language, jurisdiction)
        
        # Guardar en caché
        self._cache[cache_key] = document
        
        return document
    
    def _determine_jurisdiction(self, user_location: str) -> Jurisdiction:
        """Determina la jurisdicción legal aplicable"""
        # Cuba tiene regulaciones específicas
        if user_location.upper() == "CU":
            return Jurisdiction.CUBA
        
        # Países de la UE tienen GDPR
        eu_countries = {
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO"
        }
        if user_location.upper() in eu_countries:
            return Jurisdiction.EU
        
        # Por defecto, jurisdicción internacional
        return Jurisdiction.INTERNATIONAL
    
    def _load_document(
        self,
        document_type: DocumentType,
        language: Language,
        jurisdiction: Jurisdiction
    ) -> LegalDocument:
        """Carga un documento legal desde archivo"""
        
        # Mapear tipo de documento a nombre de archivo
        filename_map = {
            DocumentType.TERMS_OF_SERVICE: f"terms_of_service_{language.value}.md",
            DocumentType.PRIVACY_POLICY: f"privacy_policy_{language.value}.md",
            DocumentType.COOKIE_POLICY: f"cookie_policy_{language.value}.md",
            DocumentType.DATA_PROCESSING: f"data_processing_{language.value}.md",
            DocumentType.ACCEPTABLE_USE: f"acceptable_use_{language.value}.md",
            DocumentType.CRYPTO_PAYMENTS: "crypto_payments_terms.md",
        }
        
        filename = filename_map.get(document_type, f"{document_type.value}_{language.value}.md")
        filepath = Path(self.templates_dir) / filename
        
        # Intentar cargar el archivo
        content = ""
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Generar contenido por defecto si no existe
            content = self._generate_default_content(document_type, language, jurisdiction)
        
        # Títulos según tipo y idioma
        titles = {
            DocumentType.TERMS_OF_SERVICE: {
                Language.ES: "Términos y Condiciones de RICCO",
                Language.EN: "RICCO Terms and Conditions"
            },
            DocumentType.PRIVACY_POLICY: {
                Language.ES: "Política de Privacidad de RICCO",
                Language.EN: "RICCO Privacy Policy"
            },
            DocumentType.COOKIE_POLICY: {
                Language.ES: "Política de Cookies de RICCO",
                Language.EN: "RICCO Cookie Policy"
            },
            DocumentType.DATA_PROCESSING: {
                Language.ES: "Política de Tratamiento de Datos",
                Language.EN: "Data Processing Policy"
            },
            DocumentType.ACCEPTABLE_USE: {
                Language.ES: "Política de Uso Aceptable",
                Language.EN: "Acceptable Use Policy"
            },
            DocumentType.CRYPTO_PAYMENTS: {
                Language.ES: "Términos para Pagos con Criptomonedas",
                Language.EN: "Cryptocurrency Payment Terms"
            }
        }
        
        return LegalDocument(
            document_type=document_type,
            version="1.0.0",
            language=language,
            title=titles.get(document_type, {}).get(language, document_type.value),
            content=content,
            effective_date=datetime(2025, 1, 1),
            last_updated=datetime.utcnow(),
            jurisdiction=jurisdiction,
            is_active=True,
            is_published=True
        )
    
    def _generate_default_content(
        self,
        document_type: DocumentType,
        language: Language,
        jurisdiction: Jurisdiction
    ) -> str:
        """Genera contenido por defecto para un documento legal"""
        
        if language == Language.ES:
            return self._generate_spanish_content(document_type, jurisdiction)
        else:
            return self._generate_english_content(document_type, jurisdiction)
    
    def _generate_spanish_content(
        self,
        document_type: DocumentType,
        jurisdiction: Jurisdiction
    ) -> str:
        """Genera contenido en español"""
        
        base_content = f"""# Términos y Condiciones de RICCO

**Versión:** 1.0.0  
**Fecha de vigencia:** 1 de enero de 2025  
**Última actualización:** {datetime.utcnow().strftime('%d de %B de %Y')}  
**Jurisdicción:** {'Cuba' if jurisdiction == Jurisdiction.CUBA else 'Internacional'}

---

## 1. Aceptación de los Términos

Al descargar, instalar o utilizar la aplicación RICCO ("la App") y los servicios asociados, usted acepta estar sujeto a estos Términos y Condiciones ("Términos"). Si no está de acuerdo con alguno de estos términos, no debe utilizar la App ni los servicios.

### 1.1 Modificaciones
RICCO se reserva el derecho de modificar estos Términos en cualquier momento. Las modificaciones entrarán en vigor inmediatamente después de su publicación. El uso continuado de la App constituye la aceptación de los términos modificados.

## 2. Descripción de los Servicios

RICCO es un ecosistema de aplicaciones y servicios que incluye:

### 2.1 RICCO Commerce
- Marketplace para compra y venta de productos
- Gestión de inventario para comerciantes
- Sistema de pagos y facturación

### 2.2 RICCO Health
- Consultas médicas virtuales
- Gestión de citas médicas
- Historial de salud digital

### 2.3 RICCO Logistics
- Seguimiento de envíos
- Gestión de entregas
- Optimización de rutas

### 2.4 RICCO Finance
- Pagos con criptomonedas
- Energy Points (puntos de recompensa)
- Suscripciones y membresías

### 2.5 RICCO AI
- Asistente virtual inteligente
- Recomendaciones personalizadas
- Generación de interfaces dinámicas (GenUI)

## 3. Cuentas de Usuario

### 3.1 RICCO ID
Para utilizar los servicios de RICCO, debe crear una cuenta RICCO ID. Usted es responsable de:
- Proporcionar información veraz y actualizada
- Mantener la confidencialidad de sus credenciales
- Todas las actividades realizadas bajo su cuenta

### 3.2 Verificación
Podemos requerir verificación de identidad para ciertos servicios, incluyendo:
- Verificación de correo electrónico
- Verificación telefónica
- Verificación KYC (Know Your Customer) para servicios financieros

### 3.3 Suspensión y Terminación
Nos reservamos el derecho de suspender o terminar cuentas que:
- Violen estos Términos
- Involucren actividades fraudulentas
- Representen un riesgo para otros usuarios

## 4. Pagos y Suscripciones

### 4.1 Métodos de Pago
RICCO acepta:
- Tarjetas de crédito/débito
- Criptomonedas (BTC, USDT, ETH, y otras)
- Energy Points
- Transferencias bancarias (donde esté disponible)

### 4.2 Suscripciones
- Las suscripciones se renuevan automáticamente
- Puede cancelar en cualquier momento antes del período de facturación
- No hay reembolsos por períodos parciales

### 4.3 Energy Points
Los Energy Points son puntos de recompensa que:
- Pueden obtenerse mediante actividades en la app
- Tienen valor para compras dentro del ecosistema
- No son dinero fiduciario ni criptomoneda
- No tienen valor de canje por dinero
- Pueden expirar según las políticas vigentes

## 5. Uso Aceptable

### 5.1 Actividades Prohibidas
Está prohibido utilizar RICCO para:
- Actividades ilegales bajo las leyes cubanas e internacionales
- Vender productos prohibidos o restringidos
- Suplantar identidades
- Difundir malware o contenido dañino
- Violar derechos de propiedad intelectual
- Acosar, amenazar o discriminar a otros usuarios
- Manipular precios o generar contenido falso

### 5.2 Contenido
Usted es responsable del contenido que publica. RICCO puede eliminar contenido que:
- Violente estos Términos
- Sea ofensivo o inapropiado
- Infrinja derechos de terceros

## 6. Propiedad Intelectual

### 6.1 Derechos de RICCO
RICCO y sus licenciantes poseen todos los derechos sobre:
- La aplicación y su código fuente
- Marcas comerciales y logotipos
- Diseños y contenido original
- Algoritmos y modelos de IA

### 6.2 Licencia de Uso
Se le concede una licencia limitada, no exclusiva, revocable para:
- Utilizar la App para fines personales y comerciales legítimos
- Acceder a los servicios según su suscripción

### 6.3 Contenido del Usuario
Usted mantiene la propiedad de su contenido, pero otorga a RICCO una licencia para:
- Procesar y almacenar su contenido
- Mostrarlo según la configuración de privacidad
- Utilizarlo para mejorar los servicios (con su consentimiento)

## 7. Privacidad y Datos

El tratamiento de datos personales se rige por nuestra Política de Privacidad, que forma parte integral de estos Términos.

### 7.1 Datos Recopilados
Recopilamos datos necesarios para:
- Prestar los servicios solicitados
- Mejorar la experiencia del usuario
- Cumplir obligaciones legales
- Proteger la seguridad

### 7.2 Derechos del Usuario
Usted tiene derecho a:
- Acceder a sus datos personales
- Rectificar datos incorrectos
- Solicitar eliminación de datos
- Oponerse a ciertos tratamientos
- Exportar sus datos

## 8. Inteligencia Artificial

### 8.1 Servicios de IA
RICCO utiliza inteligencia artificial para:
- Personalizar la experiencia del usuario
- Generar recomendaciones
- Procesar consultas (RICCO AI)
- Generar interfaces dinámicas (GenUI/A2UI)

### 8.2 Consentimiento para IA
El uso de servicios de IA personalizados requiere su consentimiento explícito. Puede desactivar esta función en cualquier momento en Configuración > Privacidad.

### 8.3 Limitaciones
Los servicios de IA tienen limitaciones:
- Pueden cometer errores
- No constituyen asesoramiento profesional
- Deben verificarse los resultados importantes

## 9. Descargo de Responsabilidad

### 9.1 Servicios "Tal Cual"
Los servicios se proporcionan "tal cual" sin garantías de:
- Disponibilidad ininterrumpida
- Ausencia de errores
- Exactitud de resultados de IA

### 9.2 Limitación de Responsabilidad
RICCO no será responsable por:
- Daños indirectos o consecuentes
- Pérdida de datos o beneficios
- Acciones de terceros

### 9.3 Límite Máximo
La responsabilidad total de RICCO está limitada al monto pagado por el usuario en los últimos 12 meses.

## 10. Terminación

### 10.1 Por el Usuario
Puede terminar su cuenta en cualquier momento desde Configuración > Cuenta > Eliminar cuenta.

### 10.2 Por RICCO
Podemos terminar o suspender servicios por:
- Violación de estos Términos
- Inactividad prolongada
- Solicitudes legales

### 10.3 Efectos
Tras la terminación:
- Se eliminarán sus datos según nuestra política de retención
- Se cancelarán suscripciones activas
- Perderá acceso a Energy Points no utilizados

## 11. Resolución de Disputas

### 11.1 Jurisdicción
{'Estos Términos se rigen por las leyes de la República de Cuba. Cualquier disputa será resuelta por los tribunales cubanos competentes.' if jurisdiction == Jurisdiction.CUBA else 'Estos Términos se rigen por las leyes aplicables según su jurisdicción.'}

### 11.2 Arbitraje
Antes de recurrir a vías legales, las partes acuerdan intentar resolver disputas mediante:
1. Negociación directa
2. Mediación
3. Arbitraje (si aplica)

### 11.3 Acciones Colectivas
Usted acepta que las disputas se resolverán individualmente, no mediante acciones colectivas.

## 12. Disposiciones Generales

### 12.1 Acuerdo Completo
Estos Términos, junto con la Política de Privacidad, constituyen el acuerdo completo entre usted y RICCO.

### 12.2 Independencia
Si alguna disposición es declarada inválida, las demás permanecerán en vigor.

### 12.3 Renuncia
La falta de ejercicio de un derecho no constituye renuncia al mismo.

### 12.4 Cesión
No puede ceder sus derechos bajo estos Términos sin consentimiento por escrito.

## 13. Contacto

Para consultas sobre estos Términos:

**RICCO Legal Team**  
📧 Email: legal@ricco.app  
📍 La Habana, Cuba  

**Delegado de Protección de Datos (DPO):**  
📧 Email: dpo@ricco.app  

---

*Última actualización: {datetime.utcnow().strftime('%d/%m/%Y')}*
*Versión del documento: 1.0.0*
"""
        return base_content
    
    def _generate_english_content(
        self,
        document_type: DocumentType,
        jurisdiction: Jurisdiction
    ) -> str:
        """Generates content in English"""
        
        return f"""# RICCO Terms and Conditions

**Version:** 1.0.0  
**Effective Date:** January 1, 2025  
**Last Updated:** {datetime.utcnow().strftime('%B %d, %Y')}  
**Jurisdiction:** {'Cuba' if jurisdiction == Jurisdiction.CUBA else 'International'}

---

## 1. Acceptance of Terms

By downloading, installing, or using the RICCO application ("the App") and associated services, you agree to be bound by these Terms and Conditions ("Terms"). If you do not agree to any of these terms, you must not use the App or services.

### 1.1 Modifications
RICCO reserves the right to modify these Terms at any time. Modifications become effective immediately upon posting. Continued use of the App constitutes acceptance of the modified terms.

## 2. Services Description

RICCO is an ecosystem of applications and services including:

### 2.1 RICCO Commerce
- Marketplace for buying and selling products
- Inventory management for merchants
- Payment and billing system

### 2.2 RICCO Health
- Virtual medical consultations
- Appointment management
- Digital health records

### 2.3 RICCO Logistics
- Shipment tracking
- Delivery management
- Route optimization

### 2.4 RICCO Finance
- Cryptocurrency payments
- Energy Points (reward points)
- Subscriptions and memberships

### 2.5 RICCO AI
- Intelligent virtual assistant
- Personalized recommendations
- Dynamic interface generation (GenUI)

## 3. User Accounts

### 3.1 RICCO ID
To use RICCO services, you must create a RICCO ID account. You are responsible for:
- Providing truthful and up-to-date information
- Maintaining confidentiality of your credentials
- All activities under your account

### 3.2 Verification
We may require identity verification for certain services, including:
- Email verification
- Phone verification
- KYC (Know Your Customer) verification for financial services

### 3.3 Suspension and Termination
We reserve the right to suspend or terminate accounts that:
- Violate these Terms
- Involve fraudulent activities
- Pose a risk to other users

## 4. Payments and Subscriptions

### 4.1 Payment Methods
RICCO accepts:
- Credit/debit cards
- Cryptocurrencies (BTC, USDT, ETH, and others)
- Energy Points
- Bank transfers (where available)

### 4.2 Subscriptions
- Subscriptions renew automatically
- You can cancel anytime before the billing period
- No refunds for partial periods

### 4.3 Energy Points
Energy Points are reward points that:
- Can be earned through app activities
- Have value for purchases within the ecosystem
- Are not fiat money or cryptocurrency
- Have no cash redemption value
- May expire according to current policies

## 5. Acceptable Use

### 5.1 Prohibited Activities
Using RICCO for the following is prohibited:
- Illegal activities under Cuban and international laws
- Selling prohibited or restricted products
- Identity impersonation
- Spreading malware or harmful content
- Violating intellectual property rights
- Harassing, threatening, or discriminating against other users
- Price manipulation or generating fake content

### 5.2 Content
You are responsible for content you post. RICCO may remove content that:
- Violates these Terms
- Is offensive or inappropriate
- Infringes third-party rights

## 6. Intellectual Property

### 6.1 RICCO Rights
RICCO and its licensors own all rights to:
- The application and its source code
- Trademarks and logos
- Designs and original content
- Algorithms and AI models

### 6.2 Use License
You are granted a limited, non-exclusive, revocable license to:
- Use the App for legitimate personal and commercial purposes
- Access services according to your subscription

### 6.3 User Content
You maintain ownership of your content, but grant RICCO a license to:
- Process and store your content
- Display it according to privacy settings
- Use it to improve services (with your consent)

## 7. Privacy and Data

Data processing is governed by our Privacy Policy, which is an integral part of these Terms.

### 7.1 Data Collected
We collect data necessary for:
- Providing requested services
- Improving user experience
- Fulfilling legal obligations
- Protecting security

### 7.2 User Rights
You have the right to:
- Access your personal data
- Rectify incorrect data
- Request data deletion
- Object to certain processing
- Export your data

## 8. Artificial Intelligence

### 8.1 AI Services
RICCO uses artificial intelligence to:
- Personalize user experience
- Generate recommendations
- Process queries (RICCO AI)
- Generate dynamic interfaces (GenUI/A2UI)

### 8.2 AI Consent
Using personalized AI services requires your explicit consent. You can disable this feature at any time in Settings > Privacy.

### 8.3 Limitations
AI services have limitations:
- They may make mistakes
- They do not constitute professional advice
- Important results should be verified

## 9. Disclaimer

### 9.1 "As Is" Services
Services are provided "as is" without warranties of:
- Uninterrupted availability
- Error-free operation
- Accuracy of AI results

### 9.2 Limitation of Liability
RICCO will not be liable for:
- Indirect or consequential damages
- Loss of data or profits
- Third-party actions

### 9.3 Maximum Limit
RICCO's total liability is limited to the amount paid by the user in the last 12 months.

## 10. Termination

### 10.1 By User
You can terminate your account at any time from Settings > Account > Delete account.

### 10.2 By RICCO
We may terminate or suspend services for:
- Violation of these Terms
- Prolonged inactivity
- Legal requests

### 10.3 Effects
After termination:
- Your data will be deleted according to our retention policy
- Active subscriptions will be canceled
- You will lose access to unused Energy Points

## 11. Dispute Resolution

### 11.1 Jurisdiction
{'These Terms are governed by the laws of the Republic of Cuba. Any dispute will be resolved by competent Cuban courts.' if jurisdiction == Jurisdiction.CUBA else 'These Terms are governed by applicable laws according to your jurisdiction.'}

### 11.2 Arbitration
Before resorting to legal channels, parties agree to attempt to resolve disputes through:
1. Direct negotiation
2. Mediation
3. Arbitration (if applicable)

### 11.3 Class Actions
You agree that disputes will be resolved individually, not through class actions.

## 12. General Provisions

### 12.1 Entire Agreement
These Terms, along with the Privacy Policy, constitute the entire agreement between you and RICCO.

### 12.2 Independence
If any provision is declared invalid, the others remain in force.

### 12.3 Waiver
Failure to exercise a right does not constitute waiver.

### 12.4 Assignment
You may not assign your rights under these Terms without written consent.

## 13. Contact

For questions about these Terms:

**RICCO Legal Team**  
📧 Email: legal@ricco.app  
📍 Havana, Cuba  

**Data Protection Officer (DPO):**  
📧 Email: dpo@ricco.app  

---

*Last updated: {datetime.utcnow().strftime('%m/%d/%Y')}*
*Document version: 1.0.0*
"""

    def check_for_updates(
        self,
        current_version: str,
        document_type: DocumentType
    ) -> bool:
        """Verifica si hay actualizaciones del documento"""
        latest = self.get_terms_for_user(document_type=document_type)
        return latest.version != current_version
    
    def get_all_documents(
        self,
        language: Language = Language.ES,
        jurisdiction: Jurisdiction = Jurisdiction.CUBA
    ) -> Dict[str, LegalDocument]:
        """Obtiene todos los documentos legales disponibles"""
        documents = {}
        for doc_type in DocumentType:
            try:
                documents[doc_type.value] = self._load_document(
                    doc_type, language, jurisdiction
                )
            except Exception:
                continue
        return documents
