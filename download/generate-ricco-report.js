const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer, 
        AlignmentType, PageOrientation, LevelFormat, HeadingLevel, BorderStyle, WidthType, 
        ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents } = require('docx');
const fs = require('fs');

// Color palette - Midnight Code (Technology theme)
const colors = {
  primary: "020617",      // Midnight Black
  body: "1E293B",         // Deep Slate Blue
  secondary: "64748B",    // Cool Blue-Gray
  accent: "94A3B8",       // Steady Silver
  tableBg: "F8FAFC",      // Glacial Blue-White
  tableHeader: "E2E8F0",  // Light slate
};

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: colors.accent };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

// Read the catalog JSON
const catalog = JSON.parse(fs.readFileSync('/home/z/my-project/ecosystem/erpnext/apps/ricco-apps-catalog.json', 'utf8'));

// Helper functions
function createHeaderCell(text, width = 2340) {
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: colors.tableHeader, type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ 
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 60 },
      children: [new TextRun({ text, bold: true, size: 20, color: colors.primary })]
    })]
  });
}

function createDataCell(text, width = 2340, center = false) {
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ 
      alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
      spacing: { before: 40, after: 40 },
      children: [new TextRun({ text, size: 18, color: colors.body })]
    })]
  });
}

function createAppTable(apps) {
  const rows = [
    new TableRow({
      tableHeader: true,
      children: [
        createHeaderCell("App", 2800),
        createHeaderCell("Descripción", 4000),
        createHeaderCell("Prioridad", 1280),
        createHeaderCell("Estado", 1280)
      ]
    })
  ];
  
  apps.forEach(app => {
    rows.push(new TableRow({
      children: [
        createDataCell(app.name || app.app, 2800),
        createDataCell(app.description || app.reason || "", 4000),
        createDataCell(app.priority || "", 1280, true),
        createDataCell(app.status || "", 1280, true)
      ]
    }));
  });
  
  return new Table({
    columnWidths: [2800, 4000, 1280, 1280],
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    rows
  });
}

// Document content
const children = [];

// Cover page
children.push(
  new Paragraph({ spacing: { before: 4000 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "RICCO ERP", size: 72, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200 },
    children: [new TextRun({ text: "Catálogo Completo de Aplicaciones", size: 40, color: colors.secondary })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100 },
    children: [new TextRun({ text: "Frappe/ERPNext Ecosystem Analysis", size: 28, color: colors.accent })]
  }),
  new Paragraph({ spacing: { before: 2000 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: `Total Apps Analizadas: ${catalog.metadata.total_apps_analyzed}`, size: 24, color: colors.body })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80 },
    children: [new TextRun({ text: `Apps a Incluir: ${catalog.metadata.apps_to_include}`, size: 24, color: colors.body })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80 },
    children: [new TextRun({ text: `Apps Fusionadas: ${catalog.metadata.apps_fusioned}`, size: 24, color: colors.body })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80 },
    children: [new TextRun({ text: `Apps Excluidas: ${catalog.metadata.apps_excluded}`, size: 24, color: colors.body })]
  }),
  new Paragraph({ spacing: { before: 1500 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: `Fecha: ${catalog.metadata.generated_date}`, size: 20, color: colors.secondary })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80 },
    children: [new TextRun({ text: `Versión: ${catalog.metadata.version}`, size: 20, color: colors.secondary })]
  }),
  new Paragraph({ children: [new PageBreak()] })
);

// TOC
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "Tabla de Contenidos", size: 32, bold: true, color: colors.primary })]
  }),
  new TableOfContents("Tabla de Contenidos", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200 },
    children: [new TextRun({ text: "Nota: Esta Tabla de Contenidos se genera mediante códigos de campo. Para asegurar la precisión de los números de página, haga clic derecho en la TOC y seleccione \"Actualizar Campo\".", size: 18, color: "999999", italics: true })]
  }),
  new Paragraph({ children: [new PageBreak()] })
);

// 1. Executive Summary
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "1. Resumen Ejecutivo", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Este documento presenta el análisis exhaustivo del ecosistema Frappe/ERPNext para la implementación de RICCO ERP. Se han analizado 303 aplicaciones del Frappe Cloud Marketplace, identificando conflictos, oportunidades de fusión, y estableciendo un catálogo definitivo de aplicaciones a instalar.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: "El análisis ha resultado en la creación de 6 aplicaciones RICCO fusionadas que resuelven conflictos técnicos y funcionales, además de identificar 185 aplicaciones listas para instalación sin modificaciones.", size: 22, color: colors.body })]
  })
);

