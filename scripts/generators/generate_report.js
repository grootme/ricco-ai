const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
        AlignmentType, HeadingLevel, PageNumber, BorderStyle, WidthType, ShadingType,
        PageBreak, TableOfContents } = require("docx");
const fs = require("fs");

// Palette - Tech/AI theme
const P = {
  primary: "#0A1628",
  body: "#1A2B40",
  secondary: "#6878A0",
  accent: "#5B8DB8",
  surface: "#F4F8FC"
};
const c = (hex) => hex.replace("#", "");

// Builders
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, color: c(P.primary), font: { ascii: "Calibri", eastAsia: "SimHei" } })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
    children: [new TextRun({ text, bold: true, size: 28, color: c(P.primary), font: { ascii: "Calibri", eastAsia: "SimHei" } })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, size: 24, color: c(P.primary), font: { ascii: "Calibri", eastAsia: "SimHei" } })]
  });
}

function body(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 312 },
    children: [new TextRun({ text, size: 22, color: c(P.body), font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" } })]
  });
}

function bullet(text) {
  return new Paragraph({
    spacing: { line: 312 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "\u2022 ", size: 22, color: c(P.accent) }),
      new TextRun({ text, size: 22, color: c(P.body), font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" } })
    ]
  });
}

// Table builder
function createTable(headers, rows) {
  const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const border = { style: BorderStyle.SINGLE, size: 1, color: c(P.accent) };
  
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: border, bottom: border, left: NB, right: NB, insideHorizontal: border, insideVertical: NB },
    rows: [
      new TableRow({
        children: headers.map(h => new TableCell({
          shading: { type: ShadingType.CLEAR, fill: c(P.accent) },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 20, color: "FFFFFF" })] })]
        }))
      }),
      ...rows.map((row, i) => new TableRow({
        children: row.map(cell => new TableCell({
          shading: { type: ShadingType.CLEAR, fill: i % 2 === 0 ? c(P.surface) : "FFFFFF" },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20, color: c(P.body) })] })]
        }))
      }))
    ]
  });
}

