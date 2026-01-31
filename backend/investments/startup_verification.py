"""
Startup Verification Module
Handles blockchain-based startup verification and vetting.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.blockchain.startup_client import StartupClient
from app.services.credibility_service import CredibilityService
from app.db.models import Startup, User
from app.utils.logger import logger


class StartupVerification:
    """Startup verification service using blockchain."""
    
    def __init__(self):
        self.startup_client = StartupClient()
        self.credibility_service = CredibilityService()
    
    def verify_startup(
        self,
        startup_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Verify a startup on the blockchain.
        
        Returns:
            Verification result with blockchain proof
        """
        logger.info(f"Verifying startup: {startup_id}")
        
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise ValueError(f"Startup {startup_id} not found")
        
        # Get blockchain data
        blockchain_data = self.startup_client.get_startup_data(startup_id)
        
        # Calculate credibility score
        self.credibility_service.calculate_startup_credibility(db, startup.id)
        db.refresh(startup)
        
        return {
            "startup_id": startup_id,
            "verified": blockchain_data.get("verified", False),
            "on_chain": blockchain_data.get("on_chain", False),
            "credibility_score": startup.credibility_score,
            "transaction_signature": startup.transaction_signature,
            "blockchain_proof": blockchain_data
        }
    
    def list_verified_startups(
        self,
        skip: int = 0,
        limit: int = 100,
        sector: Optional[str] = None,
        min_credibility: float = 0.0,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        List verified startups with filtering options.
        
        Returns:
            List of verified startups
        """
        logger.info(f"Listing verified startups (skip={skip}, limit={limit})")
        
        query = db.query(Startup).filter(
            Startup.transaction_signature.isnot(None),
            Startup.credibility_score >= min_credibility
        )
        
        if sector:
            query = query.filter(Startup.sector.ilike(f"%{sector}%"))
        
        startups = query.offset(skip).limit(limit).all()
        
        result = []
        for startup in startups:
            result.append({
                "id": startup.id,
                "startup_id": startup.startup_id,
                "founder_id": startup.founder_id,  # Include founder_id for attestation fetching
                "name": startup.name,
                "sector": startup.sector,
                "country": startup.country,
                "credibility_score": startup.credibility_score,
                "funding_goal": startup.funding_goal,
                "description": startup.description,
                "transaction_signature": startup.transaction_signature,
                "verified": True,
                "on_chain": True
            })
        
        return result
    
    def get_startup_details(
        self,
        startup_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get detailed startup information with verification proof.
        
        Returns:
            Detailed startup information
        """
        logger.info(f"Getting startup details: {startup_id}")
        
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise ValueError(f"Startup {startup_id} not found")
        
        # Get founder
        founder = db.query(User).filter(User.id == startup.founder_id).first()
        
        # Get blockchain verification
        blockchain_data = self.startup_client.get_startup_data(startup_id)
        
        return {
            "id": startup.id,
            "startup_id": startup.startup_id,
            "founder_id": startup.founder_id,  # Include founder_id for attestation fetching
            "name": startup.name,
            "sector": startup.sector,
            "country": startup.country,
            "description": startup.description,
            "funding_goal": startup.funding_goal,
            "pitch_deck_url": startup.pitch_deck_url,
            "credibility_score": startup.credibility_score,
            "employees_verified": startup.employees_verified,
            "transaction_signature": startup.transaction_signature,
            "founder": {
                "id": founder.id if founder else None,
                "name": founder.full_name if founder else None,
                "email": founder.email if founder else None,
                "wallet_address": founder.wallet_address if founder else None
            },
            "website": startup.website,
            "contact_email": startup.contact_email,
            "phone": startup.phone,
            "address": startup.address,
            "year_founded": startup.year_founded,
            "team_size": startup.team_size,
            "mission": startup.mission,
            "vision": startup.vision,
            "products_services": startup.products_services,
            "verified": blockchain_data.get("verified", False),
            "on_chain": blockchain_data.get("on_chain", False),
            "blockchain_proof": blockchain_data,
            "created_at": startup.created_at.isoformat() if startup.created_at else None
        }