// Summary table
const summaryTable = new Table({
  columnWidths: [4680, 4680],
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  rows: [
    new TableRow({
      tableHeader: true,
      children: [createHeaderCell("Métrica", 4680), createHeaderCell("Valor", 4680)]
    }),
    new TableRow({ children: [createDataCell("Total Apps Analizadas", 4680), createDataCell("303", 4680, true)] }),
    new TableRow({ children: [createDataCell("Apps a Incluir", 4680), createDataCell("185", 4680, true)] }),
    new TableRow({ children: [createDataCell("Apps Fusionadas (RICCO)", 4680), createDataCell("6", 4680, true)] }),
    new TableRow({ children: [createDataCell("Apps Excluidas", 4680), createDataCell("112", 4680, true)] }),
    new TableRow({ children: [createDataCell("Categorías Analizadas", 4680), createDataCell("25", 4680, true)] })
  ]
});
children.push(summaryTable);
children.push(new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 1: Resumen estadístico del análisis", size: 18, color: colors.secondary, italics: true })] }));

// 2. Apps Fusionadas
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "2. Aplicaciones Fusionadas (RICCO Branded)", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las siguientes aplicaciones han sido creadas mediante la fusión de múltiples apps con funcionalidades superpuestas, eliminando conflictos técnicos y proporcionando una solución unificada y mejorada.", size: 22, color: colors.body })]
  })
);

catalog.fusioned_apps.forEach((app, index) => {
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 300 },
      children: [new TextRun({ text: `2.${index + 1} ${app.name}`, size: 26, bold: true, color: colors.primary })]
    }),
    new Paragraph({
      spacing: { before: 100 },
      children: [
        new TextRun({ text: "ID de Fusión: ", size: 22, bold: true, color: colors.body }),
        new TextRun({ text: app.fusion_id, size: 22, color: colors.body })
      ]
    }),
    new Paragraph({
      spacing: { before: 80 },
      children: [
        new TextRun({ text: "Descripción: ", size: 22, bold: true, color: colors.body }),
        new TextRun({ text: app.description, size: 22, color: colors.body })
      ]
    }),
    new Paragraph({
      spacing: { before: 80 },
      children: [
        new TextRun({ text: "Apps Fusionadas: ", size: 22, bold: true, color: colors.body }),
        new TextRun({ text: app.source_apps.join(", "), size: 22, color: colors.body })
      ]
    }),
    new Paragraph({
      spacing: { before: 80 },
      children: [
        new TextRun({ text: "Características: ", size: 22, bold: true, color: colors.body }),
        new TextRun({ text: app.features.join(", "), size: 22, color: colors.body })
      ]
    }),
    new Paragraph({
      spacing: { before: 80 },
      children: [
        new TextRun({ text: "Repositorio: ", size: 22, bold: true, color: colors.body }),
        new TextRun({ text: app.repository, size: 22, color: colors.accent })
      ]
    })
  );
});

// 3. Apps Core
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "3. Aplicaciones Core", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las aplicaciones core son fundamentales para el funcionamiento de RICCO ERP. Estas aplicaciones proporcionan la infraestructura base sobre la cual se construyen todas las demás funcionalidades del sistema.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.core),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 2: Aplicaciones Core de RICCO ERP", size: 18, color: colors.secondary, italics: true })] })
);

// 4. Apps de Localización
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "4. Aplicaciones de Localización", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las aplicaciones de localización garantizan el cumplimiento de regulaciones fiscales y legales específicas de cada región geográfica. RICCO ERP soporta múltiples jurisdicciones con apps especializadas.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.localization),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 3: Aplicaciones de Localización por Región", size: 18, color: colors.secondary, italics: true })] })
);

// 5. Apps de Integración
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "5. Aplicaciones de Integración", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Estas aplicaciones permiten la conexión de RICCO ERP con plataformas externas, marketplaces, y servicios de terceros, extendiendo las capacidades del sistema más allá de sus funcionalidades nativas.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.integration),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 4: Aplicaciones de Integración", size: 18, color: colors.secondary, italics: true })] })
);

// 6. Apps de Industria
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "6. Soluciones Verticales por Industria", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "RICCO ERP ofrece soluciones especializadas para diferentes sectores industriales. Estas aplicaciones verticales proporcionan funcionalidades específicas adaptadas a las necesidades de cada industria.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.industry),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 5: Soluciones Verticales por Industria", size: 18, color: colors.secondary, italics: true })] })
);

