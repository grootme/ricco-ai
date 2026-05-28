/**
 * Role Types - Tipos relacionados con roles IOVBA
 * 
 * SRP: Solo tipos de roles
 * OCP: Extensible sin modificar
 */

export interface RoleBrand {
  role: string;
  elegantName: string;
  tagline: string;
  description: string;
  icon: string;
  color: string;
  gradient: string;
}

export type IOVBARole = 'investigador' | 'observador' | 'validador' | 'builder' | 'asistente';

export const DEFAULT_ROLE: IOVBARole = 'asistente';
