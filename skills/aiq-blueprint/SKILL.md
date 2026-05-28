# AI-Q Blueprint Skill (Research Agent)

## Overview
NVIDIA AI-Q Blueprint integration for building intelligent research agents that connect to enterprise data, reason using chain-of-thought, and generate comprehensive research reports.

## Description
This skill provides tools for creating enterprise-grade research agents built on NVIDIA NeMo Agent Toolkit and LangChain Deep Agents. It supports:

- **Deep Research**: Multi-step research with source verification
- **Document Analysis**: Process and extract insights from documents
- **Citation Management**: Track and cite sources automatically
- **Report Generation**: Create structured research reports
- **Knowledge Synthesis**: Combine information from multiple sources

## Tools (14)

### aiq_init
Initialize AI-Q research agent system.

**Parameters:**
- `agent_name` (required): Name for the research agent
- `research_domain` (optional): Domain focus (e.g., 'biomedical', 'financial', 'legal')
- `llm_config` (optional): LLM configuration
- `knowledge_bases` (optional): List of knowledge bases to connect

### aiq_create_research_task
Create a new research task.

**Parameters:**
- `query` (required): Research question or topic
- `depth` (optional): 'quick', 'standard', or 'deep'
- `sources` (optional): Preferred sources ('academic', 'web', 'internal', 'all')
- `time_limit` (optional): Maximum time for research
- `output_format` (optional): 'report', 'summary', 'brief'

### aiq_search_sources
Search across connected knowledge sources.

**Parameters:**
- `query` (required): Search query
- `sources` (optional): Specific sources to search
- `filters` (optional): Search filters (date, type, etc.)
- `max_results` (optional): Maximum results per source

### aiq_analyze_document
Analyze a document for insights.

**Parameters:**
- `document_path` (required): Path to document
- `analysis_type` (optional): 'summary', 'extraction', 'qa', 'full'
- `extract_entities` (optional): Extract named entities
- `extract_relations` (optional): Extract relationships

### aiq_extract_knowledge
Extract structured knowledge from text.

**Parameters:**
- `text` (required): Text to process
- `extraction_schema` (optional): Schema for extraction
- `confidence_threshold` (optional): Minimum confidence

### aiq_verify_facts
Verify facts against sources.

**Parameters:**
- `claims` (required): List of claims to verify
- `sources` (optional): Sources to check against
- `strictness` (optional): 'lenient', 'moderate', 'strict'

### aiq_generate_citations
Generate citations for sources.

**Parameters:**
- `sources` (required): List of sources used
- `style` (optional): 'apa', 'mla', 'chicago', 'ieee', 'nature'
- `include_doi` (optional): Include DOI links

### aiq_synthesize_findings
Synthesize findings from multiple sources.

**Parameters:**
- `findings` (required): List of findings from research
- `synthesis_type` (optional): 'narrative', 'structured', 'comparative'
- `highlight_conflicts` (optional): Highlight conflicting information

### aiq_generate_report
Generate research report.

**Parameters:**
- `task_id` (required): Research task ID
- `template` (optional): Report template
- `include_appendix` (optional): Include appendix with raw data
- `include_methodology` (optional): Include methodology section

### aiq_add_knowledge_base
Add a knowledge base connection.

**Parameters:**
- `kb_name` (required): Name for the knowledge base
- `kb_type` (required): 'vector', 'graph', 'relational', 'api'
- `connection_config` (required): Connection parameters
- `index_config` (optional): Indexing configuration

### aiq_create_workflow
Create a research workflow.

**Parameters:**
- `workflow_name` (required): Name for the workflow
- `steps` (required): List of research steps
- `parallel_execution` (optional): Enable parallel steps

### aiq_execute_workflow
Execute a research workflow.

**Parameters:**
- `workflow_name` (required): Workflow to execute
- `input_data` (required): Input for the workflow
- `save_results` (optional): Save results to knowledge base

### aiq_get_research_status
Get status of research task.

**Parameters:**
- `task_id` (required): Task identifier
- `include_details` (optional): Include detailed progress

### aiq_export_results
Export research results.

**Parameters:**
- `task_id` (required): Task to export
- `format` (required): 'pdf', 'docx', 'json', 'markdown'
- `include_sources` (optional): Include source documents

## Research Workflows

### Standard Research Flow
```
1. aiq_create_research_task(query, depth="standard")
2. aiq_search_sources(query)
3. aiq_analyze_document(selected_sources)
4. aiq_extract_knowledge(text)
5. aiq_verify_facts(claims)
6. aiq_synthesize_findings(findings)
7. aiq_generate_citations(sources)
8. aiq_generate_report(task_id)
```

### Deep Research Flow
```
1. aiq_create_research_task(query, depth="deep")
2. aiq_create_workflow(workflow_name, steps)
3. aiq_execute_workflow(workflow_name)
4. aiq_get_research_status(task_id)
5. aiq_export_results(task_id)
```

## Domain Configurations

### Biomedical Research
```python
aiq_init(
    agent_name="biomedical-researcher",
    research_domain="biomedical",
    knowledge_bases=["pubmed", "clinical_trials", "drug_db"]
)
```

### Financial Research
```python
aiq_init(
    agent_name="financial-analyst",
    research_domain="financial",
    knowledge_bases=["sec_filings", "market_data", "news"]
)
```

### Legal Research
```python
aiq_init(
    agent_name="legal-researcher",
    research_domain="legal",
    knowledge_bases=["case_law", "statutes", "regulations"]
)
```

## Integration with NVIDIA NeMo

This skill integrates with:
- **NeMo Agent Toolkit**: Agent orchestration
- **NVIDIA NIM**: Model inference
- **NeMo Retriever**: Document retrieval
- **NeMo Curator**: Data curation

## Usage Examples

### Quick Research
```
1. aiq_init(agent_name="researcher")
2. task = aiq_create_research_task("What are the latest advances in LLM reasoning?")
3. aiq_generate_report(task["task_id"])
```

### Biomedical Deep Research
```
1. aiq_init(agent_name="bio-researcher", research_domain="biomedical")
2. aiq_add_knowledge_base("pubmed", kb_type="api", connection_config={...})
3. aiq_create_research_task("CRISPR gene therapy clinical trials 2024", depth="deep")
```

## References

- [NVIDIA AI-Q Blueprint](https://github.com/NVIDIA-AI-Blueprints/aiq)
- [NeMo Agent Toolkit](./references/nemo.md)
- [Research Workflows](./references/workflows.md)