// 7. Apps de Productividad
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "7. Aplicaciones de Productividad", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las aplicaciones de productividad mejoran la eficiencia operativa del equipo, proporcionando herramientas para gestión de tareas, planificación, comunicación interna y automatización de procesos.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.productivity),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 6: Aplicaciones de Productividad", size: 18, color: colors.secondary, italics: true })] })
);

// 8. Apps de Analytics
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "8. Aplicaciones de Analytics e Inteligencia de Negocios", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Estas aplicaciones proporcionan capacidades de análisis de datos, visualización, reporting y business intelligence para la toma de decisiones informadas.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.analytics),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 7: Aplicaciones de Analytics", size: 18, color: colors.secondary, italics: true })] })
);

// 9. Apps de Comunicación
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "9. Aplicaciones de Comunicación", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las aplicaciones de comunicación facilitan la interacción con clientes, proveedores y equipo interno a través de múltiples canales incluyendo SMS, email, fax y plataformas de mensajería.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.communication),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 8: Aplicaciones de Comunicación", size: 18, color: colors.secondary, italics: true })] })
);

// 10. Apps de HR
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "10. Extensiones de Recursos Humanos", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Estas aplicaciones extienden las funcionalidades del módulo core de HRMS, proporcionando capacidades adicionales para gestión de asistencia, nómina especializada, integración biométrica y más.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.hr),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 9: Extensiones de Recursos Humanos", size: 18, color: colors.secondary, italics: true })] })
);

// 11. Apps de Inventario
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "11. Aplicaciones de Inventario y Logística", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las aplicaciones de inventario y logística proporcionan herramientas avanzadas para gestión de almacenes, envíos, tracking de paquetes y control de movimiento de materiales.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.inventory),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 10: Aplicaciones de Inventario y Logística", size: 18, color: colors.secondary, italics: true })] })
);

// 12. Apps de Utilidades
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "12. Utilidades y Herramientas", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las utilidades proporcionan funcionalidades complementarias que mejoran la experiencia del usuario y extienden las capacidades técnicas del sistema.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.utilities),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 11: Utilidades y Herramientas", size: 18, color: colors.secondary, italics: true })] })
);

// 13. Apps de Finanzas
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "13. Extensiones Financieras", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "Las extensiones financieras proporcionan capacidades avanzadas para gestión bancaria, conciliación, tesorería, pagos internacionales y cumplimiento fiscal.", size: 22, color: colors.body })]
  }),
  createAppTable(catalog.apps_to_install.finance_extended),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 12: Extensiones Financieras", size: 18, color: colors.secondary, italics: true })] })
);

// 14. Cobertura Regional
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "14. Cobertura Regional", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "RICCO ERP soporta múltiples regiones geográficas con aplicaciones de localización específicas. La siguiente tabla muestra la cobertura por país/región.", size: 22, color: colors.body })]
  })
);

const regionRows = [
  new TableRow({
    tableHeader: true,
    children: [createHeaderCell("Región", 3120), createHeaderCell("Apps Disponibles", 6240)]
  })
];

Object.entries(catalog.apps_by_region).forEach(([region, apps]) => {
  regionRows.push(new TableRow({
    children: [
      createDataCell(region, 3120),
      createDataCell(apps.join(", "), 6240)
    ]
  }));
});

const regionTable = new Table({
  columnWidths: [3120, 6240],
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  rows: regionRows
});
children.push(regionTable);
children.push(new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 13: Cobertura Regional de Localización", size: 18, color: colors.secondary, italics: true })] }));

// 15. Prioridades de Instalación
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "15. Prioridades de Instalación", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "La implementación de RICCO ERP se divide en tres fases según la criticidad de cada aplicación. Esta estrategia garantiza una implementación ordenada y minimiza riesgos.", size: 22, color: colors.body })]
  })
);

// Phase 1
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300 },
    children: [new TextRun({ text: "15.1 Fase 1 - CRÍTICA", size: 26, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({ text: "Aplicaciones esenciales que deben instalarse primero. Sin estas, el sistema no puede funcionar.", size: 22, color: colors.body })]
  })
);

const phase1Rows = [
  new TableRow({
    tableHeader: true,
    children: [createHeaderCell("App", 3120), createHeaderCell("Razón", 6240)]
  })
];

catalog.installation_priority.phase1_critical.forEach(item => {
  phase1Rows.push(new TableRow({
    children: [
      createDataCell(item.app, 3120),
      createDataCell(item.reason, 6240)
    ]
  }));
});

