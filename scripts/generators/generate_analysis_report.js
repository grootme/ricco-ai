const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType, PageBreak } = require('docx');
const fs = require('fs');

// Paleta Deep Cyan (DM-1) para Tech/AI
const palette = {
  primary: "#162235",
  accent: "#37DCF2",
  body: "#FFFFFF",
  subtitle: "#B0B8C0",
  meta: "#90989F",
  surface: "#EDF3F5"
};

const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" },
          size: 24,
          color: "000000"
        },
        paragraph: {
          spacing: { line: 312 }
        }
      },
      heading1: {
        run: {
          font: { ascii: "Calibri", eastAsia: "SimHei" },
          size: 32,
          bold: true,
          color: "162235"
        }
      },
      heading2: {
        run: {
          font: { ascii: "Calibri", eastAsia: "SimHei" },
          size: 28,
          bold: true,
          color: "162235"
        }
      },
      heading3: {
        run: {
          font: { ascii: "Calibri", eastAsia: "SimHei" },
          size: 26,
          bold: true,
          color: "1B6B7A"
        }
      }
    }
  },
  sections: [
    // COVER
    {
      properties: {
        page: { margin: { top: 0, right: 0, bottom: 0, left: 0 } }
      },
      children: [
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          borders: {
            top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            insideVertical: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }
          },
          rows: [
            new TableRow({
              height: { value: 16838, rule: "exact" },
              children: [
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "162235" },
                  width: { size: 100, type: WidthType.PERCENTAGE },
                  children: [
                    new Paragraph({ spacing: { before: 2500 }, children: [] }),
                    new Paragraph({
                      alignment: AlignmentType.CENTER,
                      spacing: { before: 1000, after: 400 },
                      children: [
                        new TextRun({
                          text: "RICCO AI",
                          font: { ascii: "Calibri", eastAsia: "SimHei" },
                          size: 72,
                          bold: true,
                          color: "37DCF2"
                        })
                      ]
                    }),
                    new Paragraph({
                      alignment: AlignmentType.CENTER,
                      spacing: { before: 200, after: 600 },
                      children: [
                        new TextRun({
                          text: "Analisis de Arquitectura y Deuda Tecnica",
                          font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" },
                          size: 36,
                          color: "FFFFFF"
                        })
                      ]
                    }),
                    new Paragraph({
                      alignment: AlignmentType.CENTER,
                      spacing: { before: 400 },
                      children: [
                        new TextRun({
                          text: "Duplicaciones, Patrones GOF, Protocolos y Refactorizacion",
                          font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" },
                          size: 24,
                          color: "B0B8C0"
                        })
                      ]
                    }),
                    new Paragraph({ spacing: { before: 5000 }, children: [] }),
                    new Paragraph({
                      alignment: AlignmentType.CENTER,
                      children: [
                        new TextRun({
                          text: "Version 1.0 - Mayo 2026",
                          font: { ascii: "Calibri", eastAsia: "Microsoft YaHei" },
                          size: 20,
                          color: "687078"
                        })
                      ]
                    })
                  ]
                })
              ]
            })
          ]
        })
      ]
    },
    // BODY
    {
      properties: {
        page: {
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
          pageNumbers: { start: 1, formatType: "decimal" }
        }
      },
      children: [
        // Section 1
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun({ text: "1. Resumen Ejecutivo", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Este analisis identifica problemas criticos en la arquitectura del proyecto RICCO AI. Se detectaron 164 archivos Python con 55,467 lineas de codigo, presentando duplicaciones significativas, inconsistencias en patrones de diseno y deuda tecnica que requiere atencion inmediata."
            })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Los hallazgos principales incluyen: estructura paralela app/ y src/ sin separacion clara, tres implementaciones del protocolo A2A, multiples versiones de servicios duplicados, y violaciones a principios SOLID y patrones GOF fundamentales."
            })
          ]
        }),

        // Section 2
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun({ text: "2. Problemas Criticos de Arquitectura", bold: true })]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "2.1 Estructura Duplicada app/ vs src/", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El proyecto mantiene dos estructuras de directorios paralelas que causan confusion y duplicacion. La carpeta app/ contiene servicios como a2ui_service.py (48KB), evoai_service.py, multimedia_service.py, mientras que src/services/ tiene versiones diferentes de los mismos servicios. Esto indica una migracion incompleta o falta de definicion sobre cual estructura es la canonica."
            })
          ]
        }),

        // Table: Duplications
        new Paragraph({
          spacing: { before: 200, after: 100 },
          children: [
            new TextRun({ text: "Duplicaciones Detectadas:", bold: true, size: 22 })
          ]
        }),
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          borders: {
            top: { style: BorderStyle.SINGLE, size: 2, color: "1B6B7A" },
            bottom: { style: BorderStyle.SINGLE, size: 2, color: "1B6B7A" },
            left: { style: BorderStyle.NONE },
            right: { style: BorderStyle.NONE },
            insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" },
            insideVertical: { style: BorderStyle.NONE }
          },
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Archivo 1", bold: true, color: "FFFFFF", size: 22 })] })]
                }),
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Archivo 2", bold: true, color: "FFFFFF", size: 22 })] })]
                }),
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Problema", bold: true, color: "FFFFFF", size: 22 })] })]
                })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "app/services/a2ui_service.py (48KB)", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/services/a2ui_service.py (6KB)", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Versiones incompatibles", size: 21, color: "C0392B" })] })] })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/api/a2a_routes.py (1805 lineas)", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/services/a2a_sdk_adapter.py", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Logica duplicada A2A", size: 21, color: "C0392B" })] })] })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/schemas/a2a_types.py", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/schemas/a2a_enhanced_types.py", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Tipos duplicados", size: 21, color: "C0392B" })] })] })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/services/a2ui_service.py", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "src/services/a2ui_service_enhanced.py", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Tres versiones A2UI", size: 21, color: "C0392B" })] })] })
              ]
            })
          ]
        }),

        // Section 2.2
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 300 },
          children: [new TextRun({ text: "2.2 Funciones Duplicadas", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Se identificaron funciones duplicadas en multiples archivos que realizan la misma funcionalidad con ligeras variaciones. La funcion extract_text_from_message aparece en a2a_routes.py y a2a_sdk_adapter.py. La funcion get_agent_card esta implementada en tres lugares diferentes. Esto viola el principio DRY (Don't Repeat Yourself) y dificulta el mantenimiento."
            })
          ]
        }),

        // Section 3
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "3. Problemas de Patrones GOF", bold: true })]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "3.1 Factory Pattern - Implementacion Incompleta", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El patron Factory esta implementado en src/agents/factory/ pero no se utiliza de manera consistente. Existe AgentFactory que crea SwarmAgent, pero tambien existe AgentBuilder en src/services/adk/agent_builder.py que construye agentes de otra forma. Esto crea confusion sobre cual mecanismo usar para crear agentes y puede llevar a inconsistencias en la configuracion de los mismos."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "3.2 Adapter Pattern - Sobreimplementado", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El patron Adapter se utiliza excesivamente para el protocolo A2A. Existen tres adaptadores diferentes: a2a_routes.py (implementacion custom), a2a_sdk_adapter.py (adaptador SDK oficial), y a2a_enhanced_client.py (cliente mejorado). Cada uno convierte entre formatos de manera diferente, creando una complejidad innecesaria. Lo ideal seria tener un unico adaptador que maneje todas las conversiones."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "3.3 Singleton Pattern - Ausente", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El patron Singleton no esta implementado correctamente para servicios criticos. Se observa el uso de variables globales como _orchestrator en __init__.py, pero sin proteccion contra instanciacion multiple. Los servicios como session_service, artifacts_service y memory_service se pasan como parametros en lugar de ser accesibles como singletons bien definidos."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "3.4 Strategy Pattern - No Aplicado", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El patron Strategy no se aplica en el manejo de diferentes protocolos y formatos de mensaje. El codigo usa condicionales if/elif extensos en a2a_routes.py para manejar diferentes metodos JSON-RPC. Una implementacion con Strategy permitiria agregar nuevos metodos sin modificar el codigo existente, siguiendo el principio Open/Closed."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "3.5 Template Method - Duplicacion en agent_runner.py", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Las funciones run_agent() y run_agent_stream() comparten aproximadamente 90% del codigo. Esto es un caso clasico donde el patron Template Method deberia aplicarse para extraer el flujo comun en una clase base y permitir que las subclases definan solo las diferencias. Actualmente, cualquier cambio debe aplicarse en dos lugares."
            })
          ]
        }),

        // Section 4
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "4. Problemas de Protocolos", bold: true })]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "4.1 Protocolo A2A - Tres Implementaciones", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El protocolo Agent-to-Agent (A2A) de Google tiene tres implementaciones en el proyecto, lo cual genera confusion y posibles inconsistencias. La implementacion custom en a2a_routes.py implementa metodos message/send y message/stream directamente. El adaptador SDK en a2a_sdk_adapter.py intenta usar el SDK oficial con fallback a implementacion propia. El cliente mejorado en a2a_enhanced_client.py proporciona una interfaz unificada pero agrega otra capa de complejidad."
            })
          ]
        }),

        // Table: A2A Implementations
        new Paragraph({
          spacing: { before: 200, after: 100 },
          children: [
            new TextRun({ text: "Comparacion de Implementaciones A2A:", bold: true, size: 22 })
          ]
        }),
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          borders: {
            top: { style: BorderStyle.SINGLE, size: 2, color: "1B6B7A" },
            bottom: { style: BorderStyle.SINGLE, size: 2, color: "1B6B7A" },
            left: { style: BorderStyle.NONE },
            right: { style: BorderStyle.NONE },
            insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" },
            insideVertical: { style: BorderStyle.NONE }
          },
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Implementacion", bold: true, color: "FFFFFF", size: 22 })] })]
                }),
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Lineas", bold: true, color: "FFFFFF", size: 22 })] })]
                }),
                new TableCell({
                  shading: { type: ShadingType.CLEAR, fill: "1B6B7A" },
                  margins: { top: 60, bottom: 60, left: 120, right: 120 },
                  children: [new Paragraph({ children: [new TextRun({ text: "Problemas", bold: true, color: "FFFFFF", size: 22 })] })]
                })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "a2a_routes.py (Custom)", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "1805", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Funciones gigantes, logging excesivo", size: 21 })] })] })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "a2a_sdk_adapter.py", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "398", size: 21 })] })] }),
                new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EDF3F5" }, margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Fallback inconsistente, TODOs sin resolver", size: 21 })] })] })
              ]
            }),
            new TableRow({
              children: [
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "a2a_enhanced_client.py", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "746", size: 21 })] })] }),
                new TableCell({ margins: { top: 60, bottom: 60, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Duplica logica de conversion", size: 21 })] })] })
              ]
            })
          ]
        }),

        // Section 4.2
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 300 },
          children: [new TextRun({ text: "4.2 Protocolo MCP - Falta de Cohesion", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El protocolo Model Context Protocol (MCP) se implementa en tres directorios diferentes: src/mcp/proxy/, src/mcp/registry/ y src/mcp/tools/. Sin embargo, no existe una clara separacion de responsabilidades. El archivo mcp_arsenal.py en services mezcla la logica de herramientas con la configuracion de servidores. Se recomienda reorganizar siguiendo el patron Repository para el registro de herramientas y el patron Proxy para la comunicacion con servidores MCP."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "4.3 Protocolo A2UI - Tres Servicios", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El SDK A2UI de Google para generacion de UI dinamica tiene tres implementaciones de servicio. El servicio en app/services/a2ui_service.py tiene 1440 lineas con funcionalidad completa. El servicio en src/services/a2ui_service.py es una version reducida de solo 200 lineas. El servicio mejorado en src/services/a2ui_service_enhanced.py agrega context bundles pero duplica funcionalidad. Esta fragmentacion hace imposible saber cual servicio usar en cada situacion."
            })
          ]
        }),

        // Section 5
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "5. Deuda Tecnica Identificada", bold: true })]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "5.1 TODOs y FIXMEs Pendientes", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Se identificaron multiples comentarios TODO y FIXME en el codigo que indican trabajo incompleto. En a2a_sdk_adapter.py existe un TODO para procesar archivos que nunca se completo. En streaming_service.py hay un TODO para obtener eventos de la cola. En sanitization/routes.py falta verificacion de permisos de administrador. Estos items representan funcionalidad incompleta que puede causar problemas en produccion."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "5.2 Logging Excesivo", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El codigo contiene un numero excesivo de instrucciones de logging con emojis y mensajes de debug. Por ejemplo, agent_runner.py tiene mas de 30 instrucciones logger.info() con emojis, incluyendo mensajes como DEBUG - Processing file, DEBUG - File size, etc. Estos logs deben ser condicionales al nivel DEBUG o eliminados en produccion para evitar impacto en rendimiento."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "5.3 Imports Opcionales con try/except", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El patron de importacion opcional con try/except se usa extensivamente para el SDK de A2A. Cinco archivos diferentes implementan el patron SDK_AVAILABLE con el mismo bloque try/except. Esto indica dependencias inestables que deberian manejarse de forma centralizada. Se recomienda crear un modulo de compatibilidad que maneje todas las importaciones opcionales en un solo lugar."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "5.4 Funciones Demasiado Largas", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Multiples funciones exceden las 100 lineas, violando el principio de responsabilidad unica. La funcion run_agent() tiene 229 lineas. La funcion handle_message_send() en a2a_routes.py tiene mas de 200 lineas. La funcion convert_sets() esta definida dentro de agent_runner.py en lugar de ser un modulo de utilidades. Se recomienda extraer funciones auxiliares y aplicar el patron Extract Method."
            })
          ]
        }),

        // Section 6
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "6. Recomendaciones de Refactorizacion", bold: true })]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "6.1 Consolidar Estructura de Directorios", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Eliminar la estructura app/ y mantener unicamente src/ como directorio fuente canónico. Migrar el codigo util de app/services/ a src/services/ y eliminar los archivos duplicados. Esto reducira la confusion y facilitara el mantenimiento del codigo."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "6.2 Unificar Implementaciones A2A", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Consolidar las tres implementaciones del protocolo A2A en una unica implementacion. Crear una jerarquia de clases usando el patron Strategy donde la implementacion base maneje el protocolo y las subclases proporcionen adaptadores especificos para SDK custom y oficial. Eliminar a2a_enhanced_client.py y mover su funcionalidad al adaptador principal."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "6.3 Aplicar Template Method en agent_runner.py", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Crear una clase AgentRunner con un metodo template execute() que defina el flujo comun. Las subclases SyncAgentRunner y StreamingAgentRunner implementaran las diferencias especificas. Extraer el procesamiento de archivos, la creacion de sesiones y el manejo de eventos a metodos separados. Esto reducira la duplicacion de codigo en mas de 300 lineas."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "6.4 Implementar Singleton Correctamente", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Crear un modulo de servicios singleton que utilice el patron de modulo de Python para garantizar una unica instancia. Implementar get_session_service(), get_artifacts_service() y get_memory_service() como funciones que retornen la instancia unica. Eliminar el paso de estos servicios como parametros en las funciones."
            })
          ]
        }),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: "6.5 Crear Modulo de Compatibilidad", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Crear src/utils/compat.py que centralice todas las importaciones opcionales. Este modulo debe exponer funciones has_a2a_sdk(), get_a2a_types(), etc. que manejen los imports de forma transparente. Eliminar los bloques try/except duplicados en multiples archivos."
            })
          ]
        }),

        // Section 7
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "7. Plan de Accion Priorizado", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Se recomienda el siguiente orden de ejecucion para maximizar el impacto y minimizar el riesgo:" })
          ]
        }),
        new Paragraph({
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Prioridad Alta (Semana 1-2):", bold: true, color: "C0392B" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Consolidar estructura app/ hacia src/" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Unificar las tres implementaciones A2A" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Resolver TODOs criticos en archivos principales" })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "- Eliminar logging excesivo con emojis" })
          ]
        }),
        new Paragraph({
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Prioridad Media (Semana 3-4):", bold: true, color: "E67E22" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Aplicar Template Method en agent_runner.py" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Implementar Singleton para servicios" })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "- Crear modulo de compatibilidad centralizado" })
          ]
        }),
        new Paragraph({
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Prioridad Baja (Semana 5-6):", bold: true, color: "27AE60" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Reorganizar estructura MCP" })
          ]
        }),
        new Paragraph({
          spacing: { after: 50 },
          children: [
            new TextRun({ text: "- Unificar servicios A2UI" })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "- Documentar arquitectura consolidada" })
          ]
        }),

        // Section 8
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300 },
          children: [new TextRun({ text: "8. Conclusiones", bold: true })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "El proyecto RICCO AI tiene una base solida pero presenta problemas arquitectonicos significativos derivados de una migracion incompleta y falta de estandares de codificacion. La existencia de estructuras duplicadas, multiples implementaciones del mismo protocolo y patrones de diseno aplicados inconsistentemente generan deuda tecnica que dificulta el mantenimiento y la escalabilidad."
            })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Las recomendaciones presentadas permitiran reducir aproximadamente un 30% del codigo duplicado, mejorar la cohesión de los modulos y facilitar la incorporacion de nuevas funcionalidades. La priorizacion sugerida minimiza el riesgo de regresiones mientras se abordan los problemas mas criticos primero."
            })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            new TextRun({
              text: "Se recomienda establecer guias de estilo y revisiones de codigo que prevengan la acumulacion de deuda tecnica en el futuro. La implementacion de pruebas automatizadas ayudara a detectar regresiones durante el proceso de refactorizacion."
            })
          ]
        })
      ]
    }
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/z/my-project/download/RICCO_AI_Architecture_Analysis.docx', buffer);
  console.log('Documento generado: /home/z/my-project/download/RICCO_AI_Architecture_Analysis.docx');
}).catch(err => {
  console.error('Error:', err);
});
