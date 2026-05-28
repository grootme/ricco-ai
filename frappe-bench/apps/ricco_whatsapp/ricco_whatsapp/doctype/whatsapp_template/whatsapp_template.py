# Copyright (c) 2024, Ricco Technologies and contributors
# For license information, please see license.txt

"""
WhatsApp Template DocType
=========================

Manages WhatsApp message templates for business communication.
"""

import frappe
from frappe.model.document import Document
from frappe import _
import json


class WhatsAppTemplate(Document):
    """WhatsApp Template DocType Controller"""

    def validate(self):
        """Validate the template before saving"""
        self.validate_name_format()
        self.validate_components()
        self.generate_preview()

    def validate_name_format(self):
        """Validate template name format"""
        # Template names must be lowercase with underscores only
        import re
        if not re.match(r'^[a-z0-9_]+$', self.name_column):
            frappe.throw(_("Template name must contain only lowercase letters, numbers, and underscores"))

    def validate_components(self):
        """Validate component structure"""
        if not self.components:
            frappe.throw(_("Components are required"))
        
        try:
            components = json.loads(self.components) if isinstance(self.components, str) else self.components
        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON in components"))

        # Validate required fields
        if not isinstance(components, list):
            frappe.throw(_("Components must be a list"))

        # Check for body component (required)
        has_body = any(c.get("type") == "BODY" for c in components)
        if not has_body:
            frappe.throw(_("Template must have a BODY component"))

    def generate_preview(self):
        """Generate preview text from components"""
        try:
            components = json.loads(self.components) if isinstance(self.components, str) else self.components
            
            preview_parts = []
            for component in components:
                if component.get("type") == "HEADER":
                    text = component.get("text", "")
                    preview_parts.append(f"[HEADER] {text}")
                elif component.get("type") == "BODY":
                    text = component.get("text", "")
                    # Replace variables with placeholders
                    text = text.replace("{{1}}", "[...]")
                    text = text.replace("{{2}}", "[...]")
                    text = text.replace("{{3}}", "[...]")
                    text = text.replace("{{4}}", "[...]")
                    text = text.replace("{{5}}", "[...]")
                    preview_parts.append(text)
                elif component.get("type") == "FOOTER":
                    text = component.get("text", "")
                    preview_parts.append(f"[FOOTER] {text}")
                elif component.get("type") == "BUTTONS":
                    buttons = component.get("buttons", [])
                    button_texts = [b.get("text", "") for b in buttons]
                    preview_parts.append(f"[BUTTONS] {' | '.join(button_texts)}")
            
            self.preview_text = "\n".join(preview_parts)
        except Exception:
            self.preview_text = ""

    def on_update(self):
        """Actions after template is updated"""
        # Clear template cache
        frappe.cache().delete_key(f"whatsapp_template_{self.name_column}")

    def get_rendered_content(self, parameters: list = None) -> dict:
        """
        Render template with parameters
        
        Args:
            parameters: List of parameter values
            
        Returns:
            dict: Rendered component structure
        """
        components = json.loads(self.components) if isinstance(self.components, str) else self.components
        rendered = []
        
        for component in components:
            rendered_component = dict(component)
            
            if component.get("type") == "BODY" and parameters:
                text = component.get("text", "")
                for i, param in enumerate(parameters, 1):
                    text = text.replace(f"{{{{{i}}}}}", str(param))
                rendered_component["text"] = text
            
            rendered.append(rendered_component)
        
        return rendered

    def get_api_payload(self, parameters: list = None) -> dict:
        """
        Get payload for WhatsApp API
        
        Args:
            parameters: List of parameter values
            
        Returns:
            dict: API payload structure
        """
        components = json.loads(self.components) if isinstance(self.components, str) else self.components
        
        payload = {
            "type": "template",
            "template": {
                "name": self.name_column,
                "language": {
                    "code": self.language
                }
            }
        }
        
        # Add components with parameters
        template_components = []
        
        for component in components:
            comp_type = component.get("type")
            
            if comp_type == "HEADER":
                header_params = []
                if component.get("format") == "TEXT":
                    # Extract parameters from header text
                    import re
                    vars_in_header = re.findall(r'\{\{(\d+)\}\}', component.get("text", ""))
                    for var in vars_in_header:
                        idx = int(var) - 1
                        if idx < len(parameters or []):
                            header_params.append({"type": "text", "text": parameters[idx]})
                
                if header_params:
                    template_components.append({
                        "type": "header",
                        "parameters": header_params
                    })
            
            elif comp_type == "BODY":
                body_params = []
                # Extract parameters from body text
                import re
                vars_in_body = re.findall(r'\{\{(\d+)\}\}', component.get("text", ""))
                for var in vars_in_body:
                    idx = int(var) - 1
                    if idx < len(parameters or []):
                        body_params.append({"type": "text", "text": parameters[idx]})
                
                if body_params:
                    template_components.append({
                        "type": "body",
                        "parameters": body_params
                    })
            
            elif comp_type == "BUTTONS":
                # Handle button parameters
                buttons = component.get("buttons", [])
                for i, button in enumerate(buttons):
                    if button.get("type") == "URL":
                        # URL button may have variable parts
                        pass
                    elif button.get("type") == "QUICK_REPLY":
                        pass
        
        if template_components:
            payload["template"]["components"] = template_components
        
        return payload

    def increment_usage(self):
        """Increment usage counter"""
        self.total_sent = (self.total_sent or 0) + 1
        self.last_used = frappe.utils.now()
        self.db_update()

    @staticmethod
    def get_template(name: str, language: str = None) -> 'WhatsAppTemplate':
        """
        Get template by name and optional language
        
        Args:
            name: Template name
            language: Language code (optional)
            
        Returns:
            WhatsAppTemplate: Template document
        """
        cache_key = f"whatsapp_template_{name}_{language or 'default'}"
        cached = frappe.cache().get_value(cache_key)
        
        if cached:
            return cached
        
        filters = {"name_column": name, "is_active": 1, "status": "Approved"}
        if language:
            filters["language"] = language
        
        template_name = frappe.db.get_value("WhatsApp Template", filters)
        
        if not template_name and language:
            # Try default language
            filters.pop("language")
            template_name = frappe.db.get_value("WhatsApp Template", filters)
        
        if template_name:
            template = frappe.get_doc("WhatsApp Template", template_name)
            frappe.cache().set_value(cache_key, template, expires_in_sec=3600)
            return template
        
        return None


def get_available_templates() -> list:
    """
    Get all approved templates
    
    Returns:
        list: List of approved template names
    """
    templates = frappe.get_all(
        "WhatsApp Template",
        filters={"status": "Approved", "is_active": 1},
        fields=["name_column", "language", "category", "preview_text"],
        order_by="name_column"
    )
    
    return templates


@frappe.whitelist()
def get_templates_for_select():
    """Get templates formatted for select field"""
    templates = get_available_templates()
    return [{"value": t["name_column"], "label": f"{t['name_column']} ({t['language']})"} for t in templates]


@frappe.whitelist()
def preview_template(template_name: str, parameters: str = "[]"):
    """Preview a template with parameters"""
    template = frappe.get_doc("WhatsApp Template", template_name)
    params = json.loads(parameters) if isinstance(parameters, str) else parameters
    rendered = template.get_rendered_content(params)
    return rendered
