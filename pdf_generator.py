import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import logging
import re

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the document"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Section header style
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Timestamp style
        self.timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=15,
            textColor=colors.darkred,
            leftIndent=20
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=20
        )
        
        # Executive summary style
        self.executive_style = ParagraphStyle(
            'Executive',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.lightgrey
        )
        
        # Metadata style
        self.metadata_style = ParagraphStyle(
            'Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            alignment=TA_LEFT,
            textColor=colors.grey
        )

    def generate_pdf(self, summary_data: Dict) -> bytes:
        """Generate professional PDF document from summary data"""
        logger.info("📄 Generating PDF document...")
        start_time = time.time()
        
        try:
            # Create temporary file
            temp_filename = f"summary_{int(time.time())}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                temp_filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build story (content)
            story = []
            
            # Add cover page
            story.extend(self._create_cover_page(summary_data))
            story.append(PageBreak())
            
            # Add table of contents
            story.extend(self._create_table_of_contents(summary_data))
            story.append(PageBreak())
            
            # Add executive summary
            story.extend(self._create_executive_summary(summary_data))
            story.append(PageBreak())
            
            # Add detailed content
            story.extend(self._create_detailed_content(summary_data))
            
            # Add generation metadata
            story.extend(self._create_generation_metadata(summary_data))
            
            # Build PDF
            doc.build(story)
            
            # Read the generated file
            with open(temp_filename, 'rb') as f:
                pdf_content = f.read()
            
            # Clean up temporary file
            os.remove(temp_filename)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ PDF generated in {processing_time:.2f}s")
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Clean up temp file if it exists
            if 'temp_filename' in locals() and os.path.exists(temp_filename):
                os.remove(temp_filename)
            raise

    def _create_cover_page(self, summary_data: Dict) -> List:
        """Create professional cover page"""
        elements = []
        
        # Main title
        title = Paragraph(f"Video Summary Report", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 40))
        
        # Video title
        video_title = Paragraph(f"<b>{summary_data['title']}</b>", self.subtitle_style)
        elements.append(video_title)
        elements.append(Spacer(1, 30))
        
        # Video metadata table
        metadata_data = [
            ['Channel:', summary_data['channel']],
            ['Duration:', summary_data['duration']],
            ['Upload Date:', summary_data.get('upload_date', 'Unknown')],
            ['Video ID:', summary_data['video_id']],
            ['Processing Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Processing Time:', f"{summary_data['processing_time']:.2f} seconds"]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 40))
        
        # Generated by note
        generated_note = Paragraph(
            "Generated by YouTube Video Summarizer<br/>"
            "Using AI-powered content analysis and summarization",
            self.metadata_style
        )
        elements.append(generated_note)
        
        return elements

    def _create_table_of_contents(self, summary_data: Dict) -> List:
        """Create table of contents with timestamp references"""
        elements = []
        
        # TOC title
        toc_title = Paragraph("Table of Contents", self.section_style)
        elements.append(toc_title)
        elements.append(Spacer(1, 20))
        
        # Executive summary entry
        exec_entry = Paragraph("Executive Summary", self.body_style)
        elements.append(exec_entry)
        elements.append(Spacer(1, 10))
        
        # Timestamp entries
        for timestamp in summary_data['timestamps']:
            toc_entry = Paragraph(
                f"{timestamp['time']} - {timestamp['title']}",
                self.body_style
            )
            elements.append(toc_entry)
            elements.append(Spacer(1, 5))
        
        # Key takeaways entry
        takeaways_entry = Paragraph("Key Takeaways", self.body_style)
        elements.append(takeaways_entry)
        
        return elements

    def _create_executive_summary(self, summary_data: Dict) -> List:
        """Create executive summary section"""
        elements = []
        
        # Section title
        exec_title = Paragraph("Executive Summary", self.section_style)
        elements.append(exec_title)
        elements.append(Spacer(1, 15))
        
        # Executive summary content
        if 'executive_summary' in summary_data and summary_data['executive_summary']:
            exec_content = Paragraph(
                summary_data['executive_summary'],
                self.executive_style
            )
            elements.append(exec_content)
        else:
            no_summary = Paragraph(
                "Executive summary not available for this video.",
                self.body_style
            )
            elements.append(no_summary)
        
        return elements

    def _create_detailed_content(self, summary_data: Dict) -> List:
        """Create detailed content sections organized by timestamps"""
        elements = []
        
        # Main content title
        content_title = Paragraph("Detailed Summary", self.section_style)
        elements.append(content_title)
        elements.append(Spacer(1, 20))
        
        # Process full summary if available
        if 'full_summary' in summary_data and summary_data['full_summary']:
            # Split summary into sections based on timestamps
            summary_text = summary_data['full_summary']
            
            # Create sections for each timestamp
            for timestamp in summary_data['timestamps']:
                # Add timestamp header
                timestamp_header = Paragraph(
                    f"{timestamp['time']} - {timestamp['title']}",
                    self.timestamp_style
                )
                elements.append(timestamp_header)
                
                # Find corresponding content in summary
                section_content = self._extract_section_content(
                    summary_text, timestamp['title']
                )
                
                if section_content:
                    content_para = Paragraph(section_content, self.body_style)
                    elements.append(content_para)
                else:
                    # Fallback: create section based on transcript
                    section_content = self._create_section_from_transcript(
                        summary_data, timestamp
                    )
                    content_para = Paragraph(section_content, self.body_style)
                    elements.append(content_para)
                
                elements.append(Spacer(1, 10))
        else:
            # Fallback: create basic sections from timestamps
            for timestamp in summary_data['timestamps']:
                timestamp_header = Paragraph(
                    f"{timestamp['time']} - {timestamp['title']}",
                    self.timestamp_style
                )
                elements.append(timestamp_header)
                
                # Create basic section content
                section_content = f"Content for section: {timestamp['title']}"
                content_para = Paragraph(section_content, self.body_style)
                elements.append(content_para)
                elements.append(Spacer(1, 10))
        
        # Add key takeaways section
        elements.extend(self._create_key_takeaways(summary_data))
        
        return elements

    def _extract_section_content(self, summary_text: str, section_title: str) -> str:
        """Extract content for a specific section from the full summary"""
        lines = summary_text.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line contains the section title
            if section_title.lower() in line.lower() and ('#' in line or ':' in line):
                in_section = True
                continue
            
            # Check if we've reached the next section
            if in_section and (line.startswith('##') or line.startswith('#')):
                break
            
            # Add content if we're in the right section
            if in_section:
                section_content.append(line)
        
        return ' '.join(section_content) if section_content else ""

    def _create_section_from_transcript(self, summary_data: Dict, timestamp: Dict) -> str:
        """Create section content from transcript data if available"""
        if 'transcript_list' in summary_data:
            # Extract text for this timestamp range
            start_idx = timestamp['start_index']
            end_idx = timestamp['end_index']
            
            section_text = " ".join([
                entry['text'] for entry in summary_data['transcript_list'][start_idx:end_idx]
            ])
            
            # Truncate if too long
            if len(section_text) > 500:
                section_text = section_text[:500] + "..."
            
            return section_text
        
        return f"Content for section: {timestamp['title']}"

    def _create_key_takeaways(self, summary_data: Dict) -> List:
        """Create key takeaways section"""
        elements = []
        
        # Section title
        takeaways_title = Paragraph("Key Takeaways", self.section_style)
        elements.append(takeaways_title)
        elements.append(Spacer(1, 15))
        
        # Extract key points from summary
        if 'full_summary' in summary_data and summary_data['full_summary']:
            summary_text = summary_data['full_summary']
            
            # Look for key takeaways in the summary
            takeaways = self._extract_key_takeaways(summary_text)
            
            for takeaway in takeaways:
                takeaway_para = Paragraph(f"• {takeaway}", self.body_style)
                elements.append(takeaway_para)
                elements.append(Spacer(1, 5))
        else:
            no_takeaways = Paragraph(
                "Key takeaways not available for this video.",
                self.body_style
            )
            elements.append(no_takeaways)
        
        return elements

    def _extract_key_takeaways(self, summary_text: str) -> List[str]:
        """Extract key takeaways from summary text"""
        takeaways = []
        lines = summary_text.split('\n')
        
        # Look for bullet points, numbered lists, or key phrases
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for bullet points
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                takeaways.append(line[1:].strip())
            # Check for numbered items
            elif re.match(r'^\d+\.', line):
                takeaways.append(line[line.find('.')+1:].strip())
            # Check for key phrases
            elif any(keyword in line.lower() for keyword in ['key', 'important', 'takeaway', 'main', 'primary']):
                takeaways.append(line)
        
        # Limit to 5-8 takeaways
        return takeaways[:8] if takeaways else ["No specific takeaways identified"]

    def _create_generation_metadata(self, summary_data: Dict) -> List:
        """Create generation metadata section"""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Generation Information", self.metadata_style))
        
        metadata_text = f"""
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Processing time: {summary_data['processing_time']:.2f} seconds
        Subtitle extraction time: {summary_data.get('subtitle_extraction_time', 0):.2f} seconds
        Number of sections: {len(summary_data['timestamps'])}
        Video duration: {summary_data['duration']}
        """
        
        metadata_para = Paragraph(metadata_text, self.metadata_style)
        elements.append(metadata_para)
        
        return elements

