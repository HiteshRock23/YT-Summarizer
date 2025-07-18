### Student-Friendly PDF Generator — Enhanced Version
# ✅ Includes emojis, better labels, section renaming, simplified language, and formula section
# Replaces professional tone with motivational, student-friendly layout

# Only key changes shown here due to length. Full version available on request.

# -- Imports and Initial Setup (unchanged) --
import os
import time
from datetime import datetime
from typing import Dict, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import re

# -- Student-Friendly PDF Generator Class --
class StudentPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.footer_text = "📚 AI Student — Learn Smarter, Not Harder 🚀"
        self.footer_color = HexColor('#0f3460')

    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle('CustomTitle', parent=self.styles['Heading1'], fontSize=24, spaceAfter=30, alignment=TA_CENTER, textColor=colors.darkblue)
        self.section_style = ParagraphStyle('CustomSection', parent=self.styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=20, textColor=colors.darkblue)
        self.body_style = ParagraphStyle('CustomBody', parent=self.styles['Normal'], fontSize=10, spaceAfter=6, alignment=TA_JUSTIFY, leftIndent=20, rightIndent=20)
        self.executive_style = ParagraphStyle('Executive', parent=self.styles['Normal'], fontSize=11, spaceAfter=8, alignment=TA_JUSTIFY, leftIndent=20, rightIndent=20, backColor=colors.lightgrey)
        self.timestamp_style = ParagraphStyle('Timestamp', parent=self.styles['Heading3'], fontSize=12, spaceAfter=8, spaceBefore=15, textColor=colors.darkred, leftIndent=20)

    def _draw_footer(self, canvas, doc):
        canvas.saveState()
        width, height = doc.pagesize
        canvas.setStrokeColor(self.footer_color)
        canvas.line(72, 40, width - 72, 40)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(self.footer_color)
        canvas.drawString(80, 28, self.footer_text)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(width - 80, 28, f"Page {doc.page}")
        canvas.restoreState()

    def _create_key_takeaways(self, summary_text: str) -> List[str]:
        lines = summary_text.split('\n')
        takeaways = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(('•', '-', '*')) or re.match(r'^\d+\.', line):
                content = line.lstrip('•-*0123456789. ').strip()
                tag = ''
                if 'charge' in content.lower():
                    tag = '[CBSE] ⚡'
                elif 'law' in content.lower():
                    tag = '[JEE+] 📐'
                takeaways.append(f"• {content} {tag}")
        return takeaways[:8] if takeaways else ["No key points found"]

    def _create_formula_section(self, formulas: List[str]) -> List:
        elements = []
        if formulas:
            elements.append(Paragraph("📐 Key Formulas", self.section_style))
            elements.append(Spacer(1, 10))
            for f in formulas:
                elements.append(Paragraph(f"• {f}", self.body_style))
                elements.append(Spacer(1, 4))
        return elements

    def _create_executive_summary(self, text: str) -> List:
        elements = []
        elements.append(Paragraph("📘 Quick Recap", self.section_style))
        elements.append(Spacer(1, 10))
        content = Paragraph(text if text else "Oops! No recap found yet. Stay tuned! 📺", self.executive_style)
        elements.append(content)
        return elements

    def _create_table_of_contents(self, timestamps: List[Dict]) -> List:
        elements = []
        elements.append(Paragraph("🗂️ What’s Covered", self.section_style))
        elements.append(Spacer(1, 15))
        for item in timestamps:
            entry = Paragraph(f"⏱ {item['time']} - {item['title']}", self.body_style)
            elements.append(entry)
            elements.append(Spacer(1, 5))
        return elements

    def _create_detailed_sections(self, timestamps: List[Dict], full_summary: str) -> List:
        elements = [Paragraph("📚 Chapter Breakdown", self.section_style), Spacer(1, 15)]
        for ts in timestamps:
            elements.append(Paragraph(f"⏱ {ts['time']} — {ts['title']}", self.timestamp_style))
            content = f"Summary notes for {ts['title']}..."  # Placeholder
            elements.append(Paragraph(content, self.body_style))
            elements.append(Spacer(1, 10))
        return elements

    def _create_metadata_section(self, meta: Dict) -> List:
        elements = [Spacer(1, 20), Paragraph("🧪 Summary Details", self.section_style)]
        meta_text = f"""
        Video: {meta['title']}\nChannel: {meta['channel']}\nDuration: {meta['duration']}\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nProcessing time: {meta['processing_time']:.2f}s
        """
        elements.append(Paragraph(meta_text, self.body_style))
        return elements

    def generate(self, data: Dict) -> bytes:
        temp_filename = f"summary_{int(time.time())}.pdf"
        doc = SimpleDocTemplate(temp_filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        story = []
        story += self._create_executive_summary(data.get('executive_summary', ''))
        story.append(PageBreak())
        story += self._create_table_of_contents(data['timestamps'])
        story.append(PageBreak())
        story += self._create_detailed_sections(data['timestamps'], data.get('full_summary', ''))
        if data.get('formulas'):
            story.append(PageBreak())
            story += self._create_formula_section(data['formulas'])
        story.append(PageBreak())
        story += self._create_key_takeaways(data.get('full_summary', ''))
        story += self._create_metadata_section(data)
        doc.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        with open(temp_filename, 'rb') as f:
            content = f.read()
        os.remove(temp_filename)
        return content