"""
Patrones de Detección de Datos Sensibles para RICCO AI
Regex patterns para identificación de información sensible

Este módulo contiene todos los patrones regex utilizados para
detectar datos sensibles en texto, con soporte especial para
formatos cubanos y latinoamericanos.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from .models import SensitiveDataType, SanitizationRule


@dataclass
class PatternMatch:
    """
    Representa una coincidencia de patrón en el texto.
    
    Attributes:
        data_type: Tipo de dato sensible detectado
        value: Valor encontrado
        start: Posición inicial en el texto
        end: Posición final en el texto
        rule_id: ID de la regla que generó la coincidencia
        confidence: Nivel de confianza de la detección (0-1)
    """
    data_type: SensitiveDataType
    value: str
    start: int
    end: int
    rule_id: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SensitiveDataPatterns:
    """
    Colección de patrones para detección de datos sensibles.
    
    Incluye soporte para formatos internacionales con énfasis
    en formatos cubanos y latinoamericanos.
    """
    
    # ============================================
    # Patrones de Tarjetas de Crédito
    # ============================================
    
    CREDIT_CARD_PATTERNS = {
        # Visa: 16 dígitos, empieza con 4
        "visa": {
            "pattern": r"\b4[0-9]{12}(?:[0-9]{3})?\b",
            "format": "Visa",
            "check_luhn": True,
        },
        # Mastercard: 16 dígitos, empieza con 51-55 o 2221-2720
        "mastercard": {
            "pattern": r"\b(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}\b",
            "format": "Mastercard",
            "check_luhn": True,
        },
        # American Express: 15 dígitos, empieza con 34 o 37
        "amex": {
            "pattern": r"\b3[47][0-9]{13}\b",
            "format": "American Express",
            "check_luhn": True,
        },
        # Discover: 16 dígitos, empieza con 6011, 644-649, o 65
        "discover": {
            "pattern": r"\b(?:6011|65[0-9]{2}|64[4-9][0-9])\d{12}\b",
            "format": "Discover",
            "check_luhn": True,
        },
        # Diners Club: 14 dígitos, empieza con 300-305, 36, o 38
        "diners": {
            "pattern": r"\b(?:3(?:0[0-5]|[68][0-9])[0-9]{11})\b",
            "format": "Diners Club",
            "check_luhn": True,
        },
        # JCB: 16 dígitos, empieza con 2131, 1800, o 35
        "jcb": {
            "pattern": r"\b(?:2131|1800|35\d{3})\d{11}\b",
            "format": "JCB",
            "check_luhn": True,
        },
        # Patrón genérico para cualquier tarjeta (16-19 dígitos)
        "generic": {
            "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b",
            "format": "Tarjeta de Crédito",
            "check_luhn": True,
        },
    }
    
    # ============================================
    # Patrones de SSN / Identificación Nacional
    # ============================================
    
    SSN_PATTERNS = {
        # SSN de Estados Unidos: XXX-XX-XXXX
        "us_ssn": {
            "pattern": r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
            "format": "SSN (US)",
            "country": "US",
        },
        # SSN de Estados Unidos sin guiones
        "us_ssn_no_dash": {
            "pattern": r"\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b",
            "format": "SSN (US)",
            "country": "US",
        },
        # Carné de Identidad cubano: 11 dígitos
        # Formato: YYMMDDXXXXX (año, mes, día, secuencia)
        "cuba_ci": {
            "pattern": r"\b\d{11}\b",
            "format": "Carné de Identidad (Cuba)",
            "country": "CU",
            "validator": "_validate_cuban_ci",
        },
        # Carné de Identidad cubano con guión: XXXXXXXXXX-X
        "cuba_ci_hyphen": {
            "pattern": r"\b\d{10}[-\s]?\d\b",
            "format": "Carné de Identidad (Cuba)",
            "country": "CU",
        },
        # CURP México: 18 caracteres alfanuméricos
        "mx_curp": {
            "pattern": r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d\b",
            "format": "CURP (México)",
            "country": "MX",
        },
        # RFC México: 12-13 caracteres
        "mx_rfc": {
            "pattern": r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b",
            "format": "RFC (México)",
            "country": "MX",
        },
        # DNI España: 8 dígitos + letra
        "es_dni": {
            "pattern": r"\b\d{8}[A-HJ-NP-TV-Z]\b",
            "format": "DNI (España)",
            "country": "ES",
        },
        # NIE España: X/Y/Z + 7 dígitos + letra
        "es_nie": {
            "pattern": r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b",
            "format": "NIE (España)",
            "country": "ES",
        },
        # CUIL/CUIT Argentina: XX-XXXXXXXX-X
        "ar_cuit": {
            "pattern": r"\b\d{2}[-\s]?\d{8}[-\s]?\d\b",
            "format": "CUIT/CUIL (Argentina)",
            "country": "AR",
        },
        # RUT Chile: XX.XXX.XXX-X
        "cl_rut": {
            "pattern": r"\b\d{1,2}\.?\d{3}\.?\d{3}[-\s]?[0-9Kk]\b",
            "format": "RUT (Chile)",
            "country": "CL",
        },
        # Cédula Colombia: 8-10 dígitos
        "co_cc": {
            "pattern": r"\b\d{8,10}\b",
            "format": "Cédula (Colombia)",
            "country": "CO",
            "context_required": True,  # Necesita contexto para validar
        },
    }
    
    # ============================================
    # Patrones de Email
    # ============================================
    
    EMAIL_PATTERNS = {
        # Email estándar
        "standard": {
            "pattern": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "format": "Email",
        },
        # Email con dominios sensibles (gobierno, militar, etc.)
        "sensitive_domains": {
            "pattern": r"\b[a-zA-Z0-9._%+-]+@(?:gov|mil|gob|edu|health)\.[a-zA-Z]{2,}\b",
            "format": "Email Institucional",
        },
    }
    
    # ============================================
    # Patrones de Teléfono
    # ============================================
    
    PHONE_PATTERNS = {
        # Cuba: +53 XXXX XXXX o 5XXX XXXX
        "cuba_mobile": {
            "pattern": r"(?:\+?53\s?)?5\d{3}[\s-]?\d{4}\b",
            "format": "Móvil (Cuba)",
            "country": "CU",
        },
        "cuba_fixed": {
            "pattern": r"(?:\+?53\s?)?(?:7|2[1-9]|3[1-9]|4[1-9]|5[1-9]|6[1-9])[0-9]{2}[\s-]?\d{4}\b",
            "format": "Fijo (Cuba)",
            "country": "CU",
        },
        # US/Canada: +1 XXX XXX XXXX
        "us_canada": {
            "pattern": r"(?:\+?1\s?)?(?:\([2-9]\d{2}\)|[2-9]\d{2})[\s.-]?\d{3}[\s.-]?\d{4}\b",
            "format": "Teléfono (US/Canadá)",
            "country": "US",
        },
        # España: +34 XXX XXX XXX
        "spain": {
            "pattern": r"(?:\+?34\s?)?[6-9]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
            "format": "Teléfono (España)",
            "country": "ES",
        },
        # México: +52 XX XXXX XXXX
        "mexico": {
            "pattern": r"(?:\+?52\s?)?1?\s?[1-9]\d{1}\s?\d{4}[\s.-]?\d{4}\b",
            "format": "Teléfono (México)",
            "country": "MX",
        },
        # Internacional genérico
        "international": {
            "pattern": r"\+?(?:[0-9]\s?){8,15}[0-9]\b",
            "format": "Teléfono Internacional",
        },
    }
    
    # ============================================
    # Patrones de API Keys y Tokens
    # ============================================
    
    API_KEY_PATTERNS = {
        # AWS Access Key
        "aws_access": {
            "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "format": "AWS Access Key",
            "service": "AWS",
        },
        # AWS Secret Key
        "aws_secret": {
            "pattern": r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z/+=]{40}['\"]",
            "format": "AWS Secret Key",
            "service": "AWS",
        },
        # Google API Key
        "google_api": {
            "pattern": r"AIza[0-9A-Za-z\\-_]{35}",
            "format": "Google API Key",
            "service": "Google",
        },
        # Google OAuth
        "google_oauth": {
            "pattern": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
            "format": "Google OAuth Client",
            "service": "Google",
        },
        # GitHub Token
        "github_token": {
            "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}",
            "format": "GitHub Token",
            "service": "GitHub",
        },
        # Slack Token
        "slack_token": {
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
            "format": "Slack Token",
            "service": "Slack",
        },
        # Stripe API Key
        "stripe_api": {
            "pattern": r"(?:sk|rk)_(?:test|live)_[0-9a-zA-Z]{24}",
            "format": "Stripe API Key",
            "service": "Stripe",
        },
        # OpenAI API Key
        "openai_api": {
            "pattern": r"sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}",
            "format": "OpenAI API Key",
            "service": "OpenAI",
        },
        # Anthropic API Key
        "anthropic_api": {
            "pattern": r"sk-ant-api03-[A-Za-z0-9]{20,}",
            "format": "Anthropic API Key",
            "service": "Anthropic",
        },
        # JWT Token
        "jwt": {
            "pattern": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+",
            "format": "JWT Token",
            "service": "JWT",
        },
        # Generic API Key pattern
        "generic_api_key": {
            "pattern": r"(?i)(?:api[_-]?key|apikey|token|secret|password|auth)[\s:=]*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?",
            "format": "API Key Genérica",
        },
        # Private Key header
        "private_key": {
            "pattern": r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            "format": "Clave Privada",
        },
    }
    
    # ============================================
    # Patrones de Cuentas Bancarias
    # ============================================
    
    BANK_ACCOUNT_PATTERNS = {
        # IBAN genérico
        "iban": {
            "pattern": r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b",
            "format": "IBAN",
        },
        # SWIFT/BIC
        "swift": {
            "pattern": r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b",
            "format": "SWIFT/BIC",
        },
        # Routing Number US
        "routing_us": {
            "pattern": r"\b[0-9]{9}\b",
            "format": "Routing Number (US)",
            "country": "US",
            "context_required": True,
        },
        # CLABE México
        "mx_clabe": {
            "pattern": r"\b[0-9]{18}\b",
            "format": "CLABE (México)",
            "country": "MX",
        },
        # CBU Argentina
        "ar_cbu": {
            "pattern": r"\b[0-9]{22}\b",
            "format": "CBU (Argentina)",
            "country": "AR",
        },
    }
    
    # ============================================
    # Patrones de Criptomonedas
    # ============================================
    
    CRYPTO_PATTERNS = {
        # Bitcoin Address (P2PKH, P2SH, Bech32)
        "bitcoin": {
            "pattern": r"\b(?:[13][a-km-zA-Z1-9]{25,34}|bc1[a-zA-Z0-9]{39,59})\b",
            "format": "Bitcoin Address",
        },
        # Ethereum Address
        "ethereum": {
            "pattern": r"\b0x[a-fA-F0-9]{40}\b",
            "format": "Ethereum Address",
        },
        # Litecoin Address
        "litecoin": {
            "pattern": r"\b[LM][a-km-zA-Z1-9]{25,34}\b",
            "format": "Litecoin Address",
        },
        # Ripple Address
        "ripple": {
            "pattern": r"\br[0-9a-zA-Z]{24,34}\b",
            "format": "Ripple Address",
        },
        # Tron Address
        "tron": {
            "pattern": r"\bT[A-Za-z0-9]{33}\b",
            "format": "Tron Address",
        },
        # Private Key (generic hex)
        "crypto_private_key": {
            "pattern": r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b",
            "format": "Crypto Private Key",
        },
    }
    
    # ============================================
    # Patrones de Documentos de Identidad
    # ============================================
    
    GOVERNMENT_ID_PATTERNS = {
        # Pasaporte genérico
        "passport_generic": {
            "pattern": r"\b[A-Z]{1,2}[0-9]{6,9}\b",
            "format": "Pasaporte",
        },
        # Pasaporte US
        "passport_us": {
            "pattern": r"\b[0-9]{9}\b",
            "format": "Pasaporte (US)",
            "country": "US",
            "context_required": True,
        },
        # Pasaporte España
        "passport_es": {
            "pattern": r"\b[A-Z]{3}[0-9]{6}[A-Z]?\b",
            "format": "Pasaporte (España)",
            "country": "ES",
        },
        # Licencia de conducir US (varía por estado)
        "drivers_license_us": {
            "pattern": r"\b[A-Z]{1,2}[0-9]{3,8}[A-Z]?\d?\b",
            "format": "Licencia de Conducir",
            "country": "US",
            "context_required": True,
        },
    }
    
    # ============================================
    # Patrones de Ubicación Exacta
    # ============================================
    
    LOCATION_PATTERNS = {
        # Coordenadas GPS (lat, long)
        "gps_coords": {
            "pattern": r"\b-?\d{1,3}\.\d{4,},\s*-?\d{1,3}\.\d{4,}\b",
            "format": "Coordenadas GPS",
        },
        # Latitud sola
        "latitude": {
            "pattern": r"\b(?:lat|latitude)[:\s]+(-?\d{1,3}\.\d+)\b",
            "format": "Latitud",
        },
        # Longitud sola
        "longitude": {
            "pattern": r"\b(?:lon|long|longitude)[:\s]+(-?\d{1,3}\.\d+)\b",
            "format": "Longitud",
        },
        # Google Maps URL
        "google_maps_url": {
            "pattern": r"https?://(?:www\.)?google\.com/maps/[^\s]*",
            "format": "Google Maps URL",
        },
        # What3Words
        "what3words": {
            "pattern": r"\b[A-Za-z0-9]{4,}\.[A-Za-z0-9]{4,}\.[A-Za-z0-9]{4,}\b",
            "format": "What3Words",
        },
    }
    
    # ============================================
    # Patrones de Datos Médicos
    # ============================================
    
    MEDICAL_PATTERNS = {
        # Número de Historia Clínica
        "medical_record_number": {
            "pattern": r"\b(?:HC|HCE|MRN|HIST)[:\s]*[A-Z0-9-]{6,20}\b",
            "format": "Número de Historia Clínica",
        },
        # Número de Seguro Social de Salud
        "health_insurance_id": {
            "pattern": r"\b(?:NSS|NHS|HI)[:\s]*[A-Z0-9-]{6,15}\b",
            "format": "ID de Seguro Médico",
        },
        # Nombres de medicamentos controlados
        "controlled_substance": {
            "pattern": r"(?i)\b(?:oxycodone|hydrocodone|fentanyl|morphine|adderall|ritalin|xanax|valium|diazepam|codeine)\b",
            "format": "Medicamento Controlado",
        },
        # Diagnóstico ICD-10
        "icd10": {
            "pattern": r"\b[A-Z]\d{2}(?:\.[A-Z0-9]{1,4})?\b",
            "format": "Código ICD-10",
        },
        # Información médica sensible
        "medical_sensitive": {
            "pattern": r"(?i)\b(?:VIH|HIV|SIDA|AIDS|cáncer|cancer|diabetes|hipertensión|hypertension)\b",
            "format": "Información Médica Sensible",
        },
    }
    
    # ============================================
    # Patrones de Datos Financieros
    # ============================================
    
    FINANCIAL_PATTERNS = {
        # Número de cuenta genérico
        "account_number": {
            "pattern": r"\b(?:account|cuenta|acct)[:\s]*[0-9-]{8,20}\b",
            "format": "Número de Cuenta",
        },
        # Monto con moneda
        "monetary_amount": {
            "pattern": r"\b(?:USD|EUR|CUP|MXN|ARS)\s?[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?\b",
            "format": "Monto Monetario",
        },
        # Número de transacción
        "transaction_id": {
            "pattern": r"\b(?:TXN|TRANS|TRX)[:\s]*[A-Z0-9-]{8,30}\b",
            "format": "ID de Transacción",
        },
    }
    
    # ============================================
    # Patrones Biométricos
    # ============================================
    
    BIOMETRIC_PATTERNS = {
        # Template de huella digital (base64)
        "fingerprint_template": {
            "pattern": r"(?:FMR|FMD)[:\s]*[A-Za-z0-9+/=]{100,}",
            "format": "Template de Huella",
        },
        # Face encoding
        "face_encoding": {
            "pattern": r"(?:face|facial|encoding)[:\s]*\[[\d\.\-\s,]{50,}\]",
            "format": "Encoding Facial",
        },
    }
    
    # ============================================
    # Patrones de Contraseñas
    # ============================================
    
    PASSWORD_PATTERNS = {
        # Contraseña en contexto
        "password_context": {
            "pattern": r"(?i)(?:password|contraseña|passwd|pwd|pass)\s*[=:]\s*['\"]?[^'\"\s]{8,}['\"]?",
            "format": "Contraseña",
        },
        # Contraseña en URL
        "password_url": {
            "pattern": r"(?i)://[^:]+:[^@]+@",
            "format": "Contraseña en URL",
        },
    }
    
    @classmethod
    def get_all_rules(cls) -> List[SanitizationRule]:
        """
        Genera todas las reglas de sanitización a partir de los patrones.
        
        Returns:
            Lista de SanitizationRule para todos los tipos de datos
        """
        rules = []
        
        # Reglas para tarjetas de crédito
        for name, config in cls.CREDIT_CARD_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"cc_{name}",
                name=f"Tarjeta {config['format']}",
                data_type=SensitiveDataType.CREDIT_CARD,
                pattern=config["pattern"],
                replacement="****-****-****-XXXX",
                risk_level="critical",
                partial_redaction=True,
                description=f"Detecta números de tarjeta {config['format']}",
            ))
        
        # Reglas para SSN/Identificación
        for name, config in cls.SSN_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"ssn_{name}",
                name=config["format"],
                data_type=SensitiveDataType.SSN,
                pattern=config["pattern"],
                replacement="XXX-XX-XXXX",
                risk_level="critical",
                countries=[config.get("country", "*")],
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para emails
        for name, config in cls.EMAIL_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"email_{name}",
                name=config["format"],
                data_type=SensitiveDataType.EMAIL,
                pattern=config["pattern"],
                replacement="***@***.***",
                risk_level="medium",
                partial_redaction=True,
                description=f"Detecta direcciones de {config['format']}",
            ))
        
        # Reglas para teléfonos
        for name, config in cls.PHONE_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"phone_{name}",
                name=config["format"],
                data_type=SensitiveDataType.PHONE,
                pattern=config["pattern"],
                replacement="+XX-XXX-XXX-XXXX",
                risk_level="medium",
                partial_redaction=True,
                countries=[config.get("country", "*")],
                description=f"Detecta números {config['format']}",
            ))
        
        # Reglas para API keys
        for name, config in cls.API_KEY_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"apikey_{name}",
                name=config["format"],
                data_type=SensitiveDataType.API_KEY,
                pattern=config["pattern"],
                replacement="[API_KEY_REDACTED]",
                risk_level="critical",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para cuentas bancarias
        for name, config in cls.BANK_ACCOUNT_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"bank_{name}",
                name=config["format"],
                data_type=SensitiveDataType.BANK_ACCOUNT,
                pattern=config["pattern"],
                replacement="XXXX-XXXX-XXXX-XXXX",
                risk_level="critical",
                partial_redaction=True,
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para criptomonedas
        for name, config in cls.CRYPTO_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"crypto_{name}",
                name=config["format"],
                data_type=SensitiveDataType.CRYPTO_ADDRESS,
                pattern=config["pattern"],
                replacement="[CRYPTO_ADDRESS_REDACTED]",
                risk_level="high",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para documentos de identidad
        for name, config in cls.GOVERNMENT_ID_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"govtid_{name}",
                name=config["format"],
                data_type=SensitiveDataType.GOVERNMENT_ID,
                pattern=config["pattern"],
                replacement="[DOCUMENT_REDACTED]",
                risk_level="high",
                countries=[config.get("country", "*")],
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para ubicación
        for name, config in cls.LOCATION_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"location_{name}",
                name=config["format"],
                data_type=SensitiveDataType.LOCATION_EXACT,
                pattern=config["pattern"],
                replacement="[LOCATION_GENERALIZED]",
                risk_level="high",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para datos médicos
        for name, config in cls.MEDICAL_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"medical_{name}",
                name=config["format"],
                data_type=SensitiveDataType.MEDICAL_RECORD,
                pattern=config["pattern"],
                replacement="[MEDICAL_REDACTED]",
                risk_level="critical",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para datos financieros
        for name, config in cls.FINANCIAL_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"financial_{name}",
                name=config["format"],
                data_type=SensitiveDataType.FINANCIAL_DATA,
                pattern=config["pattern"],
                replacement="[FINANCIAL_REDACTED]",
                risk_level="high",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para datos biométricos
        for name, config in cls.BIOMETRIC_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"biometric_{name}",
                name=config["format"],
                data_type=SensitiveDataType.BIOMETRIC,
                pattern=config["pattern"],
                replacement="[BIOMETRIC_REDACTED]",
                risk_level="critical",
                description=f"Detecta {config['format']}",
            ))
        
        # Reglas para contraseñas
        for name, config in cls.PASSWORD_PATTERNS.items():
            rules.append(SanitizationRule(
                id=f"password_{name}",
                name=config["format"],
                data_type=SensitiveDataType.PASSWORD,
                pattern=config["pattern"],
                replacement="[PASSWORD_REDACTED]",
                risk_level="critical",
                description=f"Detecta {config['format']}",
            ))
        
        return rules
    
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """
        Valida un número de tarjeta usando el algoritmo de Luhn.
        
        Args:
            card_number: Número de tarjeta a validar
            
        Returns:
            True si pasa la validación Luhn
        """
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) < 13:
            return False
        
        # Duplicar cada segundo dígito de derecha a izquierda
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        return sum(digits) % 10 == 0
    
    @staticmethod
    def validate_cuban_ci(ci: str) -> bool:
        """
        Valida un Carné de Identidad cubano.
        
        El CI cubano tiene 11 dígitos: YYMMDDXXXXX
        - YY: Año de nacimiento (2 dígitos)
        - MM: Mes (01-12)
        - DD: Día (01-31)
        - XXXXX: Número de secuencia
        
        Args:
            ci: Número de CI a validar
            
        Returns:
            True si el formato es válido
        """
        if len(ci) != 11 or not ci.isdigit():
            return False
        
        year = int(ci[0:2])
        month = int(ci[2:4])
        day = int(ci[4:6])
        
        # Validar mes
        if month < 1 or month > 12:
            return False
        
        # Validar día (simplificado)
        if day < 1 or day > 31:
            return False
        
        return True
    
    @staticmethod
    def partial_redact_email(email: str) -> str:
        """
        Redacta parcialmente un email.
        
        Args:
            email: Email a redactar
            
        Returns:
            Email parcialmente redactado (j***@example.com)
        """
        if "@" not in email:
            return "***@***.***"
        
        local, domain = email.split("@", 1)
        
        if len(local) <= 1:
            redacted_local = "*"
        elif len(local) <= 3:
            redacted_local = local[0] + "*" * (len(local) - 1)
        else:
            redacted_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        # Redactar dominio también
        if "." in domain:
            domain_parts = domain.split(".")
            domain_name = domain_parts[0]
            tld = ".".join(domain_parts[1:])
            
            if len(domain_name) <= 2:
                redacted_domain = "*" * len(domain_name) + "." + tld
            else:
                redacted_domain = domain_name[0] + "*" * (len(domain_name) - 1) + "." + tld
        else:
            redacted_domain = "***.***"
        
        return f"{redacted_local}@{redacted_domain}"
    
    @staticmethod
    def partial_redact_phone(phone: str) -> str:
        """
        Redacta parcialmente un número telefónico.
        
        Args:
            phone: Número a redactar
            
        Returns:
            Número parcialmente redactado
        """
        # Extraer solo dígitos
        digits = "".join(c for c in phone if c.isdigit())
        
        if len(digits) < 4:
            return "***-***"
        
        # Mantener los últimos 4 dígitos
        return "***-***-" + digits[-4:]
    
    @staticmethod
    def partial_redact_credit_card(card: str) -> str:
        """
        Redacta parcialmente un número de tarjeta.
        
        Args:
            card: Número de tarjeta
            
        Returns:
            Número parcialmente redactado (****-****-****-1234)
        """
        digits = "".join(c for c in card if c.isdigit())
        
        if len(digits) < 4:
            return "****-****-****-****"
        
        return "****-****-****-" + digits[-4:]
    
    @staticmethod
    def generalize_coordinates(lat: float, lon: float, precision: str = "city") -> Dict[str, Any]:
        """
        Generaliza coordenadas exactas a una ubicación menos precisa.
        
        Args:
            lat: Latitud
            lon: Longitud
            precision: Nivel de precisión (exact, city, region, country)
            
        Returns:
            Diccionario con ubicación generalizada
        """
        result = {
            "original_lat": None,
            "original_lon": None,
            "generalized_lat": None,
            "generalized_lon": None,
            "precision": precision,
        }
        
        if precision == "exact":
            # Mantener coordenadas exactas
            result["generalized_lat"] = lat
            result["generalized_lon"] = lon
        elif precision == "city":
            # Reducir a 2 decimales (~1km precisión)
            result["generalized_lat"] = round(lat, 2)
            result["generalized_lon"] = round(lon, 2)
        elif precision == "region":
            # Reducir a 1 decimal (~10km precisión)
            result["generalized_lat"] = round(lat, 1)
            result["generalized_lon"] = round(lon, 1)
        else:  # country
            # Solo mantener el grado (~111km precisión)
            result["generalized_lat"] = round(lat, 0)
            result["generalized_lon"] = round(lon, 0)
        
        return result
