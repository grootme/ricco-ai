'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Check,
  X,
  Settings,
  Palette,
  Monitor,
  Moon,
  Sun,
  Building2,
  ShoppingCart,
  MessageSquare,
  CreditCard,
  BarChart3,
  Users,
  Package,
  LayoutDashboard
} from 'lucide-react';
import { useRiccoTheme } from '@/lib/ricco-theme/theme-context';
import { availableThemes } from '@/lib/ricco-theme/theme-config';

export function ThemePreview() {
  const { theme, themeId, mode, setTheme, setMode, toggleMode } = useRiccoTheme();

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Palette className="h-5 w-5" />
          Theme Preview
        </CardTitle>
        <CardDescription>
          Preview how your RICCO ERP will look with different themes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Current Theme Info */}
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
            <div>
              <div className="font-semibold">{theme.name}</div>
              <div className="text-sm text-muted-foreground">{theme.description}</div>
            </div>
            <Badge variant="secondary">{mode}</Badge>
          </div>

          {/* Color Preview */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Color Palette</h4>
            <div className="grid grid-cols-6 gap-2">
              {Object.entries(theme.colors[mode]).slice(0, 12).map(([key, value]) => (
                <div key={key} className="text-center">
                  <div
                    className="h-10 w-10 rounded-lg border mx-auto mb-1"
                    style={{ background: `hsl(${value})` }}
                  />
                  <div className="text-xs text-muted-foreground capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sample Components */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Component Preview</h4>
            <div className="flex flex-wrap gap-2">
              <Button>Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="destructive">Destructive</Button>
              <Badge>Badge</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ThemeGallery() {
  const { themeId, setTheme, mode } = useRiccoTheme();

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {availableThemes.map((t) => (
        <Card
          key={t.id}
          className={`cursor-pointer transition-all hover:shadow-lg ${
            themeId === t.id ? 'ring-2 ring-primary' : ''
          }`}
          onClick={() => setTheme(t.id)}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{t.name}</CardTitle>
              {themeId === t.id && <Check className="h-5 w-5 text-primary" />}
            </div>
            <CardDescription className="text-xs">{t.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* Color Swatches */}
              <div className="flex gap-1">
                <div
                  className="h-8 flex-1 rounded-l-lg border"
                  style={{ background: `hsl(${t.colors[mode].primary})` }}
                />
                <div
                  className="h-8 flex-1 border"
                  style={{ background: `hsl(${t.colors[mode].secondary})` }}
                />
                <div
                  className="h-8 flex-1 border"
                  style={{ background: `hsl(${t.colors[mode].accent})` }}
                />
                <div
                  className="h-8 flex-1 rounded-r-lg border"
                  style={{ background: `hsl(${t.colors[mode].background})` }}
                />
              </div>

              {/* Sample Button */}
              <Button
                className="w-full"
                style={{
                  '--primary': t.colors[mode].primary,
                } as React.CSSProperties}
              >
                Use This Theme
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function ThemeSettings() {
  const { theme, themeId, mode, setTheme, setMode, toggleMode, resetTheme } = useRiccoTheme();

  return (
    <div className="space-y-6">
      {/* Mode Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Color Mode
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Sun className="h-5 w-5" />
              <Label htmlFor="dark-mode">Dark Mode</Label>
              <Moon className="h-5 w-5" />
            </div>
            <Switch
              id="dark-mode"
              checked={mode === 'dark'}
              onCheckedChange={toggleMode}
            />
          </div>
        </CardContent>
      </Card>

      {/* Theme Gallery */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Select Theme
          </CardTitle>
          <CardDescription>Choose a theme for your RICCO ERP</CardDescription>
        </CardHeader>
        <CardContent>
          <ThemeGallery />
        </CardContent>
      </Card>

      {/* Reset */}
      <div className="flex justify-end">
        <Button variant="outline" onClick={resetTheme}>
          Reset to Default
        </Button>
      </div>
    </div>
  );
}
