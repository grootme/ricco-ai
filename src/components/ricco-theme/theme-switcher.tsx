'use client';

import * as React from 'react';
import { Check, Moon, Sun, Palette } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useRiccoTheme } from '@/lib/ricco-theme/theme-context';
import { availableThemes } from '@/lib/ricco-theme/theme-config';

export function ThemeSwitcher() {
  const { theme, themeId, mode, setTheme, toggleMode } = useRiccoTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" className="relative">
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Palette className="h-4 w-4" />
          RICCO Theme
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Mode Toggle */}
        <DropdownMenuItem onClick={toggleMode} className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            {mode === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            {mode === 'dark' ? 'Dark Mode' : 'Light Mode'}
          </span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Theme Selection */}
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Select Theme
        </DropdownMenuLabel>
        {availableThemes.map((t) => (
          <DropdownMenuItem
            key={t.id}
            onClick={() => setTheme(t.id)}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <div
                className="h-4 w-4 rounded-full border"
                style={{
                  background: `hsl(${t.colors.light.primary})`,
                }}
              />
              <div>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-muted-foreground">{t.description}</div>
              </div>
            </div>
            {themeId === t.id && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Compact theme toggle for mobile/header
export function ThemeToggle() {
  const { mode, toggleMode } = useRiccoTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleMode}
      className="h-9 w-9"
    >
      {mode === 'dark' ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}

// Theme selector without mode toggle
export function ThemeSelector() {
  const { themeId, setTheme } = useRiccoTheme();

  return (
    <div className="grid grid-cols-2 gap-2">
      {availableThemes.map((t) => (
        <button
          key={t.id}
          onClick={() => setTheme(t.id)}
          className={`
            flex items-center gap-2 p-3 rounded-lg border transition-all
            ${themeId === t.id
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50'
            }
          `}
        >
          <div
            className="h-6 w-6 rounded-full border"
            style={{
              background: `hsl(${t.colors.light.primary})`,
            }}
          />
          <span className="text-sm font-medium">{t.name}</span>
        </button>
      ))}
    </div>
  );
}
