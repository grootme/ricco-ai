"""
A2UI Theme Manager - Theme system integration for component theming.
Supports multiple themes, custom themes, and theme propagation.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class ThemeMode(str, Enum):
    """Theme display modes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeVariant(str, Enum):
    """Theme variant types."""
    DEFAULT = "default"
    DARK = "dark"
    CUBAN = "cuban"
    CUSTOM = "custom"


class ColorScale(BaseModel):
    """Color scale with multiple shades."""
    main: str = Field(..., description="Primary color")
    light: Optional[str] = Field(None, description="Light variant")
    dark: Optional[str] = Field(None, description="Dark variant")
    contrast_text: Optional[str] = Field(None, description="Text color on main")
    
    def to_css_vars(self, prefix: str) -> Dict[str, str]:
        """Convert to CSS variables."""
        vars_dict = {f"--{prefix}": self.main}
        if self.light:
            vars_dict[f"--{prefix}-light"] = self.light
        if self.dark:
            vars_dict[f"--{prefix}-dark"] = self.dark
        if self.contrast_text:
            vars_dict[f"--{prefix}-contrast"] = self.contrast_text
        return vars_dict


class Typography(BaseModel):
    """Typography configuration."""
    font_family: str = Field(default="Inter, system-ui, sans-serif")
    font_size_base: str = Field(default="16px")
    line_height: str = Field(default="1.5")
    
    # Heading sizes
    h1: str = Field(default="2.5rem")
    h2: str = Field(default="2rem")
    h3: str = Field(default="1.75rem")
    h4: str = Field(default="1.5rem")
    h5: str = Field(default="1.25rem")
    h6: str = Field(default="1rem")
    
    # Font weights
    font_weight_normal: int = Field(default=400)
    font_weight_medium: int = Field(default=500)
    font_weight_semibold: int = Field(default=600)
    font_weight_bold: int = Field(default=700)
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert to CSS variables."""
        return {
            "--font-family": self.font_family,
            "--font-size-base": self.font_size_base,
            "--line-height": self.line_height,
            "--h1": self.h1,
            "--h2": self.h2,
            "--h3": self.h3,
            "--h4": self.h4,
            "--h5": self.h5,
            "--h6": self.h6,
        }


class Spacing(BaseModel):
    """Spacing scale configuration."""
    xs: str = Field(default="4px")
    sm: str = Field(default="8px")
    md: str = Field(default="16px")
    lg: str = Field(default="24px")
    xl: str = Field(default="32px")
    xxl: str = Field(default="48px")
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert to CSS variables."""
        return {
            "--spacing-xs": self.xs,
            "--spacing-sm": self.sm,
            "--spacing-md": self.md,
            "--spacing-lg": self.lg,
            "--spacing-xl": self.xl,
            "--spacing-xxl": self.xxl,
        }


class BorderRadius(BaseModel):
    """Border radius configuration."""
    none: str = Field(default="0")
    sm: str = Field(default="4px")
    md: str = Field(default="8px")
    lg: str = Field(default="12px")
    xl: str = Field(default="16px")
    full: str = Field(default="9999px")
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert to CSS variables."""
        return {
            "--radius-none": self.none,
            "--radius-sm": self.sm,
            "--radius-md": self.md,
            "--radius-lg": self.lg,
            "--radius-xl": self.xl,
            "--radius-full": self.full,
        }


class Shadows(BaseModel):
    """Shadow configuration."""
    none: str = Field(default="none")
    sm: str = Field(default="0 1px 2px rgba(0, 0, 0, 0.05)")
    md: str = Field(default="0 4px 6px rgba(0, 0, 0, 0.1)")
    lg: str = Field(default="0 10px 15px rgba(0, 0, 0, 0.1)")
    xl: str = Field(default="0 20px 25px rgba(0, 0, 0, 0.15)")
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert to CSS variables."""
        return {
            "--shadow-none": self.none,
            "--shadow-sm": self.sm,
            "--shadow-md": self.md,
            "--shadow-lg": self.lg,
            "--shadow-xl": self.xl,
        }


