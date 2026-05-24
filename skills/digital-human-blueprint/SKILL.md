# Digital Human Blueprint Skill

## Overview
NVIDIA Digital Human Blueprint integration for creating interactive, AI-powered virtual humans with realistic facial animation, speech synthesis, and conversational intelligence.

## Description
This skill provides tools for building digital human applications with lifelike avatars that can engage in natural conversations. It includes:

- **Avatar Management**: Create and customize 3D avatars
- **Facial Animation**: Realistic facial expressions and lip-sync
- **Speech Synthesis**: High-quality TTS with emotional variation
- **Conversation AI**: Natural dialogue with context awareness
- **Animation Control**: Gesture and body movement coordination

## Tools (14)

### digitalhuman_init
Initialize a digital human system.

**Parameters:**
- `system_name` (required): Name for the digital human instance
- `avatar_type` (required): '3d', '2d', or 'realistic'
- `render_quality` (optional): 'low', 'medium', 'high', or 'ultra'
- `voice_provider` (optional): 'nvidia', 'elevenlabs', or 'azure'

### digitalhuman_create_avatar
Create a new avatar configuration.

**Parameters:**
- `avatar_name` (required): Name for the avatar
- `appearance` (required): Appearance configuration object
- `personality` (optional): Personality traits
- `voice_id` (optional): Voice identifier
- `default_expression` (optional): Default facial expression

### digitalhuman_set_appearance
Configure avatar appearance.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `gender` (optional): 'male', 'female', or 'neutral'
- `age` (optional): Apparent age range
- `ethnicity` (optional): Ethnic appearance
- `hair_style` (optional): Hair configuration
- `clothing` (optional): Outfit configuration
- `accessories` (optional): Accessories (glasses, jewelry, etc.)

### digitalhuman_set_expression
Set avatar facial expression.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `expression` (required): Expression name or blend weights
- `intensity` (optional): Expression intensity (0.0-1.0)
- `transition_duration` (optional): Transition time in seconds
- `hold_duration` (optional): How long to hold the expression

### digitalhuman_animate_speech
Animate avatar speaking.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `text` (required): Text to speak
- `voice_emotion` (optional): Emotion for speech
- `speaking_rate` (optional): Speech speed multiplier
- `gesture_mode` (optional): 'none', 'automatic', or 'custom'
- `gestures` (optional): List of gestures to perform

### digitalhuman_synthesize_speech
Synthesize speech audio.

**Parameters:**
- `text` (required): Text to synthesize
- `voice_id` (optional): Voice identifier
- `emotion` (optional): Emotional tone
- `speed` (optional): Speech rate
- `pitch` (optional): Voice pitch adjustment
- `output_format` (optional): 'wav', 'mp3', or 'ogg'

### digitalhuman_listen
Process audio input for conversation.

**Parameters:**
- `audio_data` (required): Audio input (base64 or file path)
- `language` (optional): Language code (default: 'en-US')
- `enable_sentiment` (optional): Enable sentiment analysis
- `enable_intent` (optional): Enable intent detection

### digitalhuman_respond
Generate conversational response.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `user_input` (required): User's message
- `context` (optional): Conversation context
- `response_style` (optional): 'formal', 'casual', 'empathetic'
- `include_gestures` (optional): Generate gestures with response

### digitalhuman_set_context
Set conversation context.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `context_type` (required): 'user_profile', 'knowledge', 'session'
- `context_data` (required): Context information
- `priority` (optional): Context priority level

### digitalhuman_create_animation
Create a custom animation sequence.

**Parameters:**
- `animation_name` (required): Name for the animation
- `avatar_name` (required): Target avatar
- `keyframes` (required): List of animation keyframes
- `duration` (optional): Total animation duration
- `loop` (optional): Whether to loop the animation

### digitalhuman_play_animation
Play an animation on the avatar.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `animation_name` (required): Animation to play
- `blend_duration` (optional): Transition blend time
- `speed` (optional): Playback speed multiplier
- `interrupt` (optional): Interrupt current animation

### digitalhuman_stream_session
Start a streaming session.

**Parameters:**
- `avatar_name` (required): Avatar identifier
- `session_type` (required): 'webrtc', 'websocket', or 'rtmp'
- `quality` (optional): Stream quality preset
- `audio_enabled` (optional): Enable audio streaming
- `video_enabled` (optional): Enable video streaming

### digitalhuman_analyze_face
Analyze user's facial expressions (for interaction).

**Parameters:**
- `image_data` (required): Image or video frame
- `detect_emotions` (optional): Enable emotion detection
- `detect_gaze` (optional): Enable gaze tracking
- `detect_engagement` (optional): Enable engagement analysis

### digitalhuman_get_metrics
Get digital human performance metrics.

