/**
 * Testing Types - Tipos relacionados con testing IOVBA
 * 
 * SRP: Solo tipos de testing
 * OCP: Extensible sin modificar
 */

import { IOVBADomain, IOVBARole } from './index';

export type TestLevel = 'basic' | 'intermediate' | 'advanced' | 'expert' | 'master';

export interface IOVBATestCase {
  id: string;
  name: string;
  description: string;
  level: TestLevel;
  domain: IOVBADomain;
  role?: IOVBARole;
  input: Record<string, unknown>;
  expected_output: Record<string, unknown>;
  validation_rules: ValidationRule[];
  timeout_ms: number;
  tags: string[];
}

export interface ValidationRule {
  type: 'exact' | 'contains' | 'regex' | 'semantic' | 'custom';
  field: string;
  value: string | number | boolean | RegExp;
  weight: number;
}

export interface IOVBATestResult {
  test_id: string;
  test_name?: string;
  group_id: string;
  domain?: IOVBADomain;
  elegant_name?: string;
  agent_role?: IOVBARole;
  passed: boolean;
  score: number;
  max_score?: number;
  execution_time_ms: number;
  output: Record<string, unknown>;
  validation_results: ValidationResult[];
  timestamp: string;
}

export interface ValidationResult {
  rule_id: string;
  passed: boolean;
  score: number;
  message: string;
}

export interface IOVBATestSuite {
  id: string;
  name: string;
  description: string;
  domain: IOVBADomain;
  level: TestLevel;
  test_cases: IOVBATestCase[];
  total_tests: number;
  estimated_duration_ms: number;
}

export interface IOVBATestReport {
  suite_id: string;
  suite_name?: string;
  group_id: string;
  domain?: IOVBADomain;
  elegant_name?: string;
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  score: number;
  max_score?: number;
  level_achieved: TestLevel;
  execution_time_ms: number;
  results: IOVBATestResult[];
  recommendations: string[];
  timestamp: string;
}