class ThemeDefinition(BaseModel):
    """Complete theme definition."""
    theme_id: str = Field(..., description="Unique theme identifier")
    theme_name: str = Field(..., description="Human-readable theme name")
    variant: ThemeVariant = Field(default=ThemeVariant.DEFAULT)
    mode: ThemeMode = Field(default=ThemeMode.LIGHT)
    
    # Colors
    primary: ColorScale = Field(..., description="Primary color")
    secondary: ColorScale = Field(..., description="Secondary color")
    success: ColorScale = Field(default=ColorScale(main="#10B981", contrast_text="#FFFFFF"))
    warning: ColorScale = Field(default=ColorScale(main="#F59E0B", contrast_text="#FFFFFF"))
    error: ColorScale = Field(default=ColorScale(main="#EF4444", contrast_text="#FFFFFF"))
    info: ColorScale = Field(default=ColorScale(main="#3B82F6", contrast_text="#FFFFFF"))
    
    # Background and surface colors
    background: str = Field(default="#FFFFFF")
    surface: str = Field(default="#FFFFFF")
    surface_elevated: str = Field(default="#F9FAFB")
    
    # Text colors
    text_primary: str = Field(default="#111827")
    text_secondary: str = Field(default="#6B7280")
    text_disabled: str = Field(default="#9CA3AF")
    text_hint: str = Field(default="#D1D5DB")
    
    # Border colors
    border: str = Field(default="#E5E7EB")
    border_dark: str = Field(default="#D1D5DB")
    divider: str = Field(default="#F3F4F6")
    
    # Typography
    typography: Typography = Field(default_factory=Typography)
    
    # Spacing
    spacing: Spacing = Field(default_factory=Spacing)
    
    # Border radius
    border_radius: BorderRadius = Field(default_factory=BorderRadius)
    
    # Shadows
    shadows: Shadows = Field(default_factory=Shadows)
    
    # Component-specific overrides
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Custom CSS variables
    custom_vars: Dict[str, str] = Field(default_factory=dict)
    
    # Metadata
    author: Optional[str] = None
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def to_css_vars(self) -> Dict[str, str]:
        """Convert entire theme to CSS variables."""
        vars_dict = {}
        
        # Colors
        vars_dict.update(self.primary.to_css_vars("color-primary"))
        vars_dict.update(self.secondary.to_css_vars("color-secondary"))
        vars_dict.update(self.success.to_css_vars("color-success"))
        vars_dict.update(self.warning.to_css_vars("color-warning"))
        vars_dict.update(self.error.to_css_vars("color-error"))
        vars_dict.update(self.info.to_css_vars("color-info"))
        
        # Backgrounds
        vars_dict["--background"] = self.background
        vars_dict["--surface"] = self.surface
        vars_dict["--surface-elevated"] = self.surface_elevated
        
        # Text
        vars_dict["--text-primary"] = self.text_primary
        vars_dict["--text-secondary"] = self.text_secondary
        vars_dict["--text-disabled"] = self.text_disabled
        vars_dict["--text-hint"] = self.text_hint
        
        # Borders
        vars_dict["--border"] = self.border
        vars_dict["--border-dark"] = self.border_dark
        vars_dict["--divider"] = self.divider
        
        # Typography
        vars_dict.update(self.typography.to_css_vars())
        
        # Spacing
        vars_dict.update(self.spacing.to_css_vars())
        
        # Border radius
        vars_dict.update(self.border_radius.to_css_vars())
        
        # Shadows
        vars_dict.update(self.shadows.to_css_vars())
        
        # Custom vars
        vars_dict.update(self.custom_vars)
        
        return vars_dict
    
    def to_css(self) -> str:
        """Convert theme to CSS string."""
        css_vars = self.to_css_vars()
        vars_str = "\n".join(f"  {k}: {v};" for k, v in css_vars.items())
        return f":root {{\n{vars_str}\n}}"
    
    def get_component_style(self, component_id: str) -> Dict[str, Any]:
        """Get style overrides for a specific component."""
        return self.components.get(component_id, {})