children.push(new Table({ columnWidths: [3120, 6240], margins: { top: 80, bottom: 80, left: 120, right: 120 }, rows: phase1Rows }));
children.push(new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 14: Fase 1 - Aplicaciones Críticas", size: 18, color: colors.secondary, italics: true })] }));

// Phase 2
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300 },
    children: [new TextRun({ text: "15.2 Fase 2 - IMPORTANTE", size: 26, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({ text: "Aplicaciones que amplían significativamente las capacidades del sistema. Se recomienda instalar después de la Fase 1.", size: 22, color: colors.body })]
  })
);

const phase2Rows = [
  new TableRow({
    tableHeader: true,
    children: [createHeaderCell("App", 3120), createHeaderCell("Razón", 6240)]
  })
];

catalog.installation_priority.phase2_important.forEach(item => {
  phase2Rows.push(new TableRow({
    children: [
      createDataCell(item.app, 3120),
      createDataCell(item.reason, 6240)
    ]
  }));
});

children.push(new Table({ columnWidths: [3120, 6240], margins: { top: 80, bottom: 80, left: 120, right: 120 }, rows: phase2Rows }));
children.push(new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 15: Fase 2 - Aplicaciones Importantes", size: 18, color: colors.secondary, italics: true })] }));

// Phase 3
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300 },
    children: [new TextRun({ text: "15.3 Fase 3 - OPCIONAL", size: 26, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({ text: "Aplicaciones especializadas y de nicho. Instalar según necesidades específicas del negocio.", size: 22, color: colors.body })]
  })
);

const phase3Rows = [
  new TableRow({
    tableHeader: true,
    children: [createHeaderCell("App", 3120), createHeaderCell("Razón", 6240)]
  })
];

catalog.installation_priority.phase3_optional.forEach(item => {
  phase3Rows.push(new TableRow({
    children: [
      createDataCell(item.app, 3120),
      createDataCell(item.reason, 6240)
    ]
  }));
});

children.push(new Table({ columnWidths: [3120, 6240], margins: { top: 80, bottom: 80, left: 120, right: 120 }, rows: phase3Rows }));
children.push(new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tabla 16: Fase 3 - Aplicaciones Opcionales", size: 18, color: colors.secondary, italics: true })] }));

// 16. Conclusiones
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400 },
    children: [new TextRun({ text: "16. Conclusiones", size: 32, bold: true, color: colors.primary })]
  }),
  new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "El análisis exhaustivo del ecosistema Frappe/ERPNext ha permitido identificar un conjunto robusto de aplicaciones para RICCO ERP. Las principales conclusiones son:", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 100 },
    children: [new TextRun({ text: "1. Se han creado 6 aplicaciones RICCO fusionadas que resuelven conflictos críticos en áreas como POS, WhatsApp, pagos y e-commerce. Estas aplicaciones proporcionan funcionalidad unificada y eliminan redundancias.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 100 },
    children: [new TextRun({ text: "2. Se identificaron 185 aplicaciones listas para instalación directa sin conflictos, cubriendo todas las áreas funcionales necesarias para un ERP empresarial completo.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 100 },
    children: [new TextRun({ text: "3. La cobertura regional incluye 15+ países/regiones con aplicaciones de localización específicas para cumplimiento fiscal y legal.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 100 },
    children: [new TextRun({ text: "4. El plan de implementación en 3 fases garantiza una implementación ordenada, empezando por las aplicaciones críticas y avanzando hacia funcionalidades especializadas.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 100 },
    children: [new TextRun({ text: "5. Las 112 aplicaciones excluidas fueron descartadas por conflictos técnicos, duplicación de funcionalidad, o baja calidad/mantenimiento.", size: 22, color: colors.body })]
  }),
  new Paragraph({
    spacing: { before: 200 },
    children: [new TextRun({ text: "RICCO ERP está posicionado para ser una solución ERP empresarial completa, aprovechando el ecosistema Frappe/ERPNext con personalizaciones estratégicas que agregan valor diferenciado.", size: 22, color: colors.body })]
  })
);

// Create document
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: colors.secondary, font: "Times New Roman" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } }
    ]
  },
  sections: [{
    properties: {
      page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ 
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "RICCO ERP - Catálogo de Aplicaciones", size: 18, color: colors.secondary })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ 
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Página ", size: 18, color: colors.secondary }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, color: colors.secondary }),
          new TextRun({ text: " de ", size: 18, color: colors.secondary }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: colors.secondary })
        ]
      })] })
    },
    children
  }]
});

// Generate file
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/z/my-project/download/RICCO-ERP-Catalogo-Apps-Final.docx', buffer);
  console.log('Document generated: /home/z/my-project/download/RICCO-ERP-Catalogo-Apps-Final.docx');
});
