"""
Investment Receipt Generator
Generates PDF receipts for investment transactions.
"""
from typing import Dict, Any
from datetime import datetime
from io import BytesIO
from app.utils.logger import logger


class ReceiptGenerator:
    """Service to generate investment receipts in PDF format."""
    
    def generate_receipt(
        self,
        investment: Dict[str, Any],
        investor: Dict[str, Any],
        startup: Dict[str, Any]
    ) -> bytes:
        """
        Generate a PDF receipt for an investment transaction.
        
        Args:
            investment: Investment data with id, amount, tx_signature, timestamp
            investor: Investor data with full_name, email, wallet_address
            startup: Startup data with name, sector, startup_id
            
        Returns:
            PDF bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            
            logger.info(f"Generating receipt for investment {investment.get('id')}")
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch
            )
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'ReceiptTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'ReceiptHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'ReceiptNormal',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#333333'),
                spaceAfter=6
            )
            
            # Title
            story.append(Paragraph("INVESTMENT RECEIPT", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Receipt Number and Date
            receipt_number = f"INV-{investment.get('id', 'N/A')}"
            receipt_date = investment.get('timestamp')
            if isinstance(receipt_date, str):
                try:
                    dt = datetime.fromisoformat(receipt_date.replace('Z', '+00:00'))
                    receipt_date = dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    receipt_date = receipt_date
            elif isinstance(receipt_date, datetime):
                receipt_date = receipt_date.strftime("%B %d, %Y at %I:%M %p")
            else:
                receipt_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            # Receipt Info Table
            receipt_info_data = [
                ['Receipt Number:', receipt_number],
                ['Date:', receipt_date]
            ]
            
            receipt_info_table = Table(receipt_info_data, colWidths=[2*inch, 4*inch])
            receipt_info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(receipt_info_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Investor Information
            story.append(Paragraph("Investor Information", heading_style))
            investor_name = investor.get('full_name', 'N/A')
            investor_email = investor.get('email', 'N/A')
            investor_wallet = investor.get('wallet_address', 'N/A')
            
            investor_data = [
                ['Name:', investor_name],
                ['Email:', investor_email],
                ['Wallet Address:', investor_wallet]
            ]
            
            investor_table = Table(investor_data, colWidths=[2*inch, 4*inch])
            investor_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(investor_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Startup Information
            story.append(Paragraph("Startup Information", heading_style))
            startup_name = startup.get('name', 'N/A')
            startup_id = startup.get('startup_id', 'N/A')
            startup_sector = startup.get('sector', 'N/A')
            
            startup_data = [
                ['Startup Name:', startup_name],
                ['Startup ID:', startup_id],
                ['Sector:', startup_sector]
            ]
            
            startup_table = Table(startup_data, colWidths=[2*inch, 4*inch])
            startup_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(startup_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Transaction Details
            story.append(Paragraph("Transaction Details", heading_style))
            amount = investment.get('amount', 0)
            tx_signature = investment.get('tx_signature', 'N/A')
            explorer_url = investment.get('explorer_url', '')
            
            transaction_data = [
                ['Investment Amount:', f"${amount:,.2f} USDC"],
                ['Transaction Signature:', tx_signature],
            ]
            
            transaction_table = Table(transaction_data, colWidths=[2*inch, 4*inch])
            transaction_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(transaction_table)
            story.append(Spacer(1, 0.4*inch))
            
            # Footer
            footer_text = (
                "This receipt serves as proof of your investment transaction on the TrustBridge platform. "
                "All transactions are recorded on the Solana blockchain for transparency and verification. "
                "Please keep this receipt for your records."
            )
            story.append(Paragraph(footer_text, normal_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            logger.error("reportlab not installed. Install with: pip install reportlab")
            raise NotImplementedError("Receipt generation requires reportlab. Install with: pip install reportlab")
        except Exception as e:
            logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            raise
