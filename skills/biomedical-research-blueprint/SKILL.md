# Biomedical AI-Q Research Agent Blueprint Skill

Deep research agent with virtual screening capabilities for biomedical research and drug discovery.

## Description

This skill provides tools for creating detailed research reports with virtual screening capabilities for discovering novel small-molecule therapies. Integrates AI-Q Research Assistant with MolMIM for molecular generation and DiffDock for protein-ligand docking.

## When to Use

- Biomedical literature research
- Drug discovery and development
- Virtual screening for novel therapeutics
- Protein-ligand interaction prediction
- Research report generation
- Molecular property optimization

## Blueprint Source

Based on: [NVIDIA biomedical-aiq-research-agent](https://github.com/NVIDIA-AI-Blueprints/biomedical-aiq-research-agent)

## Tools

### Research Tools

| Tool | Description |
|------|-------------|
| `create_research_plan` | Create structured research plan |
| `search_literature` | Search biomedical literature |
| `search_internal_docs` | Search internal/on-premise documents |
| `web_search` | Web search with Tavily integration |
| `generate_report` | Generate comprehensive research report |
| `reflect_on_report` | Identify gaps for further research |

### Virtual Screening Tools

| Tool | Description |
|------|-------------|
| `generate_molecules` | Generate novel molecules using MolMIM |
| `optimize_molecule` | Optimize molecule properties |
| `predict_docking` | Predict protein-ligand docking with DiffDock |
| `score_binding_affinity` | Score binding affinity predictions |
| `get_protein_structure` | Get protein structure from PDB |

### Molecular Analysis Tools

| Tool | Description |
|------|-------------|
| `get_smiles_from_name` | Get SMILES string from molecule name |
| `search_rcsb_pdb` | Search RCSB Protein Data Bank |
| `calculate_molecular_properties` | Calculate molecular descriptors |
| `predict_admet` | Predict ADMET properties |

### Document Tools

| Tool | Description |
|------|-------------|
| `upload_research_document` | Upload document to RAG collection |
| `query_research_knowledge` | Query research knowledge base |
| `create_collection` | Create new document collection |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Demo Web Application                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Research Interface  │ Virtual Screening Dashboard         │  │
│  │ - Topic Input       │ - Molecule Generation               │  │
│  │ - Report Viewer     │ - Docking Visualization             │  │
│  │ - Q&A Interface     │ - Property Optimization             │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    AI-Q Research Agent (AIRA)                     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Research Pipeline                                          │   │
│  │ 1. Plan → 2. Search → 3. Write → 4. Reflect → 5. Finish  │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Parallel Search Agent                                      │   │
│  │ - RAG Query → LLM Judge → Fallback Web Search             │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Virtual Screening Services                     │
│  ┌───────────────────────┐  ┌───────────────────────────────┐     │
│  │ MolMIM                │  │ DiffDock                      │     │
│  │ - Molecular Generation│  │ - Protein-Ligand Docking      │     │
│  │ - Property Guided     │  │ - Binding Affinity Prediction │     │
│  └───────────────────────┘  └───────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NVIDIA NIM Services                            │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Llama-3.3-Nemotron-Super-49B-v1 (Reasoning LLM)          │   │
│  │ Llama-3.3-70B-Instruct (Report Writing)                  │   │
│  │ NeMo Retriever (Document Processing)                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# NVIDIA API Keys
NVIDIA_API_KEY=nvapi-xxx
NGC_API_KEY=nvapi-xxx

# Tavily for Web Search
TAVILY_API_KEY=tvly-xxx

# Database
MILVUS_HOST=localhost
NEO4J_URI=bolt://localhost:7687

# Virtual Screening
MOLMIM_ENDPOINT=https://build.nvidia.com/nvidia/molmim-generate
DIFFDOCK_ENDPOINT=https://build.nvidia.com/mit/diffdock
```

### Integration with DeerFlow

```python
from deerflow.blueprints import BiomedicalResearchBlueprint

research = BiomedicalResearchBlueprint(
    enable_virtual_screening=True,
    enable_web_search=True
)

# Create research plan
plan = await research.create_research_plan(
    topic="Novel therapies for Alzheimer's disease targeting tau protein",
    structure=["Introduction", "Literature Review", "Virtual Screening", "Conclusions"]
)

# Generate report with human-in-the-loop
report = await research.generate_report(
    plan=plan,
    enable_feedback=True
)

# Virtual screening for novel molecules
molecules = await research.generate_molecules(
    seed_smiles="CC(=O)Oc1ccccc1C(=O)O",  # Aspirin-like
    target_properties={"logp": 2.0, "mw": 300},
    num_molecules=100
)

# Predict protein-ligand docking
docking = await research.predict_docking(
    protein_pdb="6HRE",  # Tau protein
    molecule_smiles=molecules[0].smiles
)
```

## GPU Requirements

### For Hosted NIMs (Recommended)
- 1x L40S for local RAG ingestion

### For Full Local Deployment

| Component | GPU Requirement |
|-----------|-----------------|
| NeMo Retriever (Ingestion) | 1x H100 80GB or 1x A100 80GB |
| Nemotron Super 49B | 1x H100 80GB or 2x A100 80GB |
| Llama 3.3 70B | 2x H100 80GB or 4x A100 80GB |
| MolMIM | 1x Ampere/L40 (3GB+ VRAM) |
| DiffDock | 1x H100/A100/A6000/A10/L40S |

**Total:** 5x H100 80GB or 8x A100 80GB

## Example Usage

```python
from deerflow.tools.biomedical import (
    ResearchAgent,
    VirtualScreening,
    LiteratureSearch
)

# Initialize research agent
agent = ResearchAgent(
    llm="llama-3.3-nemotron-super-49b-v1",
    enable_web_search=True
)

# Create research plan
plan = await agent.plan(
    topic="Investigation of BACE1 inhibitors for Alzheimer's treatment"
)

# Search literature
literature = await agent.search_literature(
    query="BACE1 inhibitor clinical trials",
    sources=["pubmed", "internal_docs"]
)

# Generate report
report = await agent.generate_report(plan)

# Virtual screening
screening = VirtualScreening()
molecules = await screening.generate(
    target="BACE1",
    seed_molecule="known_inhibitor_smiles",
    num_candidates=50
)

# Dock molecules
for mol in molecules[:10]:
    result = await screening.dock(
        protein="BACE1.pdb",
        molecule=mol.smiles
    )
    print(f"Binding score: {result.score}")
```

## Workflow

1. **Research Phase**
   - Create structured research plan
   - Parallel search across multiple sources
   - LLM-as-judge for result relevance
   - Fallback to web search if needed

2. **Report Generation**
   - Write sections based on research
   - Human feedback on drafts
   - Reflect on gaps and iterate

3. **Virtual Screening** (when applicable)
   - Generate novel molecules with MolMIM
   - Predict docking with DiffDock
   - Score and rank candidates

## References

- [AI-Q NVIDIA Research Assistant](https://build.nvidia.com/nvidia/aiq)
- [Virtual Screening Blueprint](https://build.nvidia.com/nvidia/generative-virtual-screening-for-drug-discovery)
- [MolMIM Model](https://build.nvidia.com/nvidia/molmim-generate)
- [DiffDock Model](https://build.nvidia.com/mit/diffdock)
- [RCSB PDB API](https://rcsbapi.readthedocs.io/)
