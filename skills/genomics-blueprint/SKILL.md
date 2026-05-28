# Genomics Analysis Blueprint Skill

GPU-accelerated genomics workflows using NVIDIA Parabricks and CodonFM for alignment, variant calling, and variant effect prediction.

## Description

This skill provides tools for running essential genomics workflows including linear and graph-based read alignment, variant calling via DeepVariant, and variant effect prediction using CodonFM (NVIDIA's RNA foundation model).

## When to Use

- Germline variant calling on WES/WGS data
- Pangenome analysis workflows
- Variant effect prediction
- RNA sequence analysis
- Drug discovery genomics
- Clinical genomics pipelines

## Blueprint Source

Based on: [NVIDIA genomics-analysis](https://github.com/NVIDIA-AI-Blueprints/genomics-analysis)

## Tools

### Alignment Tools

| Tool | Description |
|------|-------------|
| `run_bwa_mem` | GPU-accelerated BWA-MEM alignment via Parabricks |
| `run_giraffe_align` | Pangenome graph alignment using Giraffe |
| `get_alignment_stats` | Get alignment statistics |

### Variant Calling Tools

| Tool | Description |
|------|-------------|
| `run_deepvariant` | GPU-accelerated DeepVariant for variant calling |
| `run_pangenome_deepvariant` | Pangenome-aware DeepVariant |
| `annotate_variants` | Annotate VCF with functional information |
| `filter_variants` | Filter variants by quality metrics |

### Variant Effect Prediction Tools

| Tool | Description |
|------|-------------|
| `predict_variant_effect` | Predict variant functional impact using CodonFM |
| `extract_transcripts` | Extract protein-coding sequences from GENCODE |
| `map_variants_to_transcripts` | Map variants to gene transcripts |
| `calculate_log_likelihood` | Calculate log likelihood ratios for variants |

### Workflow Tools

| Tool | Description |
|------|-------------|
| `run_germline_wes_pipeline` | Complete germline WES workflow |
| `run_pangenome_pipeline` | Pangenome analysis workflow |
| `run_variant_effect_pipeline` | Full variant effect prediction pipeline |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jupyter Notebook Interface                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────┐  │
│  │ germline_wes    │ │ pangenome       │ │ variant_effect    │  │
│  │ .ipynb          │ │ .ipynb          │ │ _prediction.ipynb │  │
│  └─────────────────┘ └─────────────────┘ └───────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NVIDIA Parabricks                               │
│  ┌───────────────────────┐  ┌───────────────────────────────────┐ │
│  │ BWA-MEM (fq2bam)      │  │ DeepVariant                       │ │
│  │ GPU-Accelerated       │  │ GPU-Accelerated                   │ │
│  │ Alignment             │  │ Variant Calling                   │ │
│  └───────────────────────┘  └───────────────────────────────────┘ │
│  ┌───────────────────────┐  ┌───────────────────────────────────┐ │
│  │ Giraffe               │  │ Pangenome-Aware                   │ │
│  │ Graph Alignment       │  │ DeepVariant                       │ │
│  └───────────────────────┘  └───────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    CodonFM (RNA Foundation Model)                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Variant Effect Prediction                                    │  │
│  │ - Log Likelihood Ratio Calculation                          │  │
│  │ - Functional Impact Scoring                                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Reference Data                                  │
│  ┌───────────────────┐  ┌───────────────────────────────────┐     │
│  │ GRCh38 Reference  │  │ HPRC v1.1 Pangenome               │     │
│  │ Genome            │  │ Graph                             │     │
│  └───────────────────┘  └───────────────────────────────────┘     │
│  ┌───────────────────┐  ┌───────────────────────────────────┐     │
│  │ GENCODE Gene      │  │ NA12878 Sample                    │     │
│  │ Annotations       │  │ (Genome in a Bottle)              │     │
│  └───────────────────┘  └───────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Parabricks License
NVIDIA_CLARA_LICENSE=xxx

# Reference Data
REFERENCE_GENOME=/data/reference/GRCh38.fa
PANGENOME_GRAPH=/data/pangenome/hprc-v1.1-mc-grch38.gfa

# Output Directories
OUTPUT_DIR=/data/output
TEMP_DIR=/tmp/parabricks
```

### Integration with DeerFlow

```python
from deerflow.blueprints import GenomicsBlueprint

genomics = GenomicsBlueprint(
    parabricks_license="xxx",
    reference_genome="/data/GRCh38.fa"
)

# Run germline WES pipeline
result = await genomics.run_germline_wes_pipeline(
    fastq1="/data/sample_R1.fastq.gz",
    fastq2="/data/sample_R2.fastq.gz",
    output_vcf="/data/output/variants.vcf"
)

# Predict variant effects
effects = await genomics.predict_variant_effect(
    vcf_file="/data/output/variants.vcf",
    gene_annotations="/data/gencode.gtf"
)
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| Parabricks BWA-MEM | 1x T4 (16GB) | 1x A100 (40GB) |
| DeepVariant | 1x A100 (40GB) | 1x H100 (80GB) |
| CodonFM | 1x L40S (48GB) | 1x A100 (80GB) |

**Supported GPUs:** T4, A10, A30, A40, A100, A6000, L4, L40, H100, H200, GH200, B200, B300, GB200, GB300

## Performance

- **Alignment**: 10-50x faster than CPU BWA-MEM
- **Variant Calling**: 20-100x faster than CPU DeepVariant
- **Graph Alignment**: Enables pangenome analysis not possible on CPU

## Example Usage

```python
from deerflow.tools.genomics import ParabricksRunner, CodonFMPredictor

# Initialize runners
aligner = ParabricksRunner(gpu_id=0)
predictor = CodonFMPredictor()

# Run alignment
alignment = await aligner.run_bwa_mem(
    fastq1="sample_R1.fastq.gz",
    fastq2="sample_R2.fastq.gz",
    reference="GRCh38.fa",
    output="aligned.bam"
)

# Call variants
variants = await aligner.run_deepvariant(
    bam_file="aligned.bam",
    reference="GRCh38.fa",
    output="variants.vcf"
)

# Predict effects
effects = await predictor.predict_effects(
    vcf_file="variants.vcf",
    transcripts="gencode.v44.annotation.gtf"
)

# Results include log-likelihood ratios
for variant in effects:
    print(f"{variant.id}: LLR={variant.log_likelihood_ratio}")
```

## References

- [NVIDIA Parabricks Documentation](https://docs.nvidia.com/clara/parabricks/latest/)
- [CodonFM Blog](https://developer.nvidia.com/blog/introducing-the-codonfm-open-model-for-rna-design-and-analysis/)
- [Pangenome Alignment Blog](https://developer.nvidia.com/blog/discover-new-biological-insights-with-accelerated-pangenome-alignment-in-nvidia-parabricks/)
- [DeepVariant](https://github.com/google/deepvariant)
