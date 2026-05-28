# Ambient Patient Healthcare Agent Blueprint Skill

Voice-enabled healthcare agent for patient intake and clinical staff assistance.

## Description

This skill provides tools for building voice agents that assist patients during the intake process, reducing the burden on clinical staff. Integrates NVIDIA RIVA ASR/TTS, NeMo Guardrails for safety, and ACE Controller for voice orchestration.

## When to Use

- Patient intake automation
- Healthcare front desk assistance
- Appointment scheduling
- Medication information queries
- Voice-based clinical workflows
- Healthcare accessibility solutions

## Blueprint Source

Based on: [NVIDIA ambient-patient](https://github.com/NVIDIA-AI-Blueprints/ambient-patient)

## Tools

### Patient Intake Tools

| Tool | Description |
|------|-------------|
| `start_patient_intake` | Initialize patient intake session |
| `collect_patient_info` | Collect patient demographic information |
| `collect_symptoms` | Collect and document patient symptoms |
| `collect_medical_history` | Gather medical history |
| `verify_insurance` | Verify insurance information |
| `complete_intake` | Finalize intake documentation |

### Appointment Tools

| Tool | Description |
|------|-------------|
| `check_availability` | Check provider availability |
| `schedule_appointment` | Schedule new appointment |
| `reschedule_appointment` | Reschedule existing appointment |
| `cancel_appointment` | Cancel appointment |
| `get_appointment_details` | Get appointment information |

### Medication Tools

| Tool | Description |
|------|-------------|
| `get_medication_info` | Get medication information |
| `check_drug_interactions` | Check for drug interactions |
| `get_dosage_info` | Get dosage instructions |
| `list_side_effects` | List medication side effects |

### Voice Agent Tools

| Tool | Description |
|------|-------------|
| `process_voice_input` | Process voice input via ASR |
| `generate_voice_response` | Generate TTS response |
| `enable_interruption` | Enable interruption handling |
| `set_voice_profile` | Set TTS voice characteristics |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Client (WebRTC)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Voice Interface                                            │  │
│  │ - Microphone Input → ASR → Agent → TTS → Speaker Output   │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │ WebRTC
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    ACE Controller SDK                             │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Voice Pipeline Orchestration                               │   │
│  │ - Connection Management                                    │   │
│  │ - Audio Stream Processing                                  │   │
│  │ - Turn Detection                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent                                │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Specialized Healthcare Agents                              │   │
│  │ - Patient Intake Agent                                     │   │
│  │ - Appointment Agent                                        │   │
│  │ - Medication Information Agent                             │   │
│  │ - Full Combined Agent                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NeMo Guardrails                                │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Content Safety + Topic Control                             │   │
│  │ - Healthcare-specific guardrails                           │   │
│  │ - PII protection                                           │   │
│  │ - Medical disclaimers                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NVIDIA NIM Services                            │
│  ┌───────────────────────┐  ┌───────────────────────────────┐     │
│  │ Llama-3.3-70B         │  │ Parakeet CTC 1.1B ASR        │     │
│  │ Instruct              │  │                               │     │
│  └───────────────────────┘  └───────────────────────────────┘     │
│  ┌───────────────────────┐  ┌───────────────────────────────┐     │
│  │ Magpie TTS            │  │ NeMoGuard Content Safety      │     │
│  │ Multilingual          │  │ + Topic Control               │     │
│  └───────────────────────┘  └───────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API Keys
NVIDIA_API_KEY=nvapi-xxx
NGC_API_KEY=nvapi-xxx

# RIVA Configuration
RIVA_API_URL=https://build.nvidia.com
RIVA_ASR_MODEL=nvidia/parakeet-ctc-1.1b-asr
RIVA_TTS_MODEL=nvidia/magpie-tts-multilingual

# LLM Configuration
LLM_MODEL=meta/llama-3.3-70b-instruct
GUARDRAILS_MODEL=nvidia/llama-3.1-nemoguard-8b-content-safety

# Agent Configuration
ENABLE_GUARDRAILS=true
ENABLE_LANGSMITH=true
```

### Integration with DeerFlow

```python
from deerflow.blueprints import AmbientPatientBlueprint

patient_agent = AmbientPatientBlueprint(
    enable_voice=True,
    enable_guardrails=True,
    agent_type="intake"  # intake, appointment, medication, or full
)

# Start voice intake session
session = await patient_agent.start_session(
    agent_type="patient_intake",
    voice_profile="professional_female"
)

# Process patient interaction
async for response in patient_agent.process_conversation(session):
    print(f"Agent: {response.text}")
    if response.action:
        print(f"Action: {response.action}")

# Complete intake
summary = await patient_agent.complete_intake(session)
print(f"Patient: {summary.patient_name}")
print(f"Symptoms: {summary.symptoms}")
```

## GPU Requirements

### For Hosted NIMs (No local GPU)
- All services via NVIDIA AI Endpoints

### For Local Deployment

| Component | GPU Requirement |
|-----------|-----------------|
| RIVA ASR | Various (L40, A100, etc.) |
| RIVA TTS | Various (L40, A100, etc.) |
| Llama 3.3 70B | 2x H100 80GB or 4x A100 80GB |
| NeMoGuard Content Safety | 1x A100/H100/L40S/A6000 |
| NeMoGuard Topic Control | 1x A100/H100/L40S/A6000 |

**Total:** 8x A100 80GB or equivalent

## Agent Types

### 1. Patient Intake Agent
Guides patients through registration:
- Collect demographic information
- Document symptoms and concerns
- Gather medical history
- Verify insurance

### 2. Appointment Agent
Handles scheduling:
- Check provider availability
- Schedule/reschedule/cancel appointments
- Send reminders

### 3. Medication Information Agent
Provides medication info:
- Drug information
- Dosage instructions
- Side effects
- Drug interactions

### 4. Full Combined Agent
All capabilities in one agent

## Example Usage

```python
from deerflow.tools.healthcare import (
    PatientIntakeAgent,
    VoicePipeline
)

# Create voice pipeline
voice = VoicePipeline(
    asr_model="parakeet-ctc-1.1b",
    tts_model="magpie-tts-multilingual",
    enable_interruption=True
)

# Create intake agent
agent = PatientIntakeAgent(
    llm_model="llama-3.3-70b-instruct",
    enable_guardrails=True
)

# Voice conversation
async with voice.session() as session:
    # Agent greets patient
    await session.speak("Hello! I'll help you with your registration today.")
    
    # Collect patient info
    patient_info = await agent.collect_info(session)
    
    # Document symptoms
    symptoms = await agent.collect_symptoms(session)
    
    # Complete intake
    await agent.complete_intake(patient_info, symptoms)
```

## Guardrails Configuration

```yaml
# rails.co
define user express pain
  "I have severe chest pain"
  "My head hurts a lot"
  "I feel a sharp pain in my stomach"

define flow
  user express pain
  bot suggest seek medical attention immediately
```

## Deployment Options

### Option A: Full Voice Assistant (Recommended)
```bash
# Using public NVIDIA AI Endpoints
docker compose -f docker-compose-public-endpoints.yml up -d
```

### Option B: Chatbot (Development)
```bash
# Text-based Gradio interface
cd agent
python gradio_app.py
```

## References

- [NVIDIA RIVA Documentation](https://docs.nvidia.com/riva/)
- [ACE Controller SDK](https://github.com/NVIDIA/ace-controller)
- [NeMo Guardrails](https://developer.nvidia.com/nemo-guardrails)
- [Llama 3.3 70B Instruct](https://build.nvidia.com/meta/llama-3_3-70b-instruct)
