# Video Search and Summarization Blueprint Skill

## Overview
NVIDIA Video Search and Summarization Blueprint integration for ingesting massive volumes of live or archived videos and extracting insights for summarization and interactive Q&A.

## Description
This skill provides tools for building video analytics AI agents that can process, search, and summarize video content at scale. It supports:

- **Video Ingestion**: Process live streams and archived videos
- **Multi-modal Analysis**: Visual, audio, and text extraction
- **Semantic Search**: Search video content by meaning
- **Summarization**: Generate video summaries and highlights
- **Interactive Q&A**: Query video content with natural language

## Tools (15)

### videosearch_init
Initialize video search system.

**Parameters:**
- `system_name` (required): Name for the video search system
- `storage_backend` (optional): 'milvus', 'qdrant', 'elastic'
- `gpu_enabled` (optional): Enable GPU acceleration
- `max_streams` (optional): Maximum concurrent streams

### videosearch_ingest_video
Ingest a video file.

**Parameters:**
- `video_path` (required): Path to video file
- `metadata` (optional): Video metadata
- `chunk_duration` (optional): Chunk duration in seconds
- `extract_frames` (optional): Extract key frames
- `extract_audio` (optional): Extract and transcribe audio

### videosearch_ingest_stream
Ingest a live video stream.

**Parameters:**
- `stream_url` (required): Stream URL (RTSP, HLS, etc.)
- `stream_name` (required): Name for the stream
- `processing_mode` (optional): 'realtime', 'batch', 'hybrid'
- `buffer_size` (optional): Buffer duration in seconds

### videosearch_extract_frames
Extract key frames from video.

**Parameters:**
- `video_id` (required): Video identifier
- `extraction_mode` (optional): 'keyframes', 'interval', 'scene_change'
- `max_frames` (optional): Maximum frames to extract
- `min_scene_diff` (optional): Minimum scene difference threshold

### videosearch_transcribe
Transcribe audio from video.

**Parameters:**
- `video_id` (required): Video identifier
- `language` (optional): Audio language
- `enable_diarization` (optional): Enable speaker diarization
- `enable_timestamps` (optional): Include word timestamps

### videosearch_detect_objects
Detect objects in video frames.

**Parameters:**
- `video_id` (required): Video identifier
- `object_types` (optional): Types of objects to detect
- `confidence_threshold` (optional): Minimum confidence
- `track_objects` (optional): Enable object tracking

### videosearch_detect_activities
Detect activities/actions in video.

**Parameters:**
- `video_id` (required): Video identifier
- `activity_types` (optional): Activities to detect
- `time_range` (optional): Time range to analyze

### videosearch_extract_text
Extract text (OCR) from video frames.

**Parameters:**
- `video_id` (required): Video identifier
- `languages` (optional): Text languages
- `detect_regions` (optional): Detect text regions only

### videosearch_index_video
Index video for semantic search.

**Parameters:**
- `video_id` (required): Video to index
- `index_visual` (optional): Index visual embeddings
- `index_audio` (optional): Index audio embeddings
- `index_text` (optional): Index text/transcript

### videosearch_search
Search video content.

**Parameters:**
- `query` (required): Search query (text or image)
- `search_mode` (optional): 'semantic', 'keyword', 'hybrid'
- `filters` (optional): Metadata filters
- `top_k` (optional): Number of results

### videosearch_search_by_frame
Search using a frame image.

**Parameters:**
- `frame_image` (required): Frame image to search
- `similarity_threshold` (optional): Minimum similarity
- `max_results` (optional): Maximum results

### videosearch_summarize
Generate video summary.

**Parameters:**
- `video_id` (required): Video to summarize
- `summary_type` (optional): 'brief', 'detailed', 'highlights'
- `max_duration` (optional): Maximum summary duration
- `include_chapters` (optional): Include chapter markers

### videosearch_qa
Ask questions about video content.

**Parameters:**
- `video_id` (required): Video context
- `question` (required): Question to answer
- `include_timestamps` (optional): Include relevant timestamps
- `include_evidence` (optional): Include supporting frames

### videosearch_create_timeline
Create video timeline with events.

**Parameters:**
- `video_id` (required): Video to analyze
- `event_types` (optional): Types of events to detect
- `granularity` (optional): Timeline granularity

### videosearch_export_results
Export search/analysis results.

**Parameters:**
- `result_id` (required): Result to export
- `format` (optional): 'json', 'csv', 'report'
- `include_clips` (optional): Include video clips

## Video Processing Pipeline

### Standard Pipeline
```
Video → Frame Extraction → Multi-modal Analysis → Indexing → Search
       ↓
    Audio → Transcription → NLP → Search
       ↓
    OCR → Text Extraction → Search
```

### Real-time Pipeline
```
Stream → Buffer → Process → Alert/Index
              ↓
         Frame Detection → Event Detection
```

## Supported Video Formats

- MP4, AVI, MOV, MKV
- RTSP, HLS, DASH streams
- WebM, FLV
- DICOM (medical video)

## Analysis Capabilities

### Visual Analysis
- Object detection and tracking
- Scene classification
- Face detection (with privacy options)
- Activity recognition
- Logo and text detection

### Audio Analysis
- Speech transcription
- Speaker diarization
- Audio event detection
- Music detection

### Text Analysis
- OCR extraction
- On-screen text detection
- Caption processing
- Metadata extraction

## Usage Examples

### Basic Video Search
```
1. videosearch_init(system_name="video_db")
2. videosearch_ingest_video("/videos/meeting.mp4")
3. videosearch_search("discussion about budget")
```

### Live Stream Monitoring
```
1. videosearch_init(system_name="monitor", max_streams=10)
2. videosearch_ingest_stream("rtsp://camera1", "camera_1", processing_mode="realtime")
3. videosearch_detect_activities("camera_1", ["motion", "person_entering"])
```

### Video Summarization
```
1. videosearch_ingest_video("/videos/webinar.mp4")
2. videosearch_transcribe("webinar")
3. videosearch_summarize("webinar", summary_type="highlights")
```

### Video Q&A
```
1. videosearch_index_video("training_video")
2. videosearch_qa("training_video", "What safety procedures are mentioned?")
```

## Integration with NVIDIA

- **NVIDIA VILA**: Vision-language model for video understanding
- **NVIDIA Riva**: Speech AI for transcription
- **NVIDIA Metropolis**: Vision AI for analytics
- **NVIDIA NIM**: Inference microservices

## References

- [Video Search Blueprint](https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization)
- [Vision AI Models](./references/vision_models.md)
- [Streaming Architecture](./references/streaming.md)
