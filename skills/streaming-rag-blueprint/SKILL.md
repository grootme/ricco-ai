# Streaming Data to RAG Blueprint Skill

Real-time RAG system for processing live data streams with GPU-accelerated SDR pipeline.

## Description

This skill enables RAG systems to process live data streams in real-time. Features a GPU-accelerated software-defined radio (SDR) pipeline that continuously captures RF signals, transcribes them, embeds, and indexes them in real-time.

## When to Use

- Real-time data ingestion and RAG
- Radio frequency signal monitoring
- Emergency response systems
- Live monitoring and surveillance
- Sensor data processing
- Smart spaces and predictive maintenance

## Blueprint Source

Based on: [NVIDIA streaming-data-to-rag](https://github.com/NVIDIA-AI-Blueprints/streaming-data-to-rag)

## Tools

### Streaming Ingestion Tools

| Tool | Description |
|------|-------------|
| `start_stream_ingestion` | Start real-time data stream ingestion |
| `stop_stream_ingestion` | Stop streaming ingestion |
| `get_stream_status` | Get stream ingestion status |
| `configure_stream` | Configure stream parameters |

### SDR Processing Tools

| Tool | Description |
|------|-------------|
| `process_sdr_signal` | Process SDR signal to text |
| `transcribe_audio_stream` | Transcribe audio stream using ASR |
| `fm_demodulate` | FM demodulation for radio signals |
| `get_sdr_spectrum` | Get SDR spectrum data |

### RAG Tools

| Tool | Description |
|------|-------------|
| `query_streaming_rag` | Query RAG with time-aware filters |
| `ingest_document` | Ingest document into vector store |
| `get_ingestion_status` | Get document ingestion status |
| `query_by_time_window` | Query documents by time range |

### Context-Aware Tools

| Tool | Description |
|------|-------------|
| `set_time_context` | Set temporal context for queries |
| `filter_by_channel` | Filter results by data stream/channel |
| `get_recent_summaries` | Get summaries of recent data |
| `search_with_recency` | Search with recency weighting |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources                                   │
│  ┌───────────────────┐  ┌───────────────────────────────────┐   │
│  │ SDR Hardware      │  │ File Replay (Testing)             │   │
│  │ (RF Signals)      │  │ (Audio Files)                     │   │
│  └───────────────────┘  └───────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │ UDP Baseband I/Q
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Holoscan SDR Pipeline                          │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ GPU-Accelerated Signal Processing                         │   │
│  │ - FM Demodulation                                         │   │
│  │ - Audio Extraction                                        │   │
│  │ - Real-time Processing                                    │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Parakeet 0.6B ASR NIM                          │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ GPU-Accelerated Speech Recognition                        │   │
│  │ - Real-time Transcription                                 │   │
│  │ - Multi-language Support                                  │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Context-Aware RAG                              │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Llama 3.2 Embedding NIM → Milvus Vector DB               │   │
│  │ Neo4j Knowledge Graph                                     │   │
│  │ Time-aware Retrieval                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NeMo Agent Toolkit UI                          │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Real-time Chat Interface                                  │   │
│  │ Transcript History View                                   │   │
│  │ Stream Status Dashboard                                   │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API
NVIDIA_API_KEY=nvapi-xxx

# Model Directory
MODEL_DIRECTORY=~/.cache/nim

# Streaming Configuration
REPLAY_FILES="sample1.mp3,sample2.mp3"
REPLAY_TIME=3600
REPLAY_MAX_FILE_SIZE=50

# Services
MILVUS_HOST=localhost
MILVUS_PORT=19530
NEO4J_URI=bolt://localhost:7687
```

### Integration with DeerFlow

```python
from deerflow.blueprints import StreamingRAGBlueprint

streaming_rag = StreamingRAGBlueprint(
    asr_model="nvidia/parakeet-ctc-0.6b-asr",
    embed_model="nvidia/llama-3.2-nv-embedqa-1b-v2",
    enable_sdr=True
)

# Start streaming ingestion
await streaming_rag.start_stream_ingestion(
    source="udp://0.0.0.0:5000",
    channel_id=0
)

# Query with time context
results = await streaming_rag.query_streaming_rag(
    query="What was discussed in the last 10 minutes?",
    time_window=(600, 0),  # Last 10 minutes
    channel=0
)

# Get recent summaries
summary = await streaming_rag.get_recent_summaries(
    duration_minutes=30,
    channel=0
)
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| Parakeet ASR NIM | 1x T4 | 1x L40S |
| Llama 3.2 Embed | 1x T4 | 1x A100 |
| Holoscan SDR | 1x T4 | 1x A100 |

## Time-Aware Query Examples

```python
# Recent summary
query = "Summarize the last 10 minutes on channel 0"

# Time window
query = "What was discussed on channel 2 between 5 and 15 minutes ago?"

# Specific time
query = "At 9 o'clock, what was the topic on channel 3?"

# Exclude recent
query = "What was discussed excluding the past 10 minutes?"

# Multiple channels
query = "Compare discussions across all channels in the last hour"
```

## Example Usage

```python
from deerflow.tools.streaming_rag import (
    SDRPipeline,
    StreamingIngestion,
    ContextAwareRAG
)

# Initialize SDR pipeline
sdr = SDRPipeline(
    sample_rate=2e6,
    center_freq=100.7e6
)

# Start ingestion
ingestion = StreamingIngestion()
await ingestion.start(
    source=sdr,
    batch_size=100,
    batch_timeout=30
)

# Query with temporal awareness
rag = ContextAwareRAG()
response = await rag.query(
    "What are the main topics discussed recently?",
    time_filter={"last_minutes": 30},
    channel_filter=[0, 1]
)

# Stop ingestion
await ingestion.stop()
```

## Deployment

### Docker Compose
```bash
# Initialize submodules
git submodule update --init --recursive

# Build images
docker compose -f deploy/docker-compose.yaml --profile replay build

# Deploy
docker compose -f deploy/docker-compose.yaml --profile replay up -d
```

### Services Endpoints
- Frontend: http://localhost:3000
- RAG Retrieval: http://localhost:8000/health
- RAG Ingestion: http://localhost:8001/health
- Milvus: http://localhost:9091/healthz
- Neo4j: http://localhost:7474

## References

- [Context-Aware RAG](https://github.com/NVIDIA/context-aware-rag)
- [NeMo Agent Toolkit UI](https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI)
- [Parakeet ASR NIM](https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr)
- [Llama 3.2 Embedding NIM](https://build.nvidia.com/nvidia/llama-3_2-nv-embedqa-1b-v2)
