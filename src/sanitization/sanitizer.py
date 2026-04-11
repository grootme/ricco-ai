"""
Servicio de Sanitización de Datos Sensibles para RICCO AI
Implementación principal del sanitizador de datos

Este módulo implementa la clase principal de sanitización que
utiliza los patrones definidos para detectar y redactar
información sensible en texto.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

import re
import time
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

import logging

from .models import (
    SensitiveDataType,
    SanitizationRule,
    SanitizationResult,
    SanitizationLevel,
    DataClassification,
    TokenizedData,
)
from .patterns import SensitiveDataPatterns, PatternMatch

logger = logging.getLogger(__name__)


class SensitiveDataSanitizer:
    """
    Servicio principal de sanitización de datos sensibles.
    
    Proporciona métodos para detectar, sanitizar y tokenizar
    información sensible en texto antes de enviarla a modelos
    de IA o bundles de contexto.
    
    Características:
    - Detección de múltiples tipos de datos sensibles
    - Redacción parcial o total configurable
    - Soporte multilingüe (español, inglés)
    - Validación con algoritmos específicos (Luhn, CI cubano)
    - Tokenización para recuperación posterior
    
    Example:
        >>> sanitizer = SensitiveDataSanitizer()
        >>> result = sanitizer.sanitize_text(
        ...     "Mi email es juan@example.com y mi teléfono es +53 5123 4567"
        ... )
        >>> print(result.sanitized)
        "Mi email es j***@example.com y mi teléfono es ***-***-4567"
    """
    
    def __init__(
        self,
        level: SanitizationLevel = SanitizationLevel.STANDARD,
        custom_rules: Optional[List[SanitizationRule]] = None,
        enable_audit: bool = True,
    ):
        """
        Inicializa el sanitizador.
        
        Args:
            level: Nivel de sanitización por defecto
            custom_rules: Reglas personalizadas adicionales
            enable_audit: Si debe habilitar el logging de auditoría
        """
        self.level = level
        self.enable_audit = enable_audit
        
        # Cargar reglas
        self._rules: Dict[str, SanitizationRule] = {}
        self._load_rules(custom_rules)
        
        # Cache de tokens para recuperación
        self._token_cache: Dict[str, TokenizedData] = {}
        
        logger.info(
            "SensitiveDataSanitizer initialized",
            level=level.value,
            rules_count=len(self._rules),
        )
    
    def _load_rules(self, custom_rules: Optional[List[SanitizationRule]] = None) -> None:
        """Carga las reglas de sanitización."""
        # Cargar reglas por defecto
        default_rules = SensitiveDataPatterns.get_all_rules()
        
        for rule in default_rules:
            self._rules[rule.id] = rule
        
        # Añadir reglas personalizadas
        if custom_rules:
            for rule in custom_rules:
                self._rules[rule.id] = rule
        
        logger.debug(f"Loaded {len(self._rules)} sanitization rules")
    
    def add_rule(self, rule: SanitizationRule) -> None:
        """
        Añade una nueva regla de sanitización.
        
        Args:
            rule: Regla a añadir
        """
        self._rules[rule.id] = rule
        logger.debug(f"Added sanitization rule: {rule.id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remueve una regla de sanitización.
        
        Args:
            rule_id: ID de la regla a remover
            
        Returns:
            True si la regla fue removida
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.debug(f"Removed sanitization rule: {rule_id}")
            return True
        return False
    
    def get_rules(self) -> List[SanitizationRule]:
        """
        Obtiene todas las reglas de sanitización.
        
        Returns:
            Lista de reglas
        """
        return list(self._rules.values())
    
    def get_rules_by_type(self, data_type: SensitiveDataType) -> List[SanitizationRule]:
        """
        Obtiene reglas filtradas por tipo de dato.
        
        Args:
            data_type: Tipo de dato sensible
            
        Returns:
            Lista de reglas para ese tipo
        """
        return [
            rule for rule in self._rules.values()
            if rule.data_type == data_type
        ]
    
    def sanitize_text(
        self,
        text: str,
        rules: Optional[List[str]] = None,
        level: Optional[SanitizationLevel] = None,
    ) -> SanitizationResult:
        """
        Sanitiza texto removiendo o redactando datos sensibles.
        
        Este es el método principal para sanitizar texto. Aplica
        las reglas configuradas para detectar y redactar datos
        sensibles según el nivel de sanitización especificado.
        
        Args:
            text: Texto a sanitizar
            rules: Lista de IDs de reglas específicas a aplicar (opcional)
            level: Nivel de sanitización (sobrescribe el por defecto)
            
        Returns:
            SanitizationResult con el texto sanitizado y estadísticas
        
        Example:
            >>> result = sanitizer.sanitize_text(
            ...     "Mi tarjeta es 4532015112830366",
            ...     level=SanitizationLevel.AGGRESSIVE
            ... )
            >>> print(result.sanitized)
            "Mi tarjeta es ****-****-****-0366"
        """
        start_time = time.time()
        level = level or self.level
        
        result = SanitizationResult(
            original=text,
            sanitized=text,
            classification=DataClassification.PUBLIC,
        )
        
        # Filtrar reglas a aplicar
        rules_to_apply = self._filter_rules(rules, level)
        
        # Ordenar por prioridad (mayor primero)
        rules_to_apply.sort(key=lambda r: r.priority, reverse=True)
        
        # Aplicar cada regla
        for rule in rules_to_apply:
            try:
                result = self._apply_rule(result.sanitized, result, rule)
            except Exception as e:
                logger.error(
                    "Error applying sanitization rule",
                    rule_id=rule.id,
                    error=str(e),
                )
        
        # Determinar clasificación final
        result.classification = self._determine_classification(result)
        
        # Calcular tiempo de procesamiento
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        # Log de auditoría
        if self.enable_audit and result.has_sensitive_data():
            self._log_sanitization(result, level)
        
        return result
    
    def _filter_rules(
        self,
        rule_ids: Optional[List[str]],
        level: SanitizationLevel,
    ) -> List[SanitizationRule]:
        """Filtra las reglas según nivel y lista especificada."""
        if rule_ids:
            # Solo reglas especificadas
            return [
                self._rules[rid] for rid in rule_ids
                if rid in self._rules and self._rules[rid].enabled
            ]
        
        # Reglas según nivel
        return [
            rule for rule in self._rules.values()
            if rule.should_apply(level)
        ]
    
    def _apply_rule(
        self,
        text: str,
        result: SanitizationResult,
        rule: SanitizationRule,
    ) -> SanitizationResult:
        """
        Aplica una regla de sanitización al texto.
        
        Args:
            text: Texto a procesar
            result: Resultado acumulado
            rule: Regla a aplicar
            
        Returns:
            SanitizationResult actualizado
        """
        try:
            pattern = re.compile(rule.pattern)
        except re.error as e:
            logger.warning(f"Invalid regex pattern for rule {rule.id}: {e}")
            return result
        
        matches = list(pattern.finditer(text))
        
        if not matches:
            return result
        
        # Procesar cada coincidencia
        new_text = text
        offset = 0
        
        for match in matches:
            original_value = match.group()
            
            # Validación adicional si es necesaria
            if not self._validate_match(rule, original_value):
                continue
            
            # Generar valor redactado
            redacted_value = self._generate_redacted_value(rule, original_value)
            
            # Calcular posición con offset
            start = match.start() + offset
            end = match.end() + offset
            
            # Reemplazar
            new_text = new_text[:start] + redacted_value + new_text[match.end():]
            
            # Actualizar offset
            offset += len(redacted_value) - len(original_value)
            
            # Registrar redacción
            result.add_redaction(
                data_type=rule.data_type,
                original_value=original_value,
                redacted_value=redacted_value,
                position=(start, start + len(redacted_value)),
                rule_id=rule.id,
            )
        
        result.sanitized = new_text
        result.rules_applied.append(rule.id)
        
        return result
    
    def _validate_match(self, rule: SanitizationRule, value: str) -> bool:
        """
        Valida una coincidencia según reglas específicas.
        
        Args:
            rule: Regla que generó la coincidencia
            value: Valor encontrado
            
        Returns:
            True si la coincidencia es válida
        """
        # Validación de tarjeta de crédito con Luhn
        if rule.data_type == SensitiveDataType.CREDIT_CARD:
            return SensitiveDataPatterns.luhn_check(value)
        
        # Validación de CI cubano
        if "cuba_ci" in rule.id:
            return SensitiveDataPatterns.validate_cuban_ci(value)
        
        return True
    
    def _generate_redacted_value(
        self,
        rule: SanitizationRule,
        original_value: str,
    ) -> str:
        """
        Genera el valor redactado según la configuración de la regla.
        
        Args:
            rule: Regla aplicada
            original_value: Valor original
            
        Returns:
            Valor redactado
        """
        if rule.partial_redaction:
            # Redacción parcial específica por tipo
            if rule.data_type == SensitiveDataType.EMAIL:
                return SensitiveDataPatterns.partial_redact_email(original_value)
            elif rule.data_type == SensitiveDataType.PHONE:
                return SensitiveDataPatterns.partial_redact_phone(original_value)
            elif rule.data_type == SensitiveDataType.CREDIT_CARD:
                return SensitiveDataPatterns.partial_redact_credit_card(original_value)
        
        if rule.preserve_format:
            # Mantener formato con caracteres de redacción
            return self._preserve_format_redact(original_value, rule.redaction_char)
        
        return rule.replacement
    
    def _preserve_format_redact(self, value: str, char: str = "*") -> str:
        """Redacta manteniendo el formato original."""
        result = []
        for c in value:
            if c.isdigit():
                result.append(char)
            elif c.isalpha():
                result.append(char)
            else:
                result.append(c)
        return "".join(result)
    
    def _determine_classification(
        self,
        result: SanitizationResult,
    ) -> DataClassification:
        """
        Determina la clasificación de datos del resultado.
        
        Args:
            result: Resultado de sanitización
            
        Returns:
            DataClassification apropiada
        """
        if not result.detected_types:
            return DataClassification.PUBLIC
        
        # Obtener nivel de riesgo más alto
        highest_risk = result.get_highest_risk()
        
        classification_map = {
            "critical": DataClassification.RESTRICTED,
            "high": DataClassification.CONFIDENTIAL,
            "medium": DataClassification.INTERNAL,
            "low": DataClassification.PUBLIC,
        }
        
        return classification_map.get(highest_risk, DataClassification.CONFIDENTIAL)
    
    def _log_sanitization(
        self,
        result: SanitizationResult,
        level: SanitizationLevel,
    ) -> None:
        """Registra la operación de sanitización."""
        logger.info(
            "Text sanitized",
            redaction_count=result.redacted_count,
            data_types=[dt.value for dt in result.detected_types],
            classification=result.classification.value,
            level=level.value,
            processing_time_ms=result.processing_time_ms,
        )
    
    def detect_sensitive_data(
        self,
        text: str,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Detecta datos sensibles sin sanitizar.
        
        Útil para análisis y logging sin modificar el texto original.
        
        Args:
            text: Texto a analizar
            include_metadata: Si incluir metadata de cada detección
            
        Returns:
            Diccionario con tipos detectados y ubicaciones
        
        Example:
            >>> detection = sanitizer.detect_sensitive_data(
            ...     "Contacto: juan@example.com"
            ... )
            >>> print(detection["has_sensitive"])
            True
            >>> print(detection["types"])
            ["email"]
        """
        result: Dict[str, Any] = {
            "has_sensitive": False,
            "types": [],
            "matches": [],
            "risk_level": None,
            "regulations": [],
        }
        
        detected_types: set = set()
        all_regulations: set = set()
        highest_risk = None
        
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            try:
                pattern = re.compile(rule.pattern)
                matches = list(pattern.finditer(text))
                
                for match in matches:
                    original_value = match.group()
                    
                    # Validar si es necesario
                    if not self._validate_match(rule, original_value):
                        continue
                    
                    detected_types.add(rule.data_type)
                    all_regulations.update(rule.data_type.get_regulations())
                    
                    match_info = {
                        "type": rule.data_type.value,
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "start": match.start(),
                        "end": match.end(),
                        "length": len(original_value),
                    }
                    
                    if include_metadata:
                        match_info["metadata"] = {
                            "risk_level": rule.risk_level,
                            "regulations": rule.data_type.get_regulations(),
                        }
                    
                    result["matches"].append(match_info)
            
            except Exception as e:
                logger.debug(f"Error detecting with rule {rule.id}: {e}")
        
        if detected_types:
            result["has_sensitive"] = True
            result["types"] = [dt.value for dt in detected_types]
            
            # Determinar nivel de riesgo más alto
            risk_order = ["critical", "high", "medium", "low"]
            for risk in risk_order:
                for dt in detected_types:
                    if dt.get_risk_level() == risk:
                        highest_risk = risk
                        break
                if highest_risk:
                    break
            
            result["risk_level"] = highest_risk
            result["regulations"] = list(all_regulations)
        
        return result
    
    def redact_pii(
        self,
        text: str,
        level: SanitizationLevel = SanitizationLevel.STANDARD,
    ) -> str:
        """
        Redacta información personal identificable (PII).
        
        Método de conveniencia que solo retorna el texto redactado.
        
        Args:
            text: Texto a redactar
            level: Nivel de redacción
            
        Returns:
            Texto con PII redactado
        """
        result = self.sanitize_text(text, level=level)
        return result.sanitized
    
    def mask_sensitive(
        self,
        text: str,
        mask_char: str = "█",
        level: SanitizationLevel = SanitizationLevel.STANDARD,
    ) -> str:
        """
        Enmascara datos sensibles con un carácter específico.
        
        Diferente a la redacción, el enmascaramiento usa un carácter
        visual más prominente.
        
        Args:
            text: Texto a enmascarar
            mask_char: Carácter a usar para enmascarar
            level: Nivel de enmascaramiento
            
        Returns:
            Texto enmascarado
        """
        result = self.sanitize_text(text, level=level)
        
        # Reemplazar los valores redactados con el carácter de máscara
        masked = result.sanitized
        for redaction in result.redactions:
            # Buscar el valor redactado y reemplazar con máscara
            redacted_len = redaction["original_length"]
            mask_value = mask_char * min(redacted_len, 10)
            masked = masked.replace(redaction["redacted_value"], mask_value, 1)
        
        return masked
    
    def tokenize_sensitive(
        self,
        text: str,
        expires_in_hours: int = 24,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, Dict[str, str]]:
        """
        Tokeniza datos sensibles para recuperación posterior.
        
        Reemplaza datos sensibles con tokens que pueden ser
        utilizados para recuperar los datos originales más tarde.
        
        Args:
            text: Texto a tokenizar
            expires_in_hours: Horas hasta expiración del token
            user_id: ID del usuario (para auditoría)
            session_id: ID de la sesión
            
        Returns:
            Tupla (texto tokenizado, mapeo de tokens)
        
        Example:
            >>> text, tokens = sanitizer.tokenize_sensitive(
            ...     "Mi email es juan@example.com"
            ... )
            >>> print(text)
            "Mi email es [TOKEN:abc123]"
            >>> print(tokens)
            {"abc123": "juan@example.com"}
        """
        result = self.sanitize_text(text)
        tokenized_text = result.sanitized
        token_map: Dict[str, str] = {}
        
        for redaction in result.redactions:
            # Generar token único
            token = secrets.token_urlsafe(16)
            token_placeholder = f"[TOKEN:{token}]"
            
            # Guardar datos originales
            original_value = text[redaction["position"][0]:redaction["position"][1]]
            
            # Crear registro de token
            tokenized_data = TokenizedData(
                token=token,
                original_data=hashlib.sha256(original_value.encode()).hexdigest(),
                data_type=redaction["data_type"],
                user_id=user_id,
                session_id=session_id,
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            )
            
            self._token_cache[token] = tokenized_data
            
            # Mapear para retorno
            token_map[token] = original_value
            
            # Reemplazar en texto
            tokenized_text = tokenized_text.replace(
                redaction["redacted_value"],
                token_placeholder,
                1,
            )
        
        return tokenized_text, token_map
    
    def recover_tokenized(
        self,
        text: str,
        token_map: Dict[str, str],
    ) -> str:
        """
        Recupera valores originales a partir de tokens.
        
        Args:
            text: Texto tokenizado
            token_map: Mapeo de tokens a valores originales
            
        Returns:
            Texto con valores originales recuperados
        """
        recovered = text
        for token, original_value in token_map.items():
            token_placeholder = f"[TOKEN:{token}]"
            recovered = recovered.replace(token_placeholder, original_value)
        
        return recovered
    
    def get_token_data(self, token: str) -> Optional[TokenizedData]:
        """
        Obtiene los datos de un token específico.
        
        Args:
            token: Token a buscar
            
        Returns:
            TokenizedData o None si no existe o expiró
        """
        token_data = self._token_cache.get(token)
        
        if token_data and token_data.is_expired():
            del self._token_cache[token]
            return None
        
        return token_data
    
    def clear_expired_tokens(self) -> int:
        """
        Limpia tokens expirados del caché.
        
        Returns:
            Número de tokens eliminados
        """
        expired = [
            token for token, data in self._token_cache.items()
            if data.is_expired()
        ]
        
        for token in expired:
            del self._token_cache[token]
        
        if expired:
            logger.info(f"Cleared {len(expired)} expired tokens")
        
        return len(expired)
    
    def is_safe_for_ai(
        self,
        text: str,
        threshold: str = "high",
    ) -> bool:
        """
        Verifica si el texto es seguro para enviar a IA.
        
        Args:
            text: Texto a verificar
            threshold: Umbral de riesgo permitido (critical, high, medium, low)
            
        Returns:
            True si el texto es seguro
        """
        detection = self.detect_sensitive_data(text, include_metadata=False)
        
        if not detection["has_sensitive"]:
            return True
        
        risk_order = ["critical", "high", "medium", "low"]
        threshold_index = risk_order.index(threshold)
        detected_index = risk_order.index(detection["risk_level"])
        
        return detected_index > threshold_index
    
    def get_sanitized_preview(
        self,
        text: str,
        max_length: int = 100,
    ) -> str:
        """
        Genera una vista previa sanitizada del texto.
        
        Args:
            text: Texto completo
            max_length: Longitud máxima de la vista previa
            
        Returns:
            Vista previa sanitizada
        """
        result = self.sanitize_text(text)
        
        if len(result.sanitized) <= max_length:
            return result.sanitized
        
        return result.sanitized[:max_length - 3] + "..."
    
    # Métodos de conveniencia estáticos
    
    @staticmethod
    def quick_sanitize(text: str) -> str:
        """
        Sanitización rápida sin configuración.
        
        Args:
            text: Texto a sanitizar
            
        Returns:
            Texto sanitizado
        """
        sanitizer = SensitiveDataSanitizer()
        return sanitizer.redact_pii(text)
    
    @staticmethod
    def quick_detect(text: str) -> Dict[str, Any]:
        """
        Detección rápida sin configuración.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Resultado de la detección
        """
        sanitizer = SensitiveDataSanitizer()
        return sanitizer.detect_sensitive_data(text)
