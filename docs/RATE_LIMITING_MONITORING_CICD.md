# RICCO AI - Rate Limiting, Monitoring & CI/CD

Este documento describe la implementación de Rate Limiting, Monitoreo y CI/CD para RICCO AI.

## 📊 Rate Limiting

### Descripción

El sistema de Rate Limiting protege la API contra abuso y garantiza un uso justo de los recursos.

### Características

- **Múltiples estrategias**: Sliding Window, Fixed Window, Token Bucket
- **Soporte Redis**: Rate limiting distribuido para múltiples instancias
- **Configuración por ruta**: Límites específicos para cada endpoint
- **Bloqueo automático**: Bloquea clientes que excedan los límites

### Configuración

Variables de entorno:

```bash
# Habilitar/deshabilitar rate limiting
RATE_LIMIT_ENABLED=true

# Límites por defecto
RATE_LIMIT_DEFAULT_REQUESTS=100
RATE_LIMIT_DEFAULT_WINDOW=60

# Límites específicos
RATE_LIMIT_AUTH_REQUESTS=10      # Endpoint de autenticación
RATE_LIMIT_CHAT_REQUESTS=30       # Endpoint de chat
RATE_LIMIT_API_KEY_REQUESTS=1000  # API Keys
```

### Uso Programático

```python
from src.middleware.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    setup_rate_limiting
)

# Configuración personalizada
route_configs = {
    "/api/v1/auth": RateLimitConfig(
        requests=5,
        window_seconds=60,
        block_duration=300  # Bloquear 5 minutos
    ),
    "/api/v1/chat": RateLimitConfig(
        requests=30,
        window_seconds=60
    ),
}

# Inicializar
rate_limiter = setup_rate_limiting(
    app=app,
    redis_url="redis://localhost:6379",
    route_configs=route_configs
)
```

### Headers de Respuesta

```
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703980800
Retry-After: 60
```

### Respuesta de Error (429)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "blocked": false
}
```

---

## 📈 Monitoreo (Prometheus + Grafana)

### Arquitectura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   RICCO API     │────▶│  Prometheus  │────▶│   Grafana   │
│   /metrics      │     │   :9090      │     │   :3002     │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                     │                    │
         │                     ▼                    │
         │              ┌──────────────┐            │
         │              │ Alertmanager │◀───────────┘
         │              │   :9093      │
         │              └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│     Jaeger      │     │    Loki      │
│   Tracing       │     │   Logs       │
│   :16686        │     │   :3100      │
└─────────────────┘     └──────────────┘
```

### Métricas Disponibles

#### HTTP
- `ricco_http_requests_total` - Total de requests HTTP
- `ricco_http_request_duration_seconds` - Duración de requests
- `ricco_http_requests_in_progress` - Requests en progreso

#### Agentes
- `ricco_agent_requests_total` - Total de requests de agentes
- `ricco_agent_execution_duration_seconds` - Tiempo de ejecución
- `ricco_agent_active_sessions` - Sesiones activas

#### MCP
- `ricco_mcp_tool_invocations_total` - Invocaciones de tools
- `ricco_mcp_tool_duration_seconds` - Duración de tools
- `ricco_mcp_server_health` - Salud de servidores MCP

#### LLM
- `ricco_llm_requests_total` - Total de requests LLM
- `ricco_llm_tokens_used_total` - Tokens utilizados
- `ricco_llm_cost_total_dollars` - Costo total

#### Rate Limiting
- `ricco_rate_limit_total` - Total de checks de rate limit
- `ricco_rate_limit_active_blocks` - Bloqueos activos

### Iniciar Stack de Monitoreo

```bash
# Iniciar todos los servicios
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Verificar servicios
docker-compose ps

# Acceder a interfaces
open http://localhost:9090  # Prometheus
open http://localhost:3002  # Grafana (admin/ricco_admin)
open http://localhost:9093  # Alertmanager
open http://localhost:16686 # Jaeger
```

### Dashboards Preconfigurados

1. **RICCO AI Overview** - Vista general del sistema
   - Request rate
   - Error rate
   - Latencia P95
   - Sesiones activas

2. **Agent Performance** - Métricas de agentes
   - Tiempo de ejecución
   - Errores por tipo
   - Memoria utilizada

3. **LLM Usage** - Uso de modelos
   - Tokens por modelo
   - Costos
   - Latencia por proveedor

### Alertas Configuradas

| Alerta | Severidad | Condición |
|--------|-----------|-----------|
| InstanceDown | Critical | Servicio caído > 1min |
| HighErrorRate | Warning | Error rate > 5% |
| SlowResponses | Warning | P95 latencia > 2s |
| AgentErrorRateHigh | Critical | Errores agentes > 10% |
| LLMHighLatency | Warning | Latencia LLM > 30s |
| HighRateLimitBlocks | Warning | Bloqueos > 10/seg |
| RateLimitAbuse | Critical | > 1000 bloqueos/hora |
| HighMemoryUsage | Critical | Memoria > 90% |
| DiskSpaceLow | Critical | Disco < 10% |