# Predefined themes
DEFAULT_LIGHT_THEME = ThemeDefinition(
    theme_id="default-light",
    theme_name="Default Light",
    variant=ThemeVariant.DEFAULT,
    mode=ThemeMode.LIGHT,
    primary=ColorScale(
        main="#3B82F6",
        light="#60A5FA",
        dark="#2563EB",
        contrast_text="#FFFFFF"
    ),
    secondary=ColorScale(
        main="#6366F1",
        light="#818CF8",
        dark="#4F46E5",
        contrast_text="#FFFFFF"
    ),
    background="#FFFFFF",
    surface="#FFFFFF",
    surface_elevated="#F9FAFB",
    text_primary="#111827",
    text_secondary="#6B7280"
)

DEFAULT_DARK_THEME = ThemeDefinition(
    theme_id="default-dark",
    theme_name="Default Dark",
    variant=ThemeVariant.DARK,
    mode=ThemeMode.DARK,
    primary=ColorScale(
        main="#60A5FA",
        light="#93C5FD",
        dark="#3B82F6",
        contrast_text="#000000"
    ),
    secondary=ColorScale(
        main="#818CF8",
        light="#A5B4FC",
        dark="#6366F1",
        contrast_text="#000000"
    ),
    success=ColorScale(main="#34D399", contrast_text="#000000"),
    warning=ColorScale(main="#FBBF24", contrast_text="#000000"),
    error=ColorScale(main="#F87171", contrast_text="#000000"),
    info=ColorScale(main="#60A5FA", contrast_text="#000000"),
    background="#0F172A",
    surface="#1E293B",
    surface_elevated="#334155",
    text_primary="#F1F5F9",
    text_secondary="#94A3B8",
    text_disabled="#64748B",
    text_hint="#475569",
    border="#334155",
    border_dark="#475569",
    divider="#1E293B"
)

CUBAN_THEME = ThemeDefinition(
    theme_id="cuban",
    theme_name="Cuban Vibrant",
    variant=ThemeVariant.CUBAN,
    mode=ThemeMode.LIGHT,
    primary=ColorScale(
        main="#E53935",  # Cuban red
        light="#EF5350",
        dark="#C62828",
        contrast_text="#FFFFFF"
    ),
    secondary=ColorScale(
        main="#1E88E5",  # Cuban blue
        light="#42A5F5",
        dark="#1565C0",
        contrast_text="#FFFFFF"
    ),
    success=ColorScale(main="#43A047", contrast_text="#FFFFFF"),
    warning=ColorScale(main="#FB8C00", contrast_text="#FFFFFF"),
    error=ColorScale(main="#E53935", contrast_text="#FFFFFF"),
    info=ColorScale(main="#1E88E5", contrast_text="#FFFFFF"),
    background="#FFFBF0",  # Warm white
    surface="#FFFFFF",
    surface_elevated="#FFF8E1",
    text_primary="#212121",
    text_secondary="#616161",
    border="#FFCC80",
    border_dark="#FFB74D",
    divider="#FFF3E0",
    custom_vars={
        "--color-accent": "#FFC107",  # Cuban gold/yellow
        "--color-cuban-red": "#E53935",
        "--color-cuban-blue": "#1E88E5",
        "--color-cuban-star": "#FFFFFF",
    }
)


