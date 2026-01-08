"""
QR Code Service
Generates QR codes for startup verification
"""
import qrcode
from io import BytesIO
import base64
from typing import Dict, Any
from app.core.config import settings
from app.utils.logger import logger


class QRCodeService:
    """Generate QR codes for startup verification"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    def generate_startup_qr(self, startup_id: str) -> Dict[str, Any]:
        """
        Generate QR code containing verification URL
        Returns base64 encoded image and verification URL
        """
        try:
            verification_url = self.create_verification_url(startup_id)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Encode to base64
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info(f"Generated QR code for startup: {startup_id}")
            
            return {
                "startup_id": startup_id,
                "qr_code": f"data:image/png;base64,{qr_image_base64}",
                "verification_url": verification_url,
                "qr_code_svg": self._generate_svg_qr(verification_url)  # Alternative SVG format
            }
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise
    
    def create_verification_url(self, startup_id: str) -> str:
        """Create verification URL"""
        return f"{self.base_url}/verify/startup/{startup_id}"
    
    def _generate_svg_qr(self, data: str) -> str:
        """Generate SVG format QR code (alternative format)"""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create SVG string
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode()
