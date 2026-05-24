# Industrial Blueprint Skill

## Overview
NVIDIA Industrial Blueprint integration for AI-powered manufacturing, quality inspection, predictive maintenance, and digital twin applications.

## Description
This skill provides tools for building industrial AI applications with computer vision, time-series analysis, and simulation capabilities. It includes:

- **Visual Inspection**: Automated quality control with computer vision
- **Predictive Maintenance**: Equipment health monitoring and failure prediction
- **Digital Twin**: Virtual factory simulation and optimization
- **Process Optimization**: Production line efficiency improvement
- **Safety Monitoring**: Workplace safety compliance

## Tools (16)

### industrial_init
Initialize an industrial AI system.

**Parameters:**
- `system_name` (required): Name for the industrial system
- `facility_type` (required): 'manufacturing', 'warehouse', 'refinery', 'power_plant'
- `enable_edge` (optional): Enable edge deployment (default: true)
- `sensors_config` (optional): Sensor configuration

### industrial_setup_camera
Configure a camera for inspection.

**Parameters:**
- `camera_id` (required): Unique camera identifier
- `location` (required): Physical location in facility
- `resolution` (optional): Camera resolution
- `fps` (optional): Frames per second
- `inspection_type` (optional): 'quality', 'safety', 'tracking'

### industrial_create_inspection
Create a visual inspection model.

**Parameters:**
- `inspection_name` (required): Name for the inspection
- `product_type` (required): Type of product to inspect
- `defect_types` (required): List of defect types to detect
- `sensitivity` (optional): Detection sensitivity (0.0-1.0)
- `min_confidence` (optional): Minimum confidence threshold

### industrial_run_inspection
Run inspection on image/video.

**Parameters:**
- `inspection_name` (required): Name of inspection to run
- `image_source` (required): Image path, camera ID, or video stream
- `return_annotations` (optional): Include visual annotations
- `return_metrics` (optional): Include quality metrics

### industrial_setup_sensor
Configure a sensor for monitoring.

**Parameters:**
- `sensor_id` (required): Unique sensor identifier
- `sensor_type` (required): 'vibration', 'temperature', 'pressure', 'flow', 'current'
- `equipment_id` (required): Equipment being monitored
- `sampling_rate` (optional): Data sampling rate
- `units` (optional): Measurement units

### industrial_predict_maintenance
Predict maintenance needs.

**Parameters:**
- `equipment_id` (required): Equipment to analyze
- `prediction_type` (optional): 'failure', 'remaining_life', 'anomaly'
- `timeframe` (optional): Prediction timeframe
- `include_recommendations` (optional): Include maintenance recommendations

### industrial_analyze_vibration
Analyze vibration data.

**Parameters:**
- `sensor_id` (required): Vibration sensor ID
- `time_range` (optional): Time range for analysis
- `analysis_type` (optional): 'fft', 'envelope', 'cepstrum'
- `detect_faults` (optional): Enable fault detection

### industrial_detect_anomaly
Detect anomalies in sensor data.

**Parameters:**
- `sensor_ids` (required): List of sensors to monitor
- `detection_model` (optional): 'statistical', 'ml', 'autoencoder'
- `sensitivity` (optional): Detection sensitivity
- `baseline_period` (optional): Period for baseline calculation

### industrial_create_twin
Create a digital twin.

**Parameters:**
- `twin_name` (required): Name for the digital twin
- `asset_id` (required): Physical asset to twin
- `twin_type` (required): 'equipment', 'line', 'facility'
- `include_physics` (optional): Include physics simulation
- `sync_frequency` (optional): Data sync frequency

### industrial_update_twin
Update digital twin state.

**Parameters:**
- `twin_name` (required): Digital twin name
- `sensor_data` (required): Current sensor readings
- `timestamp` (optional): Data timestamp
- `validate` (optional): Validate data before update

### industrial_simulate
Run simulation on digital twin.

**Parameters:**
- `twin_name` (required): Digital twin to simulate
- `scenario` (required): Simulation scenario
- `duration` (optional): Simulation duration
- `parameters` (optional): Simulation parameters

### industrial_optimize_process
Optimize production process.

**Parameters:**
- `process_id` (required): Process to optimize
- `objective` (required): 'throughput', 'quality', 'energy', 'cost'
- `constraints` (optional): Optimization constraints
- `variables` (optional): Adjustable parameters

### industrial_track_inventory
Track inventory and materials.

**Parameters:**
- `action` (required): 'count', 'locate', 'track'
- `item_type` (optional): Type of items
- `zone` (optional): Facility zone
- `camera_ids` (optional): Cameras for tracking

### industrial_monitor_safety
Monitor safety compliance.

**Parameters:**
- `zone` (required): Facility zone to monitor
- `safety_rules` (required): Safety rules to check
  - 'ppe', 'access_control', 'ergonomics', 'hazards'
- `alert_on_violation` (optional): Enable real-time alerts
- `generate_report` (optional): Generate compliance report

### industrial_track_workers
Track worker location and safety.

