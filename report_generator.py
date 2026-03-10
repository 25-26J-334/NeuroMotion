from fpdf import FPDF
import os
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        self.report_dir = "reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def create_pdf_report(self, user_name, content, report_type="Training Report"):
        """Creates a professional PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(0, 80, 155) # Dark Blue
        pdf.cell(0, 20, f"AI Athlete Trainer - {report_type}", ln=True, align='C')
        
        # Subtitle
        pdf.set_font("Arial", 'I', 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Generated for: {user_name} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        
        # Content
        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)
        
        # Clean up Markdown-style bolding/headers for plain text PDF
        clean_content = content.replace("**", "").replace("#", "").replace("`", "")
        
        # Remove emojis and non-Latin-1 characters that crash FPDF standard fonts
        # We encode to latin-1 and ignore errors to strip unsupported characters
        try:
            clean_content = clean_content.encode('latin-1', 'ignore').decode('latin-1')
        except Exception:
            # Fallback to even more aggressive ASCII-only if latin-1 fails
            clean_content = clean_content.encode('ascii', 'ignore').decode('ascii')

        pdf.multi_cell(0, 8, clean_content)
        
        # Footer
        pdf.set_y(-20)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "Powered by TrainBot AI - Meta LLaMA 3", align='C')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type.lower().replace(' ', '_')}_{timestamp}.pdf"
        filepath = os.path.join(self.report_dir, filename)
        
        pdf.output(filepath)
        return filepath, filename