class ThemeManager:
    """
    Manages themes for A2UI components.
    Handles theme registration, switching, and propagation.
    """
    
    def __init__(self):
        self._themes: Dict[str, ThemeDefinition] = {}
        self._active_theme_id: str = "default-light"
        self._theme_change_callbacks: List[Callable[[ThemeDefinition], None]] = []
        
        # Register default themes
        self._register_default_themes()
    
    def _register_default_themes(self) -> None:
        """Register built-in themes."""
        self._themes["default-light"] = DEFAULT_LIGHT_THEME
        self._themes["default-dark"] = DEFAULT_DARK_THEME
        self._themes["cuban"] = CUBAN_THEME
    
    def register_theme(self, theme: ThemeDefinition) -> bool:
        """
        Register a new theme.
        
        Args:
            theme: ThemeDefinition to register
            
        Returns:
            True if registration successful
        """
        try:
            self._themes[theme.theme_id] = theme
            logger.info("theme_registered", theme_id=theme.theme_id)
            return True
        except Exception as e:
            logger.error("theme_registration_failed", error=str(e))
            return False
    
    def get_theme(self, theme_id: str) -> Optional[ThemeDefinition]:
        """Get a theme by ID."""
        return self._themes.get(theme_id)
    
    def get_active_theme(self) -> ThemeDefinition:
        """Get the currently active theme."""
        return self._themes.get(self._active_theme_id, DEFAULT_LIGHT_THEME)
    
    def set_active_theme(self, theme_id: str) -> bool:
        """
        Set the active theme.
        
        Args:
            theme_id: ID of theme to activate
            
        Returns:
            True if theme was activated
        """
        if theme_id not in self._themes:
            logger.warning("theme_not_found", theme_id=theme_id)
            return False
        
        self._active_theme_id = theme_id
        theme = self._themes[theme_id]
        
        # Notify callbacks
        for callback in self._theme_change_callbacks:
            try:
                callback(theme)
            except Exception as e:
                logger.error("theme_change_callback_failed", error=str(e))
        
        logger.info("theme_activated", theme_id=theme_id)
        return True
    
    def get_all_themes(self) -> List[ThemeDefinition]:
        """Get all registered themes."""
        return list(self._themes.values())
    
    def get_themes_by_mode(self, mode: ThemeMode) -> List[ThemeDefinition]:
        """Get themes filtered by mode."""
        return [t for t in self._themes.values() if t.mode == mode]
    
    def on_theme_change(self, callback: Callable[[ThemeDefinition], None]) -> None:
        """Register a callback for theme changes."""
        self._theme_change_callbacks.append(callback)
    
    def create_custom_theme(
        self,
        theme_id: str,
        theme_name: str,
        base_theme_id: str = "default-light",
        overrides: Optional[Dict[str, Any]] = None
    ) -> Optional[ThemeDefinition]:
        """
        Create a custom theme based on an existing one.
        
        Args:
            theme_id: Unique ID for new theme
            theme_name: Display name for new theme
            base_theme_id: ID of theme to base on
            overrides: Property overrides
            
        Returns:
            New ThemeDefinition or None if base not found
        """
        base_theme = self._themes.get(base_theme_id)
        if not base_theme:
            logger.warning("base_theme_not_found", base_theme_id=base_theme_id)
            return None
        
        # Create new theme from base
        base_dict = base_theme.dict()
        base_dict.update({
            "theme_id": theme_id,
            "theme_name": theme_name,
            "variant": ThemeVariant.CUSTOM
        })
        
        if overrides:
            base_dict.update(overrides)
        
        new_theme = ThemeDefinition(**base_dict)
        self.register_theme(new_theme)
        
        return new_theme
    
    def get_theme_css(self, theme_id: Optional[str] = None) -> str:
        """Get CSS for a theme (or active theme if not specified)."""
        if theme_id:
            theme = self._themes.get(theme_id, DEFAULT_LIGHT_THEME)
        else:
            theme = self.get_active_theme()
        return theme.to_css()
    
    def get_theme_manifest(self) -> Dict[str, Any]:
        """Get theme manifest for client consumption."""
        return {
            "active_theme": self._active_theme_id,
            "available_themes": [
                {
                    "id": t.theme_id,
                    "name": t.theme_name,
                    "variant": t.variant,
                    "mode": t.mode
                }
                for t in self._themes.values()
            ]
        }


# Singleton instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the singleton theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
