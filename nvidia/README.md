# NVIDIA Autonomous Digital Infrastructure Ecosystem

This directory contains NVIDIA repositories for building autonomous digital infrastructure.

## Directory Structure

```
nvidia/
├── ai-blueprints/          # 11 NVIDIA AI Blueprint repositories
├── core-frameworks/        # 6 Core AI frameworks (NeMo, Megatron, etc.)
├── inference-optimization/ # 3 Inference & optimization repos
├── physical-ai/            # 3 Physical AI repos (Cosmos, Isaac)
├── workflow-infra/         # 5 Workflow & infrastructure repos
└── docs/                   # Documentation and research
```

## Repositories Summary

### AI Blueprints (11 repos)
| Repository | Description |
|------------|-------------|
| aiq | AI-Q NVIDIA Blueprint - Enterprise research agent |
| data-flywheel | Autonomous Data Flywheel service |
| rag | RAG Blueprint - Retrieval Augmented Generation |
| video-search-and-summarization | Video analytics AI agents |
| ai-virtual-assistant | Virtual assistant for customer service |
| digital-human | 3D animated digital human interface |
| biomedical-aiq-research-agent | Biomedical research agent |
| ambient-healthcare-agents | Healthcare SOAP note generation |
| Multi-Agent-Intelligent-Warehouse | Multi-agent warehouse system |
| quantitative-portfolio-optimization | Portfolio optimization |
| nim-usage-scanner | NIM usage scanner |

### Core Frameworks (6 repos)
| Repository | Description |
|------------|-------------|
| NeMo-Agent-Toolkit | Agent orchestration framework |
| GenerativeAIExamples | End-to-end AI examples |
| nemo-framework | NVIDIA NeMo Framework |
| Nemotron | Open models for agentic AI |
| Megatron-Bridge | Megatron training library |
| Megatron-LM | Large-scale transformer training |

### Inference & Optimization (3 repos)
| Repository | Description |
|------------|-------------|
| tensorrt | High-performance deep learning inference SDK |
| TensorRT-LLM | TensorRT optimizations for LLMs |
| triton-server | Triton Inference Server |

### Physical AI (3 repos)
| Repository | Description |
|------------|-------------|
| Isaac-GR00T | Generalist Robot model |
| cosmos-predict2.5 | World Foundation Models |
| cosmos-cookbook | Cosmos development cookbook |

### Workflow & Infrastructure (5 repos)
| Repository | Description |
|------------|-------------|
| OpenShell | Safe runtime for autonomous AI agents |
| OpenShell-Community | Community resources for OpenShell |
| OSMO | Workflow scaling platform |
| brev-cli | Cloud GPU instance access |
| langchain-nvidia | LangChain integration with NVIDIA NIM |

## Total: 28 Repositories

## Quick Start

```bash
# Essential for autonomous infrastructure
cd workflow-infra/OpenShell
cd core-frameworks/NeMo-Agent-Toolkit
cd ai-blueprints/aiq
cd ai-blueprints/data-flywheel
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           CAPA 5: AI FÍSICA                  │
│        physical-ai/ (Cosmos, Isaac)          │
├─────────────────────────────────────────────┤
│           CAPA 4: SERVING                    │
│     inference-optimization/ (TensorRT, etc)  │
├─────────────────────────────────────────────┤
│           CAPA 3: BLUEPRINTS                 │
│      ai-blueprints/ (AI-Q, RAG, Flywheel)    │
├─────────────────────────────────────────────┤
│           CAPA 2: FRAMEWORKS                 │
│      core-frameworks/ (NeMo, Megatron)       │
├─────────────────────────────────────────────┤
│           CAPA 1: RUNTIME                    │
│       workflow-infra/ (OpenShell, OSMO)      │
└─────────────────────────────────────────────┘
```

## Sources
- https://github.com/NVIDIA-AI-Blueprints
- https://github.com/NVIDIA
- https://github.com/NVIDIA-NeMo
- https://github.com/nvidia-cosmos

---
*Generated: 2026-04-27*