---

## 🔄 CI/CD Pipeline

### Workflows de GitHub Actions

#### CI Pipeline (`.github/workflows/ci.yml`)

Se ejecuta en cada push y PR:

```
┌──────────┐    ┌───────────┐    ┌─────────────┐    ┌──────────────┐
│   Lint   │───▶│  Security │───▶│ Test Python │───▶│ Test Frontend│
└──────────┘    └───────────┘    └─────────────┘    └──────────────┘
                                          │                  │
                                          ▼                  ▼
                                   ┌─────────────┐    ┌──────────────┐
                                   │ Integration │    │ Build Docker │
                                   └─────────────┘    └──────────────┘
```

**Jobs:**
1. **Lint** - Calidad de código (Ruff, Black, isort, MyPy)
2. **Security** - Análisis de seguridad (Bandit, Safety)
3. **Test Python** - Tests unitarios con cobertura
4. **Test Frontend** - Tests y build de Next.js
5. **Integration** - Tests de integración con servicios
6. **Build Docker** - Build de imágenes Docker

#### CD Pipeline (`.github/workflows/cd.yml`)

Despliegue automático:

```
main/release ───▶ Production
develop ────────▶ Staging
workflow_dispatch ─▶ Manual
```

**Proceso:**
1. Build de imágenes (backend + frontend)
2. Push a GitHub Container Registry
3. Deploy a Kubernetes
4. Health checks
5. Rollback automático si falla

### Configuración de Secrets

```yaml
# GitHub Secrets requeridos
DOCKERHUB_USERNAME: usuario_docker
DOCKERHUB_TOKEN: token_docker
KUBE_CONFIG_STAGING: base64_kubeconfig_staging
KUBE_CONFIG_PRODUCTION: base64_kubeconfig_production
```

### Comandos Útiles

```bash
# Ejecutar CI localmente
act push

# Build manual de imagen
docker build -t ricco-ai:latest .

# Deploy manual
kubectl apply -f k8s/

# Rollback
kubectl rollout undo deployment/ricco-backend
```

---

## 🚀 Inicio Rápido

### 1. Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Iniciar servicios de infraestructura
docker-compose up -d

# Iniciar aplicación
uvicorn src.main:app --reload
```

### 2. Con Monitoreo

```bash
# Iniciar todo el stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Verificar métricas
curl http://localhost:8000/metrics

# Acceder a Grafana
open http://localhost:3002
# Usuario: admin
# Contraseña: ricco_admin
```

### 3. Producción

```bash
# Build de imágenes
docker build -t ricco-ai/backend:latest .
docker build -t ricco-ai/frontend:latest ./ecosystem/ricco-ai/frontend

# Push a registry
docker push ricco-ai/backend:latest
docker push ricco-ai/frontend:latest

# Deploy
kubectl apply -f k8s/
```

---

## 📁 Estructura de Archivos

```
/home/z/my-project/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI Pipeline
│       └── cd.yml              # CD Pipeline
├── src/
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limiter.py     # Rate Limiting
│   ├── monitoring/
│   │   ├── __init__.py
│   │   └── metrics.py          # Prometheus Metrics
│   ├── config/
│   │   └── settings.py         # Configuración
│   └── main.py                 # Aplicación principal
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml      # Config Prometheus
│   │   └── alerts/
│   │       └── ricco_alerts.yml
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   ├── datasources/
│   │   │   └── dashboards/
│   │   └── dashboards/
│   │       └── ricco-overview.json
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   ├── loki/
│   │   └── loki-config.yml
│   └── promtail/
│       └── promtail-config.yml
├── docker-compose.yml
├── docker-compose.monitoring.yml
└── requirements.txt
```

---

## 🔧 Troubleshooting

### Rate Limiting no funciona

```bash
# Verificar que Redis esté corriendo
docker-compose ps redis

# Verificar logs
docker-compose logs ricco-backend | grep rate
```

### Métricas no aparecen en Prometheus

```bash
# Verificar endpoint de métricas
curl http://localhost:8000/metrics

# Verificar configuración de Prometheus
curl http://localhost:9090/api/v1/targets
```

### Alertas no se envían

```bash
# Verificar Alertmanager
curl http://localhost:9093/-/healthy

# Verificar configuración
curl http://localhost:9093/api/v2/status
```

### CI falla

```bash
# Ejecutar tests localmente
pytest tests/ -v

# Verificar linting
ruff check src/
black --check src/
```

---

## 📚 Referencias

- [FastAPI Rate Limiting](https://github.com/long2ice/fastapi-limiter)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [GitHub Actions](https://docs.github.com/en/actions)
