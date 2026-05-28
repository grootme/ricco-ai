# Nemotron Voice Agent Blueprint Skill

End-to-end voice agent blueprint with NVIDIA Nemotron ASR, LLM, and TTS for real-time streaming conversations.

## Description

This skill provides tools for building cascaded voice AI pipelines with streaming, interruptible conversations. Integrates Nemotron ASR (Parakeet), LLM (Nemotron), and TTS (Magpie) using the Pipecat framework with WebRTC transport.

## When to Use

- Real-time voice assistants
- Customer service voice bots
- Interactive voice response (IVR) systems
- Voice-enabled applications
- Multilingual voice interactions
- Edge deployment voice agents

## Blueprint Source

Based on: [NVIDIA nemotron-voice-agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent)

## Tools

### Speech Recognition (ASR) Tools

| Tool | Description |
|------|-------------|
| `transcribe_audio` | Transcribe audio using Parakeet ASR |
| `transcribe_streaming` | Real-time streaming transcription |
| `detect_language` | Detect spoken language |
| `get_asr_model_info` | Get ASR model information |

### Speech Synthesis (TTS) Tools

| Tool | Description |
|------|-------------|
| `synthesize_speech` | Convert text to speech using Magpie TTS |
| `synthesize_streaming` | Streaming TTS synthesis |
| `set_voice_profile` | Set voice characteristics |
| `list_available_voices` | List available TTS voices |
| `get_tts_model_info` | Get TTS model information |

### LLM Tools

| Tool | Description |
|------|-------------|
| `chat_completion` | LLM chat completion |
| `streaming_chat` | Streaming chat response |
| `set_system_prompt` | Set agent system prompt |
| `get_available_models` | List available LLM models |

### Pipeline Tools

| Tool | Description |
|------|-------------|
| `create_voice_pipeline` | Create voice agent pipeline |
| `start_conversation` | Start voice conversation session |
| `end_conversation` | End conversation session |
| `enable_interruption` | Enable/disable user interruption |
| `configure_speculative_speech` | Configure speculative speech processing |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Client (WebRTC)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Microphone Input  →  Audio Stream  →  Speaker Output      │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │ WebRTC Transport
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Pipecat Framework                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Voice Pipeline                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │  │
│  │  │ ASR Service │ │ LLM Service │ │ TTS Service         │   │  │
│  │  │ (Parakeet)  │ │ (Nemotron)  │ │ (Magpie)            │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Speculative Speech Processing (optional)             │  │  │
│  │  │ - Predict user intent before speech completes        │  │  │
│  │  │ - Reduce latency by pre-generating responses         │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NVIDIA NIM Services                            │
│  ┌───────────────────────┐  ┌───────────────────────────────┐     │
│  │ Parakeet CTC 1.1B ASR │  │ Parakeet 1.1B RNNT           │     │
│  │ (GPU 0 - 48GB VRAM)   │  │ Multilingual ASR             │     │
│  └───────────────────────┘  └───────────────────────────────┘     │
│  ┌───────────────────────┐  ┌───────────────────────────────┐     │
│  │ Magpie TTS            │  │ Nemotron 3 Nano 30B          │     │
│  │ Multilingual          │  │ (GPU 1 - 48GB VRAM)          │     │
│  └───────────────────────┘  └───────────────────────────────┘     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Llama 3.3 Nemotron Super 49B v1.5 (GPU 1 - 80GB VRAM)     │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API
NVIDIA_API_KEY=nvapi-xxx
NGC_API_KEY=nvapi-xxx

# Model Configuration
ASR_MODEL=nvidia/parakeet-ctc-1.1b-asr
TTS_MODEL=nvidia/magpie-tts-multilingual
LLM_MODEL=nvidia/nemotron-3-nano-30b-a3b

# Pipeline Configuration
ENABLE_SPECULATIVE_SPEECH=true
INTERRUPTION_ENABLED=true
WEBRTC_ICE_SERVERS=stun:stun.l.google.com:19302
```

### Integration with DeerFlow

```python
from deerflow.blueprints import VoiceAgentBlueprint

voice_agent = VoiceAgentBlueprint(
    asr_model="nvidia/parakeet-ctc-1.1b-asr",
    llm_model="nvidia/nemotron-3-nano-30b-a3b",
    tts_model="nvidia/magpie-tts-multilingual",
    enable_interruption=True
)

# Start voice conversation
session = await voice_agent.start_conversation(
    system_prompt="You are a helpful customer service assistant."
)

# Process audio
response = await voice_agent.process_audio(audio_stream)

# End conversation
await voice_agent.end_conversation(session.id)
```

## GPU Requirements

| Component | Minimum GPU | VRAM |
|-----------|-------------|------|
| ASR + TTS (GPU 0) | 1x A100 | 48 GB |
| Nemotron Nano 30B (GPU 1) | 1x A100 | 48 GB |
| Nemotron Super 49B (GPU 1) | 1x H100 | 80 GB |

**Total:** 2 GPUs required (Ampere, Hopper, Ada, or later)

## Performance Optimization

### Speculative Speech Processing
Reduces latency by predicting user intent before speech completes:

```python
voice_agent.configure_speculative_speech(
    enabled=True,
    min_audio_chunks=3,
    confidence_threshold=0.8
)
```

### Multilingual Support

```python
# Enable multilingual with auto-detection
voice_agent = VoiceAgentBlueprint(
    asr_model="nvidia/parakeet-1.1b-rnnt-multilingual-asr",
    auto_detect_language=True
)
```

## Example Usage

```python
from deerflow.tools.voice import VoicePipeline, ASRService, LLMService, TTSService

# Create services
asr = ASRService(model="parakeet-ctc-1.1b")
llm = LLMService(model="nemotron-3-nano-30b")
tts = TTSService(model="magpie-tts-multilingual")

# Create pipeline
pipeline = VoicePipeline(
    asr=asr,
    llm=llm,
    tts=tts,
    enable_interruption=True
)

# Start session
async with pipeline.session() as session:
    # User speaks
    async for response in session.process_stream(audio_stream):
        # Response audio plays
        speaker.play(response.audio)
```

## Deployment Options

### Docker Compose
```bash
docker compose up -d
# Access at http://localhost:9000
```

### Jetson Thor (Edge)
```bash
docker compose -f docker-compose.jetson.yml up -d
```

## References

- [Parakeet ASR Model Card](https://build.nvidia.com/nvidia/parakeet-ctc-1_1b-asr/modelcard)
- [Magpie TTS Model Card](https://build.nvidia.com/nvidia/magpie-tts-multilingual/modelcard)
- [Nemotron LLM Models](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/modelcard)
- [Pipecat Framework](https://github.com/pipecat-ai/pipecat)
