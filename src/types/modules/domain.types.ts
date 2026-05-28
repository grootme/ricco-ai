/**
 * Domain Types - Tipos relacionados con dominios IOVBA
 * 
 * SRP: Solo tipos de dominio
 * OCP: Extensible sin modificar
 */

export interface DomainBrand {
  domain: string;
  name: string;
  elegantName: string;
  tagline: string;
  icon: string;
  color: string;
  description: string;
}

export type IOVBADomain =
  | 'swe'
  | 'salud'
  | 'deportes'
  | 'noticias'
  | 'quimica'
  | 'biologia'
  | 'biotecnologia'
  | 'geopolitica'
  | 'finanzas'
  | 'legal'
  | 'educacion'
  | 'investigacion'
  | 'marketing'
  | 'custom';

export const DEFAULT_DOMAIN: IOVBADomain = 'custom';
