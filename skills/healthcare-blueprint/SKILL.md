# Healthcare Blueprint Skill

## Overview
NVIDIA Healthcare Blueprint integration for AI-powered medical applications including clinical documentation, medical imaging analysis, drug discovery, and patient engagement.

## Description
This skill provides tools for building healthcare AI applications with HIPAA-compliant data handling, clinical decision support, and medical NLP capabilities. It includes:

- **Clinical NLP**: Extract and analyze medical information from text
- **Medical Imaging**: AI analysis of radiology images
- **Drug Discovery**: Molecular analysis and drug interaction
- **Patient Monitoring**: Vital signs analysis and alerts
- **Clinical Trials**: Patient matching and trial management

## Tools (16)

### healthcare_init
Initialize a healthcare AI system.

**Parameters:**
- `system_name` (required): Name for the healthcare system
- `compliance_mode` (required): 'hipaa', 'gdpr', or 'standard'
- `specialty` (optional): Medical specialty focus
- `enable_audit` (optional): Enable compliance audit logging (default: true)

### healthcare_extract_clinical
Extract clinical entities from text.

**Parameters:**
- `text` (required): Clinical text to process
- `extract_types` (optional): Entity types to extract
  - 'conditions', 'medications', 'procedures', 'lab_values', 'anatomical'
- `include_negations` (optional): Include negation detection
- `include_certainty` (optional): Include certainty/uncertainty markers

### healthcare_analyze_imaging
Analyze medical imaging.

**Parameters:**
- `image_path` (required): Path to medical image (DICOM, PNG, JPEG)
- `modality` (required): 'xray', 'ct', 'mri', 'ultrasound', 'pathology'
- `analysis_type` (optional): 'screening', 'diagnosis', 'measurement'
- `body_region` (optional): Anatomical region
- `return_findings` (optional): Include detailed findings

### healthcare_check_interactions
Check drug-drug interactions.

**Parameters:**
- `medications` (required): List of medications
- `patient_factors` (optional): Patient-specific factors (age, conditions, etc.)
- `severity_filter` (optional): Minimum severity to report

### healthcare_analyze_labs
Analyze laboratory results.

**Parameters:**
- `lab_results` (required): List of lab results with values and units
- `patient_context` (optional): Patient demographics and conditions
- `reference_range` (optional): Custom reference ranges
- `flag_abnormal` (optional): Flag abnormal values

### healthcare_summarize_record
Generate clinical summary.

**Parameters:**
- `patient_id` (required): Patient identifier
- `record_types` (optional): Types of records to include
- `summary_type` (optional): 'discharge', 'progress', 'referral', 'handoff'
- `include_recommendations` (optional): Include AI recommendations

### healthcare_match_trials
Match patient to clinical trials.

**Parameters:**
- `patient_profile` (required): Patient medical profile
- `conditions` (required): List of conditions
- `location` (optional): Geographic preference
- `status` (optional): Trial status filter ('recruiting', 'active', etc.)

### healthcare_predict_risk
Predict clinical risk scores.

**Parameters:**
- `patient_data` (required): Patient clinical data
- `risk_type` (required): Type of risk assessment
  - 'readmission', 'mortality', 'deterioration', 'sepsis', 'custom'
- `timeframe` (optional): Prediction timeframe
- `include_explanation` (optional): Include feature importance

### healthcare_generate_note
Generate clinical documentation.

**Parameters:**
- `encounter_type` (required): 'office', 'emergency', 'procedure', 'telehealth'
- `patient_data` (required): Patient information
- `transcript` (optional): Visit transcript
- `note_format` (optional): 'soap', 'progress', 'h&p', 'procedure'

### healthcare_analyze_vitals
Analyze vital signs trends.

**Parameters:**
- `vital_data` (required): Time-series vital sign data
- `vital_types` (optional): Types to analyze
  - 'hr', 'bp', 'temp', 'resp', 'spo2', 'all'
- `alert_thresholds` (optional): Custom alert thresholds
- `detect_anomalies` (optional): Enable anomaly detection

### healthcare_code_diagnosis
Assign diagnostic codes.

**Parameters:**
- `clinical_text` (required): Clinical description
- `coding_system` (required): 'icd10', 'icd11', 'snomed'
- `include_confidence` (optional): Include confidence scores
- `suggestions_limit` (optional): Maximum code suggestions

### healthcare_code_procedure
Assign procedure codes.

**Parameters:**
- `procedure_description` (required): Procedure details
- `coding_system` (required): 'cpt', 'hcpcs', 'icd10-pcs'
- `modifiers` (optional): Procedure modifiers

### healthcare_check_guidelines
Check against clinical guidelines.

**Parameters:**
- `condition` (required): Primary condition
- `patient_data` (required): Patient information
- `guideline_source` (optional): 'nccn', 'aha', 'uspstf', 'who'
- `include_references` (optional): Include guideline references