**Parameters:**
- `avatar_name` (optional): Specific avatar or 'all'
- `metrics_type` (optional): 'performance', 'engagement', or 'all'
- `time_range` (optional): Time range for metrics

## Avatar Appearance Configuration

### Basic Appearance
```json
{
  "gender": "female",
  "age": "young_adult",
  "ethnicity": "mixed",
  "body_type": "average"
}
```

### Detailed Face Configuration
```json
{
  "face": {
    "shape": "oval",
    "skin_tone": "medium",
    "eye_color": "brown",
    "eye_shape": "almond",
    "nose": "average",
    "lips": "full"
  }
}
```

### Hair Configuration
```json
{
  "hair": {
    "style": "long_wavy",
    "color": "dark_brown",
    "highlights": true
  }
}
```

## Facial Expressions

### Standard Expressions
- `neutral` - Default expression
- `happy` - Smile, raised cheeks
- `sad` - Downturned mouth, lowered eyebrows
- `angry` - Furrowed brows, tightened lips
- `surprised` - Raised eyebrows, wide eyes
- `fearful` - Wide eyes, tense mouth
- `disgusted` - Wrinkled nose, curled lip
- `contempt` - Asymmetric sneer

### Blend Shapes (ARKit compatible)
```
eyeBlinkLeft, eyeBlinkRight, jawOpen, mouthClose,
mouthSmileLeft, mouthSmileRight, browDownLeft, browDownRight,
browUpLeft, browUpRight, cheekPuff, cheekSquintLeft, ...
```

## Speech Configuration

### NVIDIA TTS Voices
- `nvidia_female_1` - Professional female voice
- `nvidia_male_1` - Professional male voice
- `nvidia_neutral_1` - Gender-neutral voice

### Emotion Modifiers
```json
{
  "emotion": "empathetic",
  "emotion_intensity": 0.7,
  "speaking_style": "conversational"
}
```

### SSML Support
```xml
<speak>
  Hello! <emphasis level="strong">Welcome</emphasis> to our service.
  <break time="500ms"/> How can I help you today?
</speak>
```

## Conversation Patterns

### Greeting Flow
```
1. digitalhuman_analyze_face(user_image) → Detect user presence
2. digitalhuman_set_expression(avatar, "happy", 0.6)
3. digitalhuman_animate_speech(avatar, "Hello! Welcome!")
```

### Active Listening
```
1. digitalhuman_listen(user_audio) → Transcribe and understand
2. digitalhuman_set_expression(avatar, "attentive")
3. digitalhuman_respond(avatar, user_input)
```

### Empathetic Response
```
1. digitalhuman_listen(user_audio, enable_sentiment=true)
2. Detect sentiment: "frustrated"
3. digitalhuman_set_expression(avatar, "concerned")
4. digitalhuman_respond(avatar, input, style="empathetic")
```

## Integration with NVIDIA ACE

This skill integrates with NVIDIA ACE (Avatar Cloud Engine):

- **Audio2Face**: Automatic facial animation from audio
- **Riva**: Speech synthesis and recognition
- **Maxine**: Video enhancement SDK
- **Omniverse**: 3D avatar rendering

## Streaming Configuration

### WebRTC Setup
```javascript
const session = digitalhuman_stream_session(
  avatar_name="assistant",
  session_type="webrtc",
  quality="high"
);
```

### Quality Presets
| Preset | Resolution | FPS | Bitrate |
|--------|------------|-----|---------|
| Low | 480p | 15 | 500kbps |
| Medium | 720p | 24 | 1.5Mbps |
| High | 1080p | 30 | 3Mbps |
| Ultra | 4K | 60 | 8Mbps |

## Usage Examples

### Customer Service Avatar
```
1. digitalhuman_init(system_name="support", avatar_type="realistic")
2. digitalhuman_create_avatar(avatar_name="Sarah", appearance={...})
3. digitalhuman_set_context(avatar_name="Sarah", context_type="knowledge", 
                            context_data={products, policies})
4. digitalhuman_stream_session(avatar_name="Sarah", session_type="webrtc")
```

### Virtual Presenter
```
1. digitalhuman_init(system_name="presenter", avatar_type="3d")
2. digitalhuman_create_avatar(avatar_name="Alex", appearance={...})
3. digitalhuman_create_animation(animation_name="present", keyframes=[...])
4. digitalhuman_animate_speech(avatar_name="Alex", 
                               text="Welcome to our presentation",
                               gesture_mode="automatic")
```

## References

- [NVIDIA ACE Documentation](https://developer.nvidia.com/ace)
- [Audio2Face Guide](./references/audio2face.md)
- [Riva TTS/ASR](./references/riva.md)
- [Avatar Animation](./references/animation.md)
