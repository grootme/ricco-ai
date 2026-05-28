"""
A2UI Service Module for RICCO AI.

Streaming UI generation service with multi-platform compilation.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Target platforms for UI generation."""
    REACT = "react"
    FLUTTER = "flutter"
    LIT = "lit"
    NATIVE = "native"
    HTML = "html"


class GenerationOptions(BaseModel):
    """Options for UI generation."""
    platform: Platform = Platform.REACT
    theme: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    include_styles: bool = True
    include_actions: bool = True
    streaming: bool = True


class ComponentType(str, Enum):
    """Types of UI components."""
    BUTTON = "button"
    CARD = "card"
    FORM = "form"
    LIST = "list"
    MODAL = "modal"
    NAVIGATION = "navigation"
    INPUT = "input"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    PRODUCT_CARD = "product_card"
    USER_PROFILE = "user_profile"
    DASHBOARD = "dashboard"


class ComponentAction(BaseModel):
    """Action definition for a component."""
    action_type: str
    handler: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ComponentStyle(BaseModel):
    """Style definition for a component."""
    display: Optional[str] = None
    flex_direction: Optional[str] = None
    padding: Optional[str] = None
    margin: Optional[str] = None
    background_color: Optional[str] = None
    border_radius: Optional[str] = None
    font_size: Optional[str] = None
    custom: Dict[str, str] = Field(default_factory=dict)


class A2UIComponent(BaseModel):
    """AI-generated UI component."""
    component_id: str
    component_type: ComponentType
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    actions: List[ComponentAction] = Field(default_factory=list)
    style: Optional[ComponentStyle] = None
    children: List["A2UIComponent"] = Field(default_factory=list)
    
    # Metadata
    platform: Platform = Platform.REACT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class A2UIResponse(BaseModel):
    """Response from A2UI generation."""
    response_id: str
    prompt: str
    components: List[A2UIComponent]
    platform: Platform
    generation_time_ms: float = 0.0
    tokens_used: int = 0
    cached: bool = False


class A2UIService:
    """
    A2UI Service for generating UI from natural language.
    
    Features:
    - Streaming UI generation
    - Multi-platform compilation (React, Flutter, Lit)
    - Component registry with schema validation
    - Theme system with design tokens
    """
    
    def __init__(self, default_platform: Platform = Platform.REACT):
        self.default_platform = default_platform
        
        # Component registry
        self._components: Dict[str, A2UIComponent] = {}
        
        # Metrics
        self._total_generations = 0
        self._total_tokens_used = 0
        self._cache_hits = 0
    
    async def generate(
        self,
        prompt: str,
        options: Optional[GenerationOptions] = None,
    ) -> A2UIResponse:
        """
        Generate UI components from a natural language prompt.
        
        Args:
            prompt: Natural language description of the UI
            options: Generation options
            
        Returns:
            A2UIResponse with generated components
        """
        import time
        import uuid
        
        options = options or GenerationOptions(platform=self.default_platform)
        start_time = time.time()
        self._total_generations += 1
        
        # Generate component (placeholder implementation)
        component = await self._generate_component(prompt, options)
        
        response = A2UIResponse(
            response_id=str(uuid.uuid4()),
            prompt=prompt,
            components=[component],
            platform=options.platform,
            generation_time_ms=(time.time() - start_time) * 1000,
        )
        
        self._total_tokens_used += response.tokens_used
        
        return response
    
    async def generate_stream(
        self,
        prompt: str,
        options: Optional[GenerationOptions] = None,
    ):
        """
        Generate UI components with streaming.
        
        Yields StreamingEvent objects as components are generated.
        """
        from .streaming import StreamingEvent, StreamingEventType
        
        options = options or GenerationOptions(platform=self.default_platform)
        
        # Yield start event
        yield StreamingEvent(
            event_type=StreamingEventType.START,
            data={"prompt": prompt},
        )
        
        # Generate component
        component = await self._generate_component(prompt, options)
        
        # Yield component event
        yield StreamingEvent(
            event_type=StreamingEventType.COMPONENT,
            data={"component": component.model_dump()},
        )
        
        # Yield complete event
        yield StreamingEvent(
            event_type=StreamingEventType.COMPLETE,
            data={"component_id": component.component_id},
        )
    
    async def compile(
        self,
        component: A2UIComponent,
        platform: Platform,
    ) -> str:
        """
        Compile a component to a specific platform.
        
        Args:
            component: Component to compile
            platform: Target platform
            
        Returns:
            Compiled code as string
        """
        if platform == Platform.REACT:
            return self._compile_react(component)
        elif platform == Platform.FLUTTER:
            return self._compile_flutter(component)
        elif platform == Platform.LIT:
            return self._compile_lit(component)
        else:
            return self._compile_html(component)
    
    async def _generate_component(
        self,
        prompt: str,
        options: GenerationOptions,
    ) -> A2UIComponent:
        """Generate a component from prompt (placeholder)."""
        import uuid
        
        # Simple intent detection
        prompt_lower = prompt.lower()
        
        if "product" in prompt_lower or "card" in prompt_lower:
            component_type = ComponentType.PRODUCT_CARD
        elif "form" in prompt_lower or "input" in prompt_lower:
            component_type = ComponentType.FORM
        elif "list" in prompt_lower:
            component_type = ComponentType.LIST
        elif "button" in prompt_lower:
            component_type = ComponentType.BUTTON
        elif "profile" in prompt_lower:
            component_type = ComponentType.USER_PROFILE
        else:
            component_type = ComponentType.CONTAINER
        
        return A2UIComponent(
            component_id=f"comp_{uuid.uuid4().hex[:8]}",
            component_type=component_type,
            name=f"Generated{component_type.value.title().replace('_', '')}",
            platform=options.platform,
        )
    
    def _compile_react(self, component: A2UIComponent) -> str:
        """Compile to React JSX."""
        return f"""// Generated React Component
import React from 'react';

export const {component.name} = ({{
  // Add props here
}}) => {{
  return (
    <div className="{component.component_type.value}">
      {{/* Component content */}}
    </div>
  );
}};

export default {component.name};
"""
    
    def _compile_flutter(self, component: A2UIComponent) -> str:
        """Compile to Flutter Dart."""
        return f"""// Generated Flutter Widget
import 'package:flutter/material.dart';

class {component.name} extends StatelessWidget {{
  const {component.name}({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Container(
      child: const Text('{component.component_type.value}'),
    );
  }}
}}
"""
    
    def _compile_lit(self, component: A2UIComponent) -> str:
        """Compile to Lit web component."""
        return f"""// Generated Lit Component
import {{ LitElement, html, css }} from 'lit';

export class {component.name} extends LitElement {{
  static styles = css`
    :host {{
      display: block;
    }}
  `;

  render() {{
    return html`
      <div class="{component.component_type.value}">
        <!-- Component content -->
      </div>
    `;
  }}
}}

customElements.define('{component.component_type.value.replace("_", "-")}', {component.name});
"""
    
    def _compile_html(self, component: A2UIComponent) -> str:
        """Compile to plain HTML."""
        return f"""<!-- Generated HTML -->
<div class="{component.component_type.value}">
  <!-- Component content -->
</div>
"""
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "total_generations": self._total_generations,
            "total_tokens_used": self._total_tokens_used,
            "cache_hits": self._cache_hits,
            "registered_components": len(self._components),
        }