### healthcare_translate_medical
Translate medical terms between languages.

**Parameters:**
- `text` (required): Medical text to translate
- `source_lang` (required): Source language
- `target_lang` (required): Target language
- `preserve_formatting` (optional): Preserve clinical formatting

### healthcare_anonymize
Anonymize patient data.

**Parameters:**
- `data` (required): Patient data to anonymize
- `method` (optional): 'deidentify', 'pseudonymize', 'aggregate'
- `hipaa_safe_harbor` (optional): Use HIPAA Safe Harbor method

### healthcare_audit_log
Create compliance audit log.

**Parameters:**
- `action` (required): Action performed
- `resource_type` (required): Type of resource accessed
- `user_id` (required): User performing action
- `patient_id` (optional): Patient involved
- `details` (optional): Additional details

## Clinical Entity Types

### Conditions
- Diagnosis names and codes
- Signs and symptoms
- Disease stages and grades
- Comorbidities

### Medications
- Drug names (brand and generic)
- Dosages and frequencies
- Routes of administration
- Duration of therapy

### Procedures
- Surgical procedures
- Diagnostic procedures
- Therapeutic interventions
- Lab orders

### Lab Values
- Test names and LOINC codes
- Numerical values and units
- Reference ranges
- Abnormal flags

### Anatomical References
- Body regions
- Organs and structures
- Laterality (left/right)
- Spatial relationships

## Medical Imaging Analysis

### Chest X-Ray Analysis
```
1. healthcare_analyze_imaging(
     image_path="/data/chest_xray.dcm",
     modality="xray",
     body_region="chest",
     analysis_type="screening"
   )
```

Returns:
- Findings (e.g., "No acute cardiopulmonary abnormality")
- Confidence score
- Recommended follow-up

### CT Scan Analysis
```
1. healthcare_analyze_imaging(
     image_path="/data/ct_abdomen.dcm",
     modality="ct",
     body_region="abdomen",
     analysis_type="diagnosis"
   )
```

### Pathology Slide Analysis
```
1. healthcare_analyze_imaging(
     image_path="/data/pathology_slide.svs",
     modality="pathology",
     analysis_type="diagnosis"
   )
```

## Clinical Decision Support

### Risk Stratification
```python
result = healthcare_predict_risk(
    patient_data={
        "age": 72,
        "conditions": ["CHF", "Diabetes", "CKD"],
        "recent_hospitalization": True,
        "lab_values": {"creatinine": 2.1, "BNP": 850}
    },
    risk_type="readmission",
    timeframe="30_days"
)
# Returns: {"risk_score": 0.78, "risk_level": "high", "factors": [...]}
```

### Drug Interaction Checking
```python
interactions = healthcare_check_interactions(
    medications=["Warfarin", "Amiodarone", "Metformin"],
    patient_factors={"age": 68, "renal_function": "moderate_impairment"}
)
# Returns list of interactions with severity and recommendations
```

## Clinical Documentation

### SOAP Note Generation
```
1. healthcare_generate_note(
     encounter_type="office",
     patient_data={...},
     transcript="Doctor: How are you feeling today? Patient: ...",
     note_format="soap"
   )
```

Output:
```
SUBJECTIVE:
Patient reports improved energy levels...

OBJECTIVE:
Vitals: BP 128/78, HR 72, Temp 98.6F
Physical exam: ...

ASSESSMENT:
1. Type 2 Diabetes - well controlled
2. Hypertension - well controlled

PLAN:
1. Continue current medications
2. Recheck HbA1c in 3 months
```

## Compliance and Security

### HIPAA Compliance
- All PHI is encrypted at rest and in transit
- Audit logging for all data access
- Minimum necessary data principle
- Automatic de-identification options

### Data Anonymization
```python
anonymized = healthcare_anonymize(
    data=patient_record,
    method="deidentify",
    hipaa_safe_harbor=True
)
```

## Integration with NVIDIA Healthcare

This skill integrates with NVIDIA Clara:

- **Clara NIM**: Medical imaging AI models
- **BioNeMo**: Drug discovery and biology models
- **Monai**: Medical imaging framework
- **Riva Healthcare**: Medical speech AI

## Supported Specialties

| Specialty | Key Features |
|-----------|--------------|
| Cardiology | ECG analysis, echo interpretation |
| Radiology | Multi-modality imaging analysis |
| Oncology | Tumor detection, treatment planning |
| Pathology | Slide analysis, biomarker detection |
| Emergency | Triage, sepsis detection |
| Primary Care | Documentation, preventive care |

## References

- [NVIDIA Clara Documentation](https://developer.nvidia.com/clara)
- [BioNeMo Models](./references/bionemo.md)
- [Clinical NLP Guide](./references/clinical_nlp.md)
- [HIPAA Compliance](./references/compliance.md)
