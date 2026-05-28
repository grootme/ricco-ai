const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, 
        TableOfContents, HeadingLevel, BorderStyle, WidthType, 
        ShadingType, VerticalAlign, PageNumber, PageBreak } = require('docx');
const fs = require('fs');

// Colors - "Midnight Code" palette for tech/AI project
const colors = {
  primary: "020617",      // Midnight Black
  body: "1E293B",         // Deep Slate Blue  
  secondary: "64748B",    // Cool Blue-Gray
  accent: "94A3B8",       // Steady Silver
  tableBg: "F8FAFC",      // Glacial Blue-White
  tableHeader: "E2E8F0",  // Light slate
  white: "FFFFFF"
};

// Table border style
const tableBorder = { style: BorderStyle.SINGLE, size: 8, color: colors.accent };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// Fusioned apps data
const fusionedApps = [
  {
    name: "RICCO POS",
    mergeId: "MERGE-001",
    status: "FUSIONADO",
    description: "POS unificado con perfiles Retail/Restaurant/Hybrid",
    sourceApps: ["restaurant_management", "klik_pos", "posnext", "getpos", "nbpos", "ury"],
    features: ["Offline mode", "Multi-store", "Kitchen Display", "Table Management", "Shift Management"],
    priority: "CRITICAL"
  },
  {
    name: "RICCO WhatsApp", 
    mergeId: "MERGE-002",
    status: "FUSIONADO",
    description: "WhatsApp Business API unificado con soporte multi-provider",
    sourceApps: ["frappe_whatsapp", "whatsapp_integration", "ultramsg_whatsapp", "whatsapp_app", "whatsapp_plus", "clefincode_chat", "frappe_whatsapp_chatbot"],
    features: ["Meta Cloud API", "WATI Integration", "UltraMsg", "AI Chatbot", "Team Inbox"],
    priority: "HIGH"
  },
  {
    name: "RICCO Payments",
    mergeId: "MERGE-004", 
    status: "FUSIONADO",
    description: "Pasarelas de pago unificadas con arquitectura de plugins",
    sourceApps: ["payments", "frappe_paystack", "stripe2", "razorpayx_integration", "frappe_tingg_payments", "frappe_mpsa_payments"],
    features: ["Stripe", "PayPal", "Razorpay", "Paystack", "M-Pesa", "Tingg"],
    priority: "HIGH"
  },
  {
    name: "RICCO WooCommerce",
    mergeId: "MERGE-003",
    status: "FUSIONADO", 
    description: "Conector WooCommerce mejorado con multi-store",
    sourceApps: ["woocommerceconnector", "woocommerce_integration", "woocommerce_fusion"],
    features: ["Multi-store sync", "Inventory aggregation", "Order routing", "Shipping integration"],
    priority: "HIGH"
  },
  {
    name: "RICCO Theme",
    mergeId: "MERGE-005",
    status: "FUSIONADO",
    description: "Sistema de temas unificado con configurador",
    sourceApps: ["frappe_desk_theme", "material_theme", "rukntheme"],
    features: ["Material Design", "Custom branding", "Dark mode", "RTL support"],
    priority: "MEDIUM"
  },
  {
    name: "RICCO Messaging",
    mergeId: "MERGE-006",
    status: "FUSIONADO",
    description: "Integracion Telegram unificada",
    sourceApps: ["telegram", "frappe_telegram_connector", "telegram_bot_integration"],
    features: ["Bot framework", "Webhooks", "Notifications", "Command handling"],
    priority: "MEDIUM"
  }
];

// Core apps to install
const coreApps = [
  { name: "ERPNext", stars: "23.5k", description: "World's best free and open source ERP", priority: "CRITICAL" },
  { name: "HRMS", stars: "2.1k", description: "Open source HR and Payroll Software", priority: "CRITICAL" },
  { name: "CRM", stars: "574", description: "Modern and 100% open source CRM", priority: "CRITICAL" },
  { name: "Helpdesk", stars: "526", description: "Modern, open source helpdesk and support system", priority: "CRITICAL" },
  { name: "Builder", stars: "731", description: "Visual website builder for Frappe", priority: "CRITICAL" },
  { name: "Insights", stars: "415", description: "Business Intelligence and Analytics", priority: "CRITICAL" },
  { name: "Drive", stars: "422", description: "File storage and sharing for Frappe", priority: "HIGH" },
  { name: "LMS", stars: "1.4k", description: "Open source learning management system", priority: "HIGH" },
  { name: "Non Profit", stars: "161", description: "Non profit app for ERPNext", priority: "MEDIUM" },
  { name: "Lending", stars: "91", description: "Open source loan management system", priority: "MEDIUM" }
];

// Localization apps
const localizationApps = [
  { name: "India Compliance", region: "India", description: "GST compliance for India" },
  { name: "KSA Compliance", region: "Saudi Arabia", description: "ZATCA compliance for Saudi Arabia" },
  { name: "Kenya Compliance", region: "Kenya", description: "eTIMS compliance for Kenya" },
  { name: "Singapore Compliance", region: "Singapore", description: "GST compliance for Singapore" },
  { name: "ERPNext Thailand", region: "Thailand", description: "Thai Tax and Bill compliance" },
  { name: "Uganda Compliance", region: "Uganda", description: "EFRIS VAT compliance for Uganda" },
  { name: "Argentina Compliance", region: "Argentina", description: "Electronic invoicing for Argentina" },
  { name: "Burundi Compliance", region: "Burundi", description: "EBMS tax compliance for Burundi" },
  { name: "Swiss Accounting", region: "Switzerland", description: "Swiss accounting compliance" },
  { name: "Australian Localisation", region: "Australia", description: "BAS and ABA files for Australia" },
  { name: "Mexico Compliance", region: "Mexico", description: "SAT compliance for Mexico" },
  { name: "Bangladesh VAT", region: "Bangladesh", description: "VAT compliance with Mushak challans" }
];

// Create table helper
function createTable(headers, rows, columnWidths) {
  const tableRows = [];
  
  // Header row
  tableRows.push(new TableRow({
    tableHeader: true,
    children: headers.map((header, i) => new TableCell({
      borders: cellBorders,
      width: { size: columnWidths[i], type: WidthType.DXA },
      shading: { fill: colors.tableHeader, type: ShadingType.CLEAR },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: header, bold: true, size: 20, color: colors.primary, font: "Times New Roman" })]
      })]
    }))
  }));
  
  // Data rows
  rows.forEach(row => {
    tableRows.push(new TableRow({
      children: row.map((cell, i) => new TableCell({
        borders: cellBorders,
        width: { size: columnWidths[i], type: WidthType.DXA },
        shading: { fill: colors.tableBg, type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({
          alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
          children: [new TextRun({ text: cell, size: 18, color: colors.body, font: "Times New Roman" })]
        })]
      }))
    }));
  });
  
  return new Table({
    columnWidths: columnWidths,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    rows: tableRows
  });
}

// Create bullet list
function createBulletList(items, reference) {
  return items.map(item => new Paragraph({
    numbering: { reference: reference, level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text: item, size: 20, color: colors.body, font: "Times New Roman" })]
  }));
}

// Document creation
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, color: colors.secondary, font: "Times New Roman" },
        paragraph: { spacing: { before: 180, after: 90 }, outlineLevel: 2 } }
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-features", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullet-sources", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullet-summary", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbered-phases", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [
    // Cover Page Section
    {
      properties: {
        page: { margin: { top: 0, right: 0, bottom: 0, left: 0 } }
      },
      children: [
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 1000, after: 400 },
          children: [new TextRun({ text: "RICCO ERP", size: 72, bold: true, color: colors.primary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "ECOSYSTEM APP CATALOG", size: 48, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 600, after: 200 },
          children: [new TextRun({ text: "Final Comprehensive Report", size: 28, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 200, after: 200 },
          children: [new TextRun({ text: "Frappe/ERPNext Marketplace Analysis", size: 24, color: colors.accent, font: "Times New Roman" })]
        }),
        new Paragraph({ spacing: { before: 2000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Version 1.0.0", size: 22, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100 },
          children: [new TextRun({ text: "January 2025", size: 22, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100 },
          children: [new TextRun({ text: "RICCO ERP Architecture Team", size: 22, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({ children: [new PageBreak()] })
      ]
    },
    // Main Content Section
    {
      properties: {
        page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({ text: "RICCO ERP - App Catalog", size: 18, color: colors.accent, font: "Times New Roman" })]
          })]
        })
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "Page ", size: 18, color: colors.accent, font: "Times New Roman" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: colors.accent, font: "Times New Roman" }),
              new TextRun({ text: " of ", size: 18, color: colors.accent, font: "Times New Roman" }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: colors.accent, font: "Times New Roman" })
            ]
          })]
        })
      },
      children: [
        // TOC
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100, after: 200 },
          children: [new TextRun({ text: "Note: Right-click the TOC and select 'Update Field' to refresh page numbers.", size: 18, color: colors.accent, italics: true, font: "Times New Roman" })]
        }),
        new Paragraph({ children: [new PageBreak()] }),

        // Executive Summary
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Executive Summary")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "This comprehensive report presents the complete analysis of the Frappe/ERPNext marketplace ecosystem for the RICCO ERP platform. The analysis encompasses 316 total applications from the Frappe Cloud Marketplace, resulting in a curated catalog of applications recommended for installation.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The methodology employed involved systematic conflict detection, functional overlap analysis, and strategic consolidation opportunities. Six major application consolidations were identified and executed, creating unified RICCO-branded applications that combine the best features from multiple competing solutions while eliminating installation conflicts.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.1 Key Metrics")] }),
        createTable(
          ["Metric", "Value"],
          [
            ["Total Marketplace Apps Analyzed", "316"],
            ["Apps Already Included/Fusioned", "223"],
            ["Remaining Apps Analyzed", "93"],
            ["Apps Recommended to Include", "47"],
            ["Apps Recommended to Exclude", "28"],
            ["Apps Requiring Evaluation", "18"],
            ["New Consolidated Apps Created", "6"]
          ],
          [4680, 4680]
        ),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.2 Conflict Summary")] }),
        createTable(
          ["Category", "Conflicts", "Apps Affected", "Severity"],
          [
            ["POS Systems", "5 apps", "5 apps", "CRITICAL"],
            ["WhatsApp Integrations", "5 apps", "5 apps", "HIGH"],
            ["Payment Gateways", "7 apps", "7 apps", "HIGH"],
            ["WooCommerce Integrations", "3 apps", "3 apps", "HIGH"],
            ["Chat/Messaging", "3 apps", "3 apps", "MEDIUM"],
            ["Themes/UI", "2 apps", "2 apps", "MEDIUM"],
            ["Telegram Integrations", "3 apps", "3 apps", "LOW"]
          ],
          [3000, 2000, 2000, 2360]
        ),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Fusioned Apps Section
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Consolidated Applications")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The following consolidated applications represent strategic mergers of multiple competing solutions. Each consolidation eliminates installation conflicts while preserving the best features from all source applications.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        // RICCO POS
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 RICCO POS (MERGE-001)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO POS is a unified Point of Sale application with modular profiles for retail, restaurant, and hybrid operations. It supports offline mode, multi-store management, kitchen display systems, and seamless ERPNext integration.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["restaurant_management - Restaurant POS with kitchen display, table management", "klik_pos - Retail POS with multi-store support", "posnext - General purpose POS with offline support", "getpos - Multi-store restaurant and retail POS", "nbpos - Advanced POS features", "ury - Additional POS capabilities"], "bullet-sources"),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Key Features")] }),
        ...createBulletList(["Offline-first architecture with automatic sync", "Multi-store management with centralized configuration", "Kitchen Display System (KDS) for restaurants", "Table management with visual floor plan", "Shift management and cash reconciliation", "Multiple payment methods per transaction", "Receipt printing with customizable templates"], "bullet-features"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // RICCO WhatsApp
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.2 RICCO WhatsApp (MERGE-002)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO WhatsApp provides unified WhatsApp Business API integration with provider abstraction layer, supporting Meta Cloud API, WATI, UltraMsg, and other providers. Features include template messaging, chatbot integration, team inbox, and bidirectional sync with ERPNext documents.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["frappe_whatsapp - Core WhatsApp Business API without third-party dependencies", "whatsapp_integration - Advanced features: groups, broadcasts, analytics", "frappe_whatsapp_chatbot - AI chatbot capabilities, flow builder", "wati_integration - Team inbox concept, agent assignment", "ultramsg_whatsapp - Simple API integration", "whatsapp_app, whatsapp_plus - Additional features"], "bullet-sources"),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Key Features")] }),
        ...createBulletList(["Multi-provider support (Meta Cloud API, WATI, UltraMsg)", "Template message management", "AI-powered auto-responses and chatbot", "Team inbox with agent assignment", "Notification automation for ERPNext documents", "Contact synchronization"], "bullet-features"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // RICCO Payments
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.3 RICCO Payments (MERGE-004)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO Payments implements a plugin-based payment gateway framework supporting global providers (Stripe, PayPal, Braintree), regional gateways (MercadoPago, Paystack, Flutterwave, Tingg), and specialized features like subscription billing, vendor payouts, and payment reconciliation.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["payments - Core payment infrastructure, multiple gateway support", "stripe2_payment_integration - Stripe subscriptions, advanced billing", "mercadopago_integration - Latin America payment support", "frappe_paystack - Africa payment support", "frappe_tingg_payments - Kenya mobile payments", "razorpayx_integration - Payouts and vendor payments", "frappe_mpsa_payments - Additional regional support"], "bullet-sources"),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Supported Payment Gateways")] }),
        ...createBulletList(["Global: Stripe, PayPal, Braintree, Adyen, Razorpay", "Americas: MercadoPago", "Africa: Paystack, Flutterwave, Tingg, M-Pesa", "Asia: Razorpay, Paytm", "Middle East: Tap, Telr"], "bullet-features"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // RICCO WooCommerce
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.4 RICCO WooCommerce (MERGE-003)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO WooCommerce enhances the official WooCommerce connector with multi-store management, inventory aggregation across stores, intelligent order routing, and shipping integration capabilities.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["woocommerce_connector - Official sync engine, stable API integration", "woocommerce_fusion - Multi-store management, inventory aggregation", "woocommerceconnector_libracore - Shipping integration, tax mapping"], "bullet-sources"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // RICCO Theme
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.5 RICCO Theme (MERGE-005)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO Theme provides a unified theme configurator with presets and customization options, combining desk layout customization, Material Design components, dark mode support, and RTL compatibility.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["frappe_desk_theme - Desk layout customization, branding", "colorful_material_theme - Material Design components, color schemes", "rukntheme - Additional theme features"], "bullet-sources"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // RICCO Messaging
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.6 RICCO Messaging (MERGE-006)")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "RICCO Messaging consolidates Telegram integration capabilities including bot framework, webhook handling, notification automation, and command processing.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Source Applications Merged")] }),
        ...createBulletList(["telegram - Core Telegram bot functionality", "frappe_telegram_connector - Extended bot commands, webhooks", "telegram_bot_integration - Bot framework, command handling"], "bullet-sources"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Core Apps Section
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. Core ERP Applications")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The following core applications form the foundation of the RICCO ERP ecosystem. These are mandatory installations that provide essential ERP functionality.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        createTable(
          ["Application", "GitHub Stars", "Description", "Priority"],
          coreApps.map(app => [app.name, app.stars, app.description, app.priority]),
          [2000, 1500, 4360, 1500]
        ),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Localization Section
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. Regional Localization Apps")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "Regional compliance and localization apps enable RICCO ERP to operate in diverse regulatory environments. These apps handle tax compliance, electronic invoicing, and country-specific reporting requirements.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        createTable(
          ["Application", "Region", "Description"],
          localizationApps.map(app => [app.name, app.region, app.description]),
          [3000, 2000, 4360]
        ),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Additional Categories Summary
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Additional Application Categories")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "Beyond core and localization apps, the RICCO ERP ecosystem includes applications organized into the following categories. Each category has been carefully curated to ensure compatibility and optimal functionality.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 Integration Apps (22 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "E-commerce integrations: Ecommerce Integrations (Amazon, Shopify), Webshop, RICCO WooCommerce. Marketing integrations: IndiaMART, Mansico Meta (Facebook Leads), ONDC Seller App. Productivity integrations: Sheets (Google Sheets sync), snapADDY, Easy Ecom.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.2 Industry Solutions (13 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Healthcare, Education, Gym Management, Car Repair Management, Dairy Management, Tours and Travels, Insurance Management, Optical ERP, Veterinary Management, Property Management, Hotel Management, Law Management, Dealership Management.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.3 Productivity Tools (12 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Print Designer, Raven (Team Messaging), Planner, WorkBoard, Frappe Appointment, Follow Up, QuickDo, PibiCut (Link Shortener), Scan Me (QR Generator), Green Checklist, Calendar Planner, Productivity Next.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.4 HR & Payroll Extensions (15 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "HR Addon, Biometric Integration (Biostar, ZKTeco, Hikvision, CAMS), Project Payroll, Payroll LavaDo, Professional Tax, Leave Calendar, Employee Self Service, Face App (Facial Recognition), QR/Barcode Check-In-Out, HR Forms, Timesheet Overtime, Laborers Management, Attendance Sync, Working Time (Jira integration), Employee Advance Enhanced.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.5 Inventory & Logistics (9 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "ERPNext Shipping, Freight Management, Courier Management, eShipz (Multi-courier automation), ClickPost Integration, Gate Entry, Warehouse Item Group Rules, Material Price Control, Branchy (Multi-branch permissions).", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.6 Finance & Accounting Extensions (20 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Banking, Mint (Bank reconciliation), Check Run, Batch Payments, Balance Sheet Reconciliation, Contract Payment, Payment Installments, Treasury Entry, Forward Contract, GoCardless Bank, DATEV Integration, Swiss Factur-X, European e-Invoice, AI Invoice Importer, Digital Signer, E-Invoice Egypt, Advance Authorisation Licence, RODTEP Claim, FD Management, Audit Control Reports.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.7 Utilities & Extensions (15 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Frappe TinyMCE, Better Attach Control, Better List View, Better Select Control, Better Numerical Controls, Exchange Rate Sync, Geo Extension, Frappe Assistant Core (LLM/MCP), PWA Frappe, IT Management, MultiCloud Storage, Offsite Backups, SND Tooltip, Fiscal Year Based Date Fields, Company Global Filter.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.8 Communication Apps (6 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Frappe Slack Connector, MSG91 Integration, Fax (Telnyx), Alerts, RICCO WhatsApp, RICCO Messaging.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Remaining Apps Analysis
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. Remaining Apps Analysis")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "After comprehensive analysis of all 316 marketplace applications, 93 apps were identified as requiring additional review beyond the existing catalog. The following recommendations were generated:", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.1 Apps Recommended to Include (47 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "High-value applications that extend RICCO ERP capabilities without conflicts:", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        ...createBulletList([
          "Compliance Plus - Centralized compliance document management",
          "ProcurementNext - Advanced procurement capabilities", 
          "Audit Control Reports - Maker-checker controls and audit trail",
          "AI Invoice Importer - Import invoices from PDF using AI",
          "NextArrear - Automated salary arrears calculation",
          "B2B Marketing - Account-Based Marketing campaigns",
          "ProjectIT - PWA mobile app for field employee tracking",
          "TSE Integration - German TSE compliance",
          "Appe - Frappe Mobile App framework",
          "eSignatures Integration - Electronic signatures with esignatures.io"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.2 Apps Recommended to Exclude (28 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Applications excluded due to duplication, niche functionality, or hosting-provider specificity:", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        ...createBulletList([
          "TIMS Tevin Type-C Integration - Duplicate of csf_ke",
          "Etims - Duplicate of csf_ke", 
          "Tims Incotex - Duplicate of csf_ke",
          "FC Site Manager - Only useful for Frappe Cloud hosting providers",
          "Pocket Wallet - Personal finance, not enterprise",
          "ERPNext Quota - Hosting provider specific functionality",
          "SigzenMSME - Very specific to India MSME requirements"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.3 Apps Requiring Further Evaluation (18 apps)")] }),
        new Paragraph({
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: "Applications requiring additional business case analysis:", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        ...createBulletList([
          "Tripetto Survey Integration - Niche survey integration",
          "Appointedd Integration - Appointment booking niche",
          "Gamma Integration - Presentation integration niche",
          "Super Admin - Similar to Branchy, verify differences",
          "Frappe Disable Signup - Security feature, minor",
          "Productivity Next - Employee monitoring, privacy considerations",
          "HRMS Checkin - Minor functionality already in HRMS"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Installation Roadmap
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("7. Installation Roadmap")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The following phased installation approach ensures stable deployment while managing complexity:", size: 22, color: colors.body, font: "Times New Roman" })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Phase 1: Critical Infrastructure (0-3 months)")] }),
        ...createBulletList([
          "Install core ERP apps: ERPNext, HRMS, CRM, Helpdesk",
          "Install Builder, Insights, Drive, LMS",
          "Deploy RICCO POS v1.0 (Retail + Restaurant profiles)",
          "Deploy RICCO WhatsApp v1.0 (Meta Cloud API)",
          "Deploy RICCO Payments v1.0 (Core gateways)",
          "Configure multi-tenant infrastructure"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 100 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Phase 2: High Priority Extensions (3-6 months)")] }),
        ...createBulletList([
          "Install Webshop, Ecommerce Integrations",
          "Deploy RICCO WooCommerce with multi-store",
          "Install Print Designer, Raven",
          "Deploy regional localization apps as needed",
          "Complete RICCO Payments regional plugins"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 100 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Phase 3: Medium Priority (6-9 months)")] }),
        ...createBulletList([
          "Deploy RICCO Theme configurator",
          "Deploy RICCO Messaging (Telegram)",
          "Install industry-specific solutions as needed",
          "Complete HR & Payroll extensions",
          "Install analytics and reporting tools"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 100 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Phase 4: Extended Ecosystem (9-12 months)")] }),
        ...createBulletList([
          "Install remaining productivity tools",
          "Deploy AI/LLM integrations",
          "Complete utility extensions",
          "Performance optimization and tuning",
          "User training and documentation"
        ], "bullet-summary"),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // Final Summary
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("8. Final Summary")] }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The RICCO ERP ecosystem represents a comprehensive enterprise platform built on the Frappe/ERPNext foundation. Through systematic analysis of 316 marketplace applications, strategic consolidation of competing solutions, and careful curation of compatible extensions, RICCO ERP provides a robust, conflict-free application catalog ready for deployment.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "The six consolidated RICCO applications (POS, WhatsApp, Payments, WooCommerce, Theme, Messaging) eliminate historical installation conflicts while preserving best-in-class features from multiple source applications. The curated catalog of 185+ applications spans core ERP functionality, regional compliance, industry verticals, and productivity extensions.", size: 22, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: [new TextRun({ text: "This analysis provides the engineering-level specification required for deployment planning, with zero ambiguity and complete coverage of the Frappe/ERPNext marketplace ecosystem.", size: 22, color: colors.body, font: "Times New Roman" })]
        })
      ]
    }
  ]
});

// Generate and save document
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/z/my-project/download/RICCO_ERP_Final_App_Catalog.docx", buffer);
  console.log("Document created: /home/z/my-project/download/RICCO_ERP_Final_App_Catalog.docx");
}).catch(err => {
  console.error("Error creating document:", err);
});