// Document
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" }, size: 22, color: c(P.body) },
        paragraph: { spacing: { line: 312 } }
      }
    }
  },
  sections: [
    // Cover
    {
      properties: { page: { margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: [
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          rows: [new TableRow({
            height: { value: 16838, rule: "exact" },
            children: [new TableCell({
              shading: { type: ShadingType.CLEAR, fill: c(P.primary) },
              children: [
                new Paragraph({ spacing: { before: 3000 } }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { after: 400 },
                  children: [new TextRun({ text: "NVIDIA AI BLUEPRINTS", bold: true, size: 56, color: "FFFFFF" })]
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { after: 200 },
                  children: [new TextRun({ text: "PLATAFORMA DE INFRAESTRUCTURA DIGITAL AUT\u00d3NOMA", size: 36, color: c(P.accent) })]
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { after: 600 },
                  children: [new TextRun({ text: "An\u00e1lisis Arquitect\u00f3nico y Gu\u00eda de Implementaci\u00f3n Empresarial", size: 28, color: "B0B8C0" })]
                }),
                new Paragraph({ spacing: { before: 2000 } }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [new TextRun({ text: "Informe T\u00e9cnico Integral", size: 24, color: "90989F" })]
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [new TextRun({ text: "Versi\u00f3n 1.0 | Abril 2026", size: 20, color: "687078" })]
                })
              ]
            })]
          })]
        })
      ]
    },
    // TOC
    {
      properties: { page: { margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 } } },
      children: [
        new Paragraph({ children: [new TextRun({ text: "Contenido", bold: true, size: 32 })] }),
        new TableOfContents({ styles: ["Heading 1", "Heading 2", "Heading 3"] }),
        new Paragraph({ children: [new PageBreak()] })
      ]
    },
    // Body
    {
      properties: { page: { margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 }, pageNumbers: { start: 1 } } },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: c(P.secondary) })]
          })]
        })
      },
      children: [
        // Section 1
        h1("1. Resumen Ejecutivo"),
        body("Este informe presenta un an\u00e1lisis exhaustivo de los 28 repositorios NVIDIA clonados del ecosistema de AI Blueprints, NeMo Framework, OpenShell, TensorRT y Cosmos. El objetivo es proporcionar una gu\u00eda completa para la construcci\u00f3n de una plataforma de infraestructura digital aut\u00f3noma de grado empresarial, escalable y alineada con las tendencias tecnol\u00f3gicas m\u00e1s avanzadas en inteligencia artificial generativa, agentes aut\u00f3nomos y computaci\u00f3n acelerada por GPU."),
        body("La arquitectura propuesta se basa en un modelo de cinco capas que integra: runtime seguro para agentes (OpenShell), framework de orquestaci\u00f3n (NeMo Agent Toolkit), blueprints pre-construidos (AI-Q, RAG, Data Flywheel), optimizaci\u00f3n de inferencia (TensorRT, Triton) y AI f\u00edsica (Cosmos, Isaac). Este enfoque modular permite implementaciones progresivas y adaptaci\u00f3n a m\u00faltiples dominios de soluci\u00f3n."),
        
        h1("2. Patr\u00f3n Arquitect\u00f3nico"),
        h2("2.1 Visi\u00f3n General"),
        body("NVIDIA ha dise\u00f1ado un ecosistema arquitect\u00f3nico cohesivo que sigue el principio de 'separation of concerns' con capas claramente definidas. Cada componente cumple una funci\u00f3n espec\u00edfica mientras mantiene interoperabilidad a trav\u00e9s de APIs estandarizadas y microservicios NIM."),
        
        h2("2.2 Arquitectura en Cinco Capas"),
        h3("Capa 1: Runtime y Seguridad (OpenShell)"),
        body("OpenShell representa la base fundamental de la infraestructura aut\u00f3noma. Proporciona entornos de ejecuci\u00f3n aislados (sandboxed) donde los agentes AI pueden operar de manera segura sin comprometer datos sensibles o infraestructura cr\u00edtica. Esta capa implementa:"),
        bullet("Aislamiento de procesos mediante contenedores seguros"),
        bullet("Pol\u00edticas de acceso basadas en roles (RBAC)"),
        bullet("Auditor\u00eda completa de acciones de agentes"),
        bullet("Protecci\u00f3n contra inyecci\u00f3n de prompts y manipulaci\u00f3n"),
        
        h3("Capa 2: Framework de Agentes (NeMo Agent Toolkit)"),
        body("El NeMo Agent Toolkit constituye el n\u00facleo de orquestaci\u00f3n de la plataforma. Implementa patrones de dise\u00f1o para la coordinaci\u00f3n de equipos de agentes, incluyendo:"),
        bullet("Patr\u00f3n Chain-of-Thought para razonamiento estructurado"),
        bullet("Patr\u00f3n ReAct para acciones con retroalimentaci\u00f3n"),
        bullet("Patr\u00f3n Multi-Agent Collaboration para equipos distribuidos"),
        bullet("Integraci\u00f3n nativa con LangChain y LlamaIndex"),
        
        h3("Capa 3: Blueprints de Soluci\u00f3n"),
        body("Los AI Blueprints proporcionan implementaciones de referencia probadas en producci\u00f3n para casos de uso espec\u00edficos:"),
        bullet("AI-Q: Agente de investigaci\u00f3n empresarial con capacidades de razonamiento profundo"),
        bullet("RAG: Pipeline de Retrieval-Augmented Generation con soporte multimodal"),
        bullet("Data Flywheel: Sistema de mejora continua aut\u00f3noma de modelos"),
        bullet("Video Search: An\u00e1lisis y b\u00fasqueda de video con agentes especializados"),
        
        h3("Capa 4: Inferencia y Optimizaci\u00f3n"),
        body("TensorRT y Triton Inference Server forman la capa de serving de modelos:"),
        bullet("TensorRT-LLM: Optimizaci\u00f3n espec\u00edfica para modelos de lenguaje"),
        bullet("Triton: Serving multi-modelo con soporte de auto-escalado"),
        bullet("NIM Microservices: APIs REST est\u00e1ndar para inferencia"),
        
        h3("Capa 5: AI F\u00edsica"),
        body("Cosmos e Isaac extienden la plataforma hacia aplicaciones f\u00edsicas:"),
        bullet("Cosmos Predict: World Foundation Models para simulaci\u00f3n"),
        bullet("Isaac GR00T: Modelos de fundaci\u00f3n para rob\u00f3tica"),
        
        new Paragraph({ children: [new PageBreak()] }),
        
        h1("3. Infraestructura Necesaria"),
        h2("3.1 Requisitos de Hardware"),
        createTable(
          ["Componente", "M\u00ednimo", "Recomendado", "Enterprise"],
          [
            ["GPU Compute", "RTX 4090 / A10", "A100 80GB", "H100 NVL"],
            ["VRAM", "24 GB", "80 GB", "188 GB"],
            ["CPU", "16 cores", "32 cores", "64+ cores"],
            ["RAM", "64 GB", "256 GB", "512+ GB"],
            ["Storage", "2 TB NVMe", "8 TB NVMe", "SAN/NVMe Array"],
            ["Network", "10 Gbps", "25 Gbps", "100 Gbps InfiniBand"]
          ]
        ),
        
        h2("3.2 Stack de Software"),
        createTable(
          ["Capa", "Componente", "Versi\u00f3n", "Prop\u00f3sito"],
          [
            ["Runtime", "Docker/Podman", "24.0+", "Contenedorizaci\u00f3n"],
            ["Orquestaci\u00f3n", "Kubernetes", "1.28+", "Orquestaci\u00f3n de contenedores"],
            ["ML Framework", "PyTorch", "2.2+", "Entrenamiento e inferencia"],
            ["CUDA", "CUDA Toolkit", "12.3+", "Computaci\u00f3n GPU"],
            ["Serving", "Triton", "2.40+", "Inference server"],
            ["Monitoring", "Prometheus/Grafana", "Latest", "Observabilidad"]
          ]
        ),
        
        h2("3.3 Arquitectura de Despliegue"),
        body("Se recomienda una arquitectura de microservicios desplegada en Kubernetes con los siguientes componentes:"),
        bullet("Namespace dedicado para cada blueprint (aislamiento l\u00f3gico)"),
        bullet("GPU Operator de NVIDIA para gesti\u00f3n de recursos GPU"),
        bullet("Network Policies para segmentaci\u00f3n de red"),
        bullet("Persistent Volumes para almacenamiento de modelos y datos"),
        bullet("Horizontal Pod Autoscaler para escalado autom\u00e1tico"),
        
        new Paragraph({ children: [new PageBreak()] }),
        
        h1("4. Dominios de Soluci\u00f3n"),
        h2("4.1 Healthcare y Biomedical"),
        h3("Repositorios Aplicables"),
        bullet("ambient-healthcare-agents: Generaci\u00f3n autom\u00e1tica de notas SOAP, transcripci\u00f3n m\u00e9dica con Riva"),
        bullet("biomedical-aiq-research-agent: Investigaci\u00f3n biom\u00e9dica, screening virtual de f\u00e1rmacos"),
        bullet("ai-virtual-assistant: Asistente virtual para pacientes y personal m\u00e9dico"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        body("Para implementar una soluci\u00f3n de healthcare, se recomienda:"),
        bullet("Capa de entrada: Digital Human para interfaz conversacional emp\u00e1tica"),
        bullet("Procesamiento: Riva para ASR/TTS en tiempo real"),
        bullet("Agentes: ambient-healthcare-agents para documentaci\u00f3n cl\u00ednica"),
        bullet("Knowledge Base: RAG con datos m\u00e9dicos actualizados (PubMed, gu\u00edas cl\u00ednicas)"),
        bullet("Compliance: OpenShell para auditor\u00eda y cumplimiento HIPAA"),
        
        h2("4.2 Warehouse y Log\u00edstica"),
        h3("Repositorios Aplicables"),
        bullet("Multi-Agent-Intelligent-Warehouse: Sistema multi-agente para operaciones de almac\u00e9n"),
        bullet("video-search-and-summarization: Monitoreo de operaciones por video"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Perception: Video analytics para conteo, detecci\u00f3n de anomal\u00edas"),
        bullet("Planning: Agentes de optimizaci\u00f3n de rutas y ubicaci\u00f3n"),
        bullet("Execution: Control de robots y sistemas de picking"),
        bullet("Integration: APIs con WMS existentes (SAP, Oracle)"),
        
        h2("4.3 3D y Digital Twins"),
        h3("Repositorios Aplicables"),
        bullet("digital-human: Avatares 3D para interacci\u00f3n humana"),
        bullet("cosmos-predict2.5: Simulaci\u00f3n f\u00edsica realista"),
        bullet("Isaac-GR00T: Modelos para rob\u00f3tica y manipulaci\u00f3n"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Asset Generation: NeMo para generaci\u00f3n de texturas y modelos"),
        bullet("Animation: Digital Human para movimiento natural"),
        bullet("Physics: Cosmos para simulaci\u00f3n de f\u00edsica realista"),
        bullet("Rendering: Omniverse para visualizaci\u00f3n en tiempo real"),
        
        h2("4.4 Agricultura"),
        h3("Repositorios Aplicables"),
        bullet("video-search-and-summarization: An\u00e1lisis de im\u00e1genes de cultivos"),
        bullet("data-flywheel: Mejora continua de modelos de detecci\u00f3n"),
        bullet("RAG: Knowledge base de pr\u00e1cticas agr\u00edcolas"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Data Collection: Drones y sensores IoT"),
        bullet("Analysis: Video analytics para detecci\u00f3n de plagas y enfermedades"),
        bullet("Prediction: Modelos de rendimiento de cultivos"),
        bullet("Decision Support: Agentes de recomendaci\u00f3n para agricultores"),
        
        h2("4.5 IoT e Industrial"),
        h3("Repositorios Aplicables"),
        bullet("data-flywheel: Procesamiento continuo de datos de sensores"),
        bullet("OSMO: Orquestaci\u00f3n de workflows de datos"),
        bullet("aiq: An\u00e1lisis de causa ra\u00edz y diagn\u00f3stico"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Edge: Inferencia en dispositivos Jetson"),
        bullet("Streaming: Kafka para ingesti\u00f3n de datos"),
        bullet("Processing: OSMO para pipelines de datos"),
        bullet("Analytics: AI-Q para insights automatizados"),
        
        h2("4.6 Research y Academia"),
        h3("Repositorios Aplicables"),
        bullet("aiq: Agente de investigaci\u00f3n empresarial"),
        bullet("biomedical-aiq-research-agent: Investigaci\u00f3n biom\u00e9dica especializada"),
        bullet("rag: B\u00fasqueda en literatura cient\u00edfica"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Literature Mining: RAG con bases de datos cient\u00edficas"),
        bullet("Hypothesis Generation: AI-Q para propuestas de investigaci\u00f3n"),
        bullet("Experiment Design: Agentes especializados por dominio"),
        
        h2("4.7 Video y Media"),
        h3("Repositorios Aplicables"),
        bullet("video-search-and-summarization: An\u00e1lisis y resumen de video"),
        bullet("digital-human: Avatares para contenido"),
        bullet("ai-virtual-assistant: Asistentes para plataformas de streaming"),
        
        h3("Arquitectura de Soluci\u00f3n"),
        bullet("Ingest: Streaming de video en tiempo real"),
        bullet("Processing: Detecci\u00f3n de objetos, escenas, texto"),
        bullet("Indexing: B\u00fasqueda sem\u00e1ntica en contenido"),
        bullet("Generation: Res\u00famenes autom\u00e1ticos y highlights"),
        
        new Paragraph({ children: [new PageBreak()] }),
        
        h1("5. An\u00e1lisis Detallado por Repositorio"),
        
        h2("5.1 AI-Q (Enterprise Research Agent)"),
        h3("Descripci\u00f3n"),
        body("AI-Q es un agente de investigaci\u00f3n empresarial construido sobre NeMo Agent Toolkit que utiliza LangChain Deep Agents para proporcionar capacidades de razonamiento avanzado. El sistema puede conectarse a datos empresariales, razonar sobre ellos y generar insights accionables."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Integraci\u00f3n con m\u00faltiples fuentes de datos empresariales"),
        bullet("Razonamiento multi-paso con verificaci\u00f3n de hip\u00f3tesis"),
        bullet("Generaci\u00f3n de reportes automatizados"),
        bullet("APIs REST para integraci\u00f3n con sistemas existentes"),
        h3("Casos de Uso Recomendados"),
        bullet("Investigaci\u00f3n de mercado competitiva"),
        bullet("An\u00e1lisis de tendencias financieras"),
        bullet("Due diligence automatizada"),
        bullet("Monitoreo de reputaci\u00f3n de marca"),
        
        h2("5.2 Data Flywheel"),
        h3("Descripci\u00f3n"),
        body("Data Flywheel implementa un sistema de mejora continua aut\u00f3noma que utiliza el ciclo: datos \u2192 entrenamiento \u2192 inferencia \u2192 evaluaci\u00f3n \u2192 m\u00e1s datos. Este patr\u00f3n permite que los modelos mejoren autom\u00e1ticamente con el uso."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Detecci\u00f3n autom\u00e1tica de drift en datos"),
        bullet("Reentrenamiento incremental de modelos"),
        bullet("Evaluaci\u00f3n continua de calidad"),
        bullet("Versionado autom\u00e1tico de modelos"),
        h3("Casos de Uso Recomendados"),
        bullet("Sistemas de recomendaci\u00f3n personalizados"),
        bullet("Detecci\u00f3n de fraude adaptativa"),
        bullet("Modelos predictivos de demanda"),
        bullet("Personalizaci\u00f3n de contenido"),
        
        h2("5.3 RAG Blueprint"),
        h3("Descripci\u00f3n"),
        body("El blueprint RAG proporciona una implementaci\u00f3n completa de Retrieval-Augmented Generation con soporte para m\u00faltiples modalidades (texto, im\u00e1genes, tablas). Incluye pipelines de ingesti\u00f3n, indexaci\u00f3n y recuperaci\u00f3n optimizados."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Soporte multimodal nativo"),
        bullet("Chunking inteligente adaptativo"),
        bullet("Reranking con modelos especializados"),
        bullet("Caching para optimizaci\u00f3n de latencia"),
        h3("Casos de Uso Recomendados"),
        bullet("Asistentes de conocimiento empresarial"),
        bullet("B\u00fasqueda en documentaci\u00f3n t\u00e9cnica"),
        bullet("Sistemas de Q&A para clientes"),
        bullet("Base de conocimiento legal"),
        
        h2("5.4 Video Search and Summarization"),
        h3("Descripci\u00f3n"),
        body("Este blueprint implementa un sistema completo de an\u00e1lisis de video que permite b\u00fasqueda sem\u00e1ntica, generaci\u00f3n de res\u00famenes y Q&A sobre contenido de video. Utiliza modelos de visi\u00f3n-lenguaje para comprensi\u00f3n multimodal."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Indexaci\u00f3n de video a escala"),
        bullet("B\u00fasqueda por texto, imagen o similaridad"),
        bullet("Generaci\u00f3n de res\u00famenes temporales"),
        bullet("Detecci\u00f3n de eventos y objetos"),
        h3("Casos de Uso Recomendados"),
        bullet("Monitoreo de seguridad"),
        bullet("An\u00e1lisis de contenido deportivo"),
        bullet("Indexaci\u00f3n de reuniones grabadas"),
        bullet("Moderaci\u00f3n de contenido"),
        
        h2("5.5 AI Virtual Assistant"),
        h3("Descripci\u00f3n"),
        body("Blueprint completo para asistentes virtuales conversacionales con capacidades de understanding de intenciones, gesti\u00f3n de contexto multi-turno y ejecuci\u00f3n de acciones."),
        h3("Caracter\u00edsticas Principales"),
        bullet("NLU/NLG integrado con NIM"),
        bullet("Gesti\u00f3n de contexto conversacional"),
        bullet("Integraci\u00f3n con sistemas de tickets"),
        bullet("An\u00e1lisis de sentimiento en tiempo real"),
        h3("Casos de Uso Recomendados"),
        bullet("Soporte al cliente 24/7"),
        bullet("Asistentes de recursos humanos"),
        bullet("Gu\u00edas interactivas de productos"),
        bullet("Onboarding de empleados"),
        
        h2("5.6 Digital Human"),
        h3("Descripci\u00f3n"),
        body("Tokkio Digital Human proporciona una interfaz de avatar 3D animado para interacciones m\u00e1s naturales y emp\u00e1ticas. Combina s\u00edntesis de voz, animaci\u00f3n facial y respuesta en tiempo real."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Avatar 3D con animaci\u00f3n facial sincronizada"),
        bullet("Integraci\u00f3n con Audio2Face de NVIDIA"),
        bullet("M\u00faltiples personajes personalizables"),
        bullet("Latencia de respuesta optimizada"),
        h3("Casos de Uso Recomendados"),
        bullet("Kioscos de atenci\u00f3n al cliente"),
        bullet("Entrenamiento y simulaci\u00f3n"),
        bullet("Presentaciones virtuales"),
        bullet("Asistentes de marca"),
        
        h2("5.7 Ambient Healthcare Agents"),
        h3("Descripci\u00f3n"),
        body("Sistema especializado para generaci\u00f3n autom\u00e1tica de documentaci\u00f3n cl\u00ednica mediante escucha ambiental de consultas m\u00e9dicas. Cumple con est\u00e1ndares de privacidad healthcare."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Transcripci\u00f3n m\u00e9dica especializada con Riva"),
        bullet("Extracci\u00f3n de entidades m\u00e9dicas (SNOMED, ICD-10)"),
        bullet("Generaci\u00f3n de notas SOAP estructuradas"),
        bullet("Cumplimiento HIPAA integrado"),
        h3("Casos de Uso Recomendados"),
        bullet("Documentaci\u00f3n cl\u00ednica automatizada"),
        bullet("Res\u00famenes de consulta"),
        bullet("Codificaci\u00f3n de diagn\u00f3sticos"),
        bullet("Transcripci\u00f3n quir\u00fargica"),
        
        h2("5.8 Biomedical AI-Q Research Agent"),
        h3("Descripci\u00f3n"),
        body("Agente especializado en investigaci\u00f3n biom\u00e9dica con capacidades de screening virtual de compuestos, an\u00e1lisis de literatura cient\u00edfica y generaci\u00f3n de hip\u00f3tesis."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Screening virtual de f\u00e1rmacos"),
        bullet("An\u00e1lisis de interacciones moleculares"),
        bullet("Mining de literatura biom\u00e9dica"),
        bullet("Generaci\u00f3n de hip\u00f3tesis de investigaci\u00f3n"),
        h3("Casos de Uso Recomendados"),
        bullet("Descubrimiento de f\u00e1rmacos"),
        bullet("An\u00e1lisis de ensayos cl\u00ednicos"),
        bullet("Biolog\u00eda computacional"),
        bullet("Medicina personalizada"),
        
        h2("5.9 Multi-Agent Intelligent Warehouse"),
        h3("Descripci\u00f3n"),
        body("Sistema multi-agente completo para automatizaci\u00f3n de operaciones de almac\u00e9n, incluyendo gesti\u00f3n de inventario, optimizaci\u00f3n de picking y coordinaci\u00f3n de robots."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Coordinaci\u00f3n multi-robot"),
        bullet("Optimizaci\u00f3n de rutas en tiempo real"),
        bullet("Predicci\u00f3n de demanda"),
        bullet("Detecci\u00f3n de anomal\u00edas operativas"),
        h3("Casos de Uso Recomendados"),
        bullet("E-commerce fulfillment"),
        bullet("Gesti\u00f3n de inventario automatizada"),
        bullet("Log\u00edstica inversa"),
        bullet("Control de calidad automatizado"),
        
        h2("5.10 Quantitative Portfolio Optimization"),
        h3("Descripci\u00f3n"),
        body("Blueprint para optimizaci\u00f3n cuantitativa de portafolios utilizando t\u00e9cnicas avanzadas de ML y optimizaci\u00f3n matem\u00e1tica."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Optimizaci\u00f3n mean-variance"),
        bullet("Risk parity strategies"),
        bullet("Factor investing"),
        bullet("Backtesting automatizado"),
        h3("Casos de Uso Recomendados"),
        bullet("Gesti\u00f3n de fondos"),
        bullet("Robo-advisory"),
        bullet("Trading algor\u00edtmico"),
        bullet("An\u00e1lisis de riesgo"),
        
        h2("5.11 NIM Usage Scanner"),
        h3("Descripci\u00f3n"),
        body("Herramienta de an\u00e1lisis est\u00e1tico para detectar y catalogar el uso de NIM microservices en repositorios de c\u00f3digo."),
        h3("Caracter\u00edsticas Principales"),
        bullet("Detecci\u00f3n autom\u00e1tica de endpoints NIM"),
        bullet("An\u00e1lisis de patrones de uso"),
        bullet("Reportes de inventario"),
        bullet("Detecci\u00f3n de versiones deprecated"),
        h3("Casos de Uso Recomendados"),
        bullet("Auditor\u00eda de infraestructura ML"),
        bullet("Migraci\u00f3n de versiones"),
        bullet("Documentaci\u00f3n automatizada"),
        bullet("Compliance checking"),
        
        new Paragraph({ children: [new PageBreak()] }),
        
        h1("6. Frameworks Core"),
        h2("6.1 NeMo Agent Toolkit"),
        body("Framework open-source para construcci\u00f3n de equipos de agentes AI. Proporciona abstracciones de alto nivel para patrones comunes de agentes, integraci\u00f3n con frameworks populares y herramientas de debugging."),
        h3("Patrones Soportados"),
        bullet("Sequential: Agentes en cadena"),
        bullet("Parallel: Ejecuci\u00f3n concurrente"),
        bullet("Hierarchical: Agentes supervisores"),
        bullet("Debates: Agentes contradictorios para verificaci\u00f3n"),
        
        h2("6.2 NeMo Framework"),
        body("Framework completo para entrenamiento y fine-tuning de modelos de lenguaje a escala. Incluye soporte para distributed training, checkpointing y optimizaciones espec\u00edficas de hardware NVIDIA."),
        
        h2("6.3 TensorRT y TensorRT-LLM"),
        body("SDK de optimizaci\u00f3n de inferencia que proporciona speedups significativos sobre inference nativa de PyTorch. TensorRT-LLM extiende estas capacidades espec\u00edficamente para modelos de lenguaje."),
        
        h2("6.4 Triton Inference Server"),
        body("Servidor de inferencia multi-modelo que soporta m\u00faltiples frameworks (TensorFlow, PyTorch, ONNX, TensorRT) con capacidades de auto-escalado y batching din\u00e1mico."),
        
        h2("6.5 OpenShell"),
        body("Runtime seguro para agentes aut\u00f3nomos que proporciona entornos sandboxed, pol\u00edticas de seguridad y auditor\u00eda completa de operaciones."),
        
        h2("6.6 OSMO"),
        body("Plataforma developer-first para escalar workflows de ML, versionado de datasets y desarrollo remoto en nodos backend."),
        
        h2("6.7 Cosmos Predict"),
        body("World Foundation Models para AI f\u00edsica, dise\u00f1ado para veh\u00edculos aut\u00f3nomos, robots y simulaci\u00f3n de sistemas del mundo real."),
        
        h2("6.8 Isaac GR00T"),
        body("Modelo de fundaci\u00f3n para rob\u00f3tica que permite transferencia de habilidades de simulaci\u00f3n a robots reales."),
        
        new Paragraph({ children: [new PageBreak()] }),
        
        h1("7. Recomendaciones de Implementaci\u00f3n"),
        h2("7.1 Fase 1: Fundamentos (Meses 1-2)"),
        bullet("Desplegar OpenShell en entorno de desarrollo"),
        bullet("Configurar NeMo Agent Toolkit con modelo base"),
        bullet("Implementar RAG Blueprint con datos internos"),
        bullet("Establecer pipeline CI/CD para modelos"),
        
        h2("7.2 Fase 2: Casos de Uso (Meses 3-4)"),
        bullet("Implementar AI-Q para investigaci\u00f3n interna"),
        bullet("Desplegar asistente virtual para soporte"),
        bullet("Configurar Data Flywheel para mejora continua"),
        bullet("Integrar con sistemas empresariales existentes"),
        
        h2("7.3 Fase 3: Escalado (Meses 5-6)"),
        bullet("Desplegar Triton para serving production"),
        bullet("Implementar m\u00faltiples blueprints por dominio"),
        bullet("Configurar monitoreo y alertas"),
        bullet("Optimizar costos de GPU"),
        
        h2("7.4 Fase 4: AI F\u00edsica (Meses 7+)"),
        bullet("Evaluar Cosmos para simulaci\u00f3n"),
        bullet("Integrar Isaac para casos rob\u00f3ticos"),
        bullet("Desplegar Digital Humans para interacci\u00f3n"),
        bullet("Expandir a edge computing con Jetson"),
        
        h1("8. Conclusiones"),
        body("El ecosistema NVIDIA AI Blueprints proporciona una base s\u00f3lida y probada en producci\u00f3n para construir infraestructura digital aut\u00f3noma empresarial. La arquitectura modular de cinco capas permite implementaciones progresivas mientras que la integraci\u00f3n nativa entre componentes reduce significativamente el tiempo de desarrollo."),
        body("Los 28 repositorios analizados cubren un espectro amplio de casos de uso, desde healthcare hasta manufactura, pasando por finanzas y research. La clave del \u00e9xito est\u00e1 en seleccionar los blueprints apropiados para cada dominio y personalizarlos con datos y procesos espec\u00edficos de la organizaci\u00f3n."),
        body("La recomendaci\u00f3n principal es comenzar con OpenShell y NeMo Agent Toolkit como fundaci\u00f3n, luego implementar RAG y AI-Q como primeros casos de uso, y finalmente expandir hacia dominios especializados utilizando los blueprints espec\u00edficos disponibles en el ecosistema."),
        
        new Paragraph({ spacing: { before: 600 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "\u2014 Fin del Informe \u2014", size: 20, color: c(P.secondary), italics: true })]
        })
      ]
    }
  ]
});

// Generate
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/z/my-project/download/NVIDIA_Plataforma_Infraestructura_Autonoma.docx", buffer);
  console.log("\u2705 Document generated successfully");
});
