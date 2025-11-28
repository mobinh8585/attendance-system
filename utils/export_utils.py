import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import inch
import csv
import os
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument
from utils.persian_utils import to_persian_number
from persiantools.jdatetime import JalaliDateTime
from bidi.algorithm import get_display
import arabic_reshaper
import platform

class ExportManager:
    def __init__(self):
        self.persian_font_registered = False
        self._register_persian_fonts()
        
    def _register_persian_fonts(self):
        """Register Persian fonts for PDF generation"""
        try:
            # Try to find system fonts
            font_paths = []
            
            if platform.system() == "Windows":
                font_paths = [
                    "C:/Windows/Fonts/B Nazanin.ttf",
                    "C:/Windows/Fonts/BNazanin.ttf",
                    "C:/Windows/Fonts/tahoma.ttf",
                    "C:/Windows/Fonts/Arial.ttf"
                ]
            elif platform.system() == "Linux":
                font_paths = [
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                ]
                
            # Try project fonts directory
            if os.path.exists("fonts"):
                font_paths.extend([
                    "fonts/BNazanin.ttf",
                    "fonts/Vazir.ttf",
                    "fonts/IRANSans.ttf"
                ])
                
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.splitext(os.path.basename(font_path))[0].replace(" ", "")
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.persian_font = font_name
                    self.persian_font_registered = True
                    break
        except:
            pass
            
        if not self.persian_font_registered:
            self.persian_font = 'Helvetica'
    
    def export_to_excel(self, data, columns, file_path):
        """Export data to Excel file"""
        try:
            df = pd.DataFrame(data, columns=columns)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='گزارش', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['گزارش']
                
                # Set RTL direction
                worksheet.sheet_view.rightToLeft = True
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return True
        except Exception as e:
            print(f"Export to Excel error: {e}")
            return False
    
    def _prepare_text_for_pdf(self, text):
        """Prepare Persian/Arabic text for PDF"""
        try:
            if not text:
                return ""
            # Reshape Arabic/Persian text
            reshaped_text = arabic_reshaper.reshape(str(text))
            # Apply RTL algorithm
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            # Fallback to simple reversal if libraries not available
            return str(text)[::-1] if text else ""
    
    def export_to_pdf(self, data, columns, file_path, title="گزارش"):
        """Export data to PDF file"""
        try:
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=self.persian_font,
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            # Add title
            elements.append(Paragraph(self._prepare_text_for_pdf(title), title_style))
            
            # Add timestamp
            now = JalaliDateTime.now()
            timestamp = f"تاریخ گزارش: {to_persian_number(now.strftime('%Y/%m/%d - %H:%M'))}"
            timestamp_style = ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontName=self.persian_font,
                fontSize=12,
                alignment=1
            )
            elements.append(Paragraph(self._prepare_text_for_pdf(timestamp), timestamp_style))
            elements.append(Paragraph("<br/><br/>", styles['Normal']))
            
            # Prepare table data with RTL text
            table_data = []
            # Headers
            header_row = [self._prepare_text_for_pdf(col) for col in columns]
            table_data.append(header_row)
            
            # Data rows
            for row in data:
                table_data.append([self._prepare_text_for_pdf(cell) for cell in row])
            
            # Create table
            table = Table(table_data)
            
            # Apply table style
            table_style = TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data style
                ('FONTNAME', (0, 1), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            table.setStyle(table_style)
            
            # Auto-adjust column widths
            table._argW = [None] * len(columns)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            return True
        except Exception as e:
            print(f"Export to PDF error: {e}")
            return False
    
    def export_to_csv(self, data, columns, file_path):
        """Export data to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"Export to CSV error: {e}")
            return False
    
    def print_data(self, data, columns, title, parent_widget):
        """Print data using system print dialog"""
        try:
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'B Nazanin', Tahoma, Arial;
                        direction: rtl;
                        text-align: right;
                    }}
                    h1 {{
                        color: #1976D2;
                        text-align: center;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    th {{
                        background-color: #2196F3;
                        color: white;
                        padding: 10px;
                        text-align: center;
                        border: 1px solid #ddd;
                    }}
                    td {{
                        padding: 8px;
                        text-align: center;
                        border: 1px solid #ddd;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f5f5f5;
                    }}
                    .timestamp {{
                        text-align: center;
                        color: #666;
                        margin-top: 10px;
                    }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p class="timestamp">تاریخ: {to_persian_number(JalaliDateTime.now().strftime('%Y/%m/%d - %H:%M'))}</p>
                <table>
                    <thead>
                        <tr>
            """
            
            # Add headers
            for col in columns:
                html_content += f"<th>{col}</th>"
            
            html_content += """
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Add data rows
            for row in data:
                html_content += "<tr>"
                for cell in row:
                    html_content += f"<td>{cell}</td>"
                html_content += "</tr>"
            
            html_content += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Create printer and document
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, parent_widget)
            
            if dialog.exec():
                document = QTextDocument()
                document.setHtml(html_content)
                document.print(printer)
                return True
            
            return False
        except Exception as e:
            print(f"Print error: {e}")
            return False