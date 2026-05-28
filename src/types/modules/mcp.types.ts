/**
 * MCP Types - Tipos relacionados con MCP Servers
 * 
 * SRP: Solo tipos MCP
 * OCP: Extensible sin modificar
 */

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  transport: 'stdio' | 'http' | 'websocket';
  command?: string;
  url?: string;
  tools: MCPTool[];
  resources: MCPResource[];
  status: 'connected' | 'disconnected' | 'error';
  last_connected?: string;
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export interface MCPResource {
  uri: string;
  name: string;
  description: string;
  mime_type?: string;
}