**Parameters:**
- `zone` (required): Zone to monitor
- `track_type` (optional): 'location', 'ppe_compliance', 'posture'
- `privacy_mode` (optional): Enable privacy protection
- `alert_conditions` (optional): Conditions for alerts

### industrial_generate_report
Generate operational report.

**Parameters:**
- `report_type` (required): 'quality', 'maintenance', 'efficiency', 'safety'
- `time_range` (optional): Report time range
- `equipment_filter` (optional): Specific equipment
- `format` (optional): 'pdf', 'html', 'json'

## Visual Inspection Defects

### Surface Defects
- `scratch` - Surface scratches
- `dent` - Physical indentations
- `stain` - Discoloration or contamination
- `crack` - Surface cracks
- `chip` - Material missing from edge

### Dimensional Defects
- `oversized` - Dimension too large
- `undersized` - Dimension too small
- `misaligned` - Component misalignment
- `warped` - Shape distortion

### Assembly Defects
- `missing_component` - Part not present
- `wrong_component` - Incorrect part installed
- `loose_connection` - Improperly secured
- `foreign_object` - Debris or contamination

### Electrical Defects
- `solder_bridge` - Solder connecting wrong points
- `cold_solder` - Poor solder joint
- `component_damage` - Damaged electronic component

## Predictive Maintenance Models

### Failure Mode Detection
```python
result = industrial_predict_maintenance(
    equipment_id="pump_001",
    prediction_type="failure",
    timeframe="7_days"
)
# Returns: {"probability": 0.23, "likely_failure_mode": "bearing_wear"}
```

### Remaining Useful Life (RUL)
```python
rul = industrial_predict_maintenance(
    equipment_id="motor_003",
    prediction_type="remaining_life"
)
# Returns: {"rul_days": 145, "confidence": 0.85}
```

### Vibration Analysis
```python
analysis = industrial_analyze_vibration(
    sensor_id="vib_sensor_001",
    analysis_type="fft"
)
# Returns frequency spectrum and detected anomalies
```

## Digital Twin Capabilities

### Equipment Twin
```
Physical Equipment ←→ Digital Model
      ↓                    ↓
   Sensors            Simulation
      ↓                    ↓
   Real-time         Predictive
    Data              Analytics
```

### Process Twin
```
Production Line Digital Twin
├── Machine 1 Twin
├── Machine 2 Twin
├── Conveyor Twin
└── Quality Station Twin
```

### Facility Twin
```
Factory Digital Twin
├── Production Area
├── Warehouse
├── Utilities
└── Safety Systems
```

## Safety Monitoring Rules

### PPE Compliance
- Hard hat detection
- Safety vest detection
- Safety glasses detection
- Steel-toed boots detection

### Access Control
- Restricted area monitoring
- Authorization verification
- Time-based access rules

### Hazard Detection
- Spill detection
- Fire/smoke detection
- Gas leak detection
- Obstacle detection

## Usage Examples

### Quality Inspection Line
```
1. industrial_init(system_name="quality_line", facility_type="manufacturing")
2. industrial_setup_camera(camera_id="cam_001", location="station_1")
3. industrial_create_inspection(
     inspection_name="pcba_inspection",
     product_type="PCBA",
     defect_types=["solder_bridge", "missing_component", "cold_solder"]
   )
4. industrial_run_inspection(
     inspection_name="pcba_inspection",
     image_source="cam_001"
   )
```

### Predictive Maintenance Setup
```
1. industrial_setup_sensor(
     sensor_id="vib_001",
     sensor_type="vibration",
     equipment_id="motor_001"
   )
2. industrial_detect_anomaly(
     sensor_ids=["vib_001"],
     detection_model="autoencoder"
   )
3. industrial_predict_maintenance(
     equipment_id="motor_001",
     prediction_type="failure"
   )
```

### Digital Twin Simulation
```
1. industrial_create_twin(
     twin_name="assembly_line_1",
     asset_id="line_001",
     twin_type="line",
     include_physics=True
   )
2. industrial_simulate(
     twin_name="assembly_line_1",
     scenario="bottleneck_analysis",
     duration="1_hour"
   )
```

## Integration with NVIDIA Industrial

This skill integrates with NVIDIA industrial solutions:

- **NVIDIA Isaac**: Robotics and automation
- **Metropolis**: Computer vision for manufacturing
- **Omniverse**: Digital twin and simulation
- **Jetson**: Edge AI deployment

## Edge Deployment

### Jetson Configuration
```python
industrial_init(
    system_name="edge_inspection",
    enable_edge=True,
    edge_device="jetson_agx_orin"
)
```

### Edge AI Models
- Optimized TensorRT models
- Low-latency inference
- Offline operation capability

## References

- [NVIDIA Isaac Documentation](https://developer.nvidia.com/isaac)
- [Metropolis Vision AI](./references/metropolis.md)
- [Omniverse Digital Twin](./references/omniverse.md)
- [Predictive Maintenance Models](./references/maintenance.md)