def generate_pdf(summary_data: Dict) -> bytes:
    """Convenience function to generate PDF from summary data"""
    generator = PDFGenerator()
    return generator.generate_pdf(summary_data)

if __name__ == "__main__":
    # Test PDF generation
    test_data = {
        'video_id': 'test123',
        'title': 'Test Video Title',
        'duration': '15:30',
        'channel': 'Test Channel',
        'upload_date': '2024-01-01',
        'processing_time': 45.2,
        'subtitle_extraction_time': 2.1,
        'executive_summary': 'This is a test executive summary for the video.',
        'full_summary': 'This is the full summary content with multiple sections.',
        'timestamps': [
            {
                'time': '0:00',
                'title': 'Introduction',
                'section_id': 1,
                'start_index': 0,
                'end_index': 10
            },
            {
                'time': '5:00',
                'title': 'Main Content',
                'section_id': 2,
                'start_index': 10,
                'end_index': 20
            }
        ]
    }
    
    try:
        pdf_content = generate_pdf(test_data)
        print(f"✅ PDF generated successfully ({len(pdf_content)} bytes)")
        
        # Save test PDF
        with open('test_summary.pdf', 'wb') as f:
            f.write(pdf_content)
        print("📄 Test PDF saved as 'test_summary.pdf'")
        
    except Exception as e:
        print(f"❌ PDF generation failed: {e}") 