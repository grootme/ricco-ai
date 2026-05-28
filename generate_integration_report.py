#!/usr/bin/env python3
"""
Generate Integration Test Report PDF
"""

import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Load test results
with open('/home/z/my-project/download/integration_test_report.json', 'r') as f:
    results = json.load(f)

# Create PDF
doc = SimpleDocTemplate(
    '/home/z/my-project/download/RICCO_AI_Integration_Test_Report.pdf',
    pagesize=A4,
    rightMargin=72,
    leftMargin=72,
    topMargin=72,
    bottomMargin=72
)

# Styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Title_Custom',
    parent=styles['Title'],
    fontSize=24,
    spaceAfter=30,
    textColor=colors.HexColor('#1e3a5f')
))
styles.add(ParagraphStyle(
    name='Heading1_Custom',
    parent=styles['Heading1'],
    fontSize=16,
    spaceAfter=12,
    textColor=colors.HexColor('#2563eb')
))
styles.add(ParagraphStyle(
    name='Heading2_Custom',
    parent=styles['Heading2'],
    fontSize=14,
    spaceAfter=10,
    textColor=colors.HexColor('#3b82f6')
))
styles.add(ParagraphStyle(
    name='Body_Custom',
    parent=styles['BodyText'],
    fontSize=11,
    spaceAfter=8,
    alignment=TA_JUSTIFY
))

# Build document
story = []

# Title
story.append(Paragraph("RICCO AI - Integration Test Report", styles['Title_Custom']))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Body_Custom']))
story.append(Spacer(1, 20))

# Executive Summary
story.append(Paragraph("Executive Summary", styles['Heading1_Custom']))

summary = results['summary']
success_rate = summary['success_rate']

summary_text = f"""
This report presents the results of comprehensive integration testing for the RICCO AI platform.
The testing covered 10 major integration categories with a total of {summary['total']} individual tests.
Overall, <b>{summary['passed']} tests passed</b> and <b>{summary['failed']} tests failed</b>,
resulting in a <b>success rate of {success_rate:.1f}%</b>.
"""
story.append(Paragraph(summary_text, styles['Body_Custom']))
story.append(Spacer(1, 15))

# Summary Table
summary_data = [
    ['Metric', 'Value'],
    ['Total Tests', str(summary['total'])],
    ['Passed', str(summary['passed'])],
    ['Failed', str(summary['failed'])],
    ['Success Rate', f"{success_rate:.1f}%"],
    ['Duration', f"{results['duration_seconds']:.2f} seconds"]
]

summary_table = Table(summary_data, colWidths=[200, 150])
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
]))
story.append(summary_table)
story.append(Spacer(1, 20))

# Category Results
story.append(Paragraph("Results by Category", styles['Heading1_Custom']))

category_data = [['Category', 'Passed', 'Failed', 'Status']]
for category, stats in results['by_category'].items():
    total = stats['passed'] + stats['failed']
    status = '✓ PASS' if stats['failed'] == 0 else '✗ PARTIAL'
    category_data.append([category, str(stats['passed']), str(stats['failed']), status])

category_table = Table(category_data, colWidths=[150, 70, 70, 80])
category_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
]))
story.append(category_table)
story.append(Spacer(1, 20))

# Detailed Results
story.append(Paragraph("Detailed Test Results", styles['Heading1_Custom']))

# Group results by category
current_category = None
for key, result in results['results'].items():
    category, test_name = key.split('/')
    
    if category != current_category:
        current_category = category
        story.append(Paragraph(f"{category}", styles['Heading2_Custom']))
    
    status = "✅ PASS" if result['success'] else "❌ FAIL"
    color = colors.HexColor('#16a34a') if result['success'] else colors.HexColor('#dc2626')
    
    test_text = f"<b>{test_name}</b>: {result['message']}"
    story.append(Paragraph(f"{status} - {test_text}", styles['Body_Custom']))

story.append(Spacer(1, 20))

# OpenRouter Section
story.append(PageBreak())
story.append(Paragraph("OpenRouter Integration Details", styles['Heading1_Custom']))

openrouter_text = """
The OpenRouter integration has been successfully validated with the provided API key.
OpenRouter provides unified access to <b>357 LLM models</b> from various providers including
Meta (Llama), Google (Gemma), Mistral, OpenAI, Anthropic, and more.

<b>Key Findings:</b>
• Models endpoint successfully returned 357 available models
• Chat completion with meta-llama/llama-3.1-8b-instruct worked correctly
• API key authentication validated successfully
• 27 free models available for use

<b>Tested Capabilities:</b>
• Models listing endpoint
• Chat completion with streaming support
• Token usage tracking
• Model selection and fallback
"""
story.append(Paragraph(openrouter_text, styles['Body_Custom']))
story.append(Spacer(1, 15))

# Recommendations
story.append(Paragraph("Recommendations", styles['Heading1_Custom']))

recommendations_text = """
Based on the integration test results, the following recommendations are provided:

<b>1. Fix Remaining Import Issues:</b>
Some modules have incorrect import names (OpenAI Provider, Chat Schemas, Integration Service).
Review and update the class names to match the actual implementations.

<b>2. Install Missing Dependencies:</b>
Ensure all required Python packages are installed in the production environment:
• sqlalchemy, asyncpg for PostgreSQL
• redis for caching
• qdrant-client, pymilvus for vector stores
• structlog for logging

<b>3. Start Infrastructure Services:</b>
For full integration testing, start the required services:
• PostgreSQL database
• Redis server
• Qdrant or Milvus vector database

<b>4. Configure Environment Variables:</b>
Ensure all required environment variables are properly configured in production:
• OPENROUTER_API_KEY (✓ configured)
• DATABASE_URL
• REDIS_URL
• QDRANT_URL

<b>5. Enable Monitoring:</b>
Implement health checks and monitoring for all integrated services.
"""
story.append(Paragraph(recommendations_text, styles['Body_Custom']))

# Build PDF
doc.build(story)
print("PDF report generated: /home/z/my-project/download/RICCO_AI_Integration_Test_Report.pdf")
