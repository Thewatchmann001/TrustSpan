"""
USDC Transactions Module
Handles USDC stablecoin transfers on Solana for investments.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.blockchain.investment_client import InvestmentClient
from app.db.models import Investment, Startup, User
from app.utils.logger import logger
from app.core.exceptions import BlockchainError


class USDCTransactions:
    """USDC transaction service for investments."""
    
    def __init__(self):
        self.investment_client = InvestmentClient()
    
    def send_usdc_investment(
        self,
        investor_id: int,
        startup_id: str,
        amount_usdc: float,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send USDC investment to a startup.
        
        Args:
            investor_id: Investor user ID
            startup_id: Startup ID (on-chain)
            amount_usdc: Amount in USDC
            db: Database session
            
        Returns:
            Investment transaction result
        """
        logger.info(f"Sending {amount_usdc} USDC investment from investor {investor_id} to startup {startup_id}")
        
        # Verify investor exists and has wallet
        investor = db.query(User).filter(User.id == investor_id).first()
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        if not investor.wallet_address:
            raise ValueError("Investor must have a wallet address")
        
        # Verify startup exists
        startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
        if not startup:
            raise ValueError(f"Startup {startup_id} not found")
        
        # Get founder's wallet address (needed for USDC transfer)
        founder = db.query(User).filter(User.id == startup.founder_id).first()
        if not founder or not founder.wallet_address:
            raise ValueError("Startup founder must have a wallet address")
        
        founder_wallet_address = founder.wallet_address.strip()
        
        # Validate wallet address formats
        from app.utils.helpers import validate_solana_address
        wallet_address = investor.wallet_address.strip()
        
        if not validate_solana_address(wallet_address):
            raise ValueError("Invalid investor Solana wallet address format")
        
        if not validate_solana_address(founder_wallet_address):
            raise ValueError("Invalid founder Solana wallet address format")
        
        # Ensure startup is registered on-chain
        if not startup.transaction_signature or startup.transaction_signature.startswith("mock_"):
            logger.info(f"Startup {startup_id} not registered on-chain, registering now...")
            
            # Register startup on-chain
            from blockchain.startup_client import StartupClient
            startup_client = StartupClient()
            
            blockchain_result = startup_client.register_startup(
                startup_name=startup.name,
                sector=startup.sector,
                founder_address=founder_wallet_address
            )
            
            blockchain_startup_id = blockchain_result.get("startup_id")
            if blockchain_startup_id:
                startup.startup_id = blockchain_startup_id
            startup.transaction_signature = blockchain_result.get("transaction_signature")
            db.commit()
            db.refresh(startup)
        
        # Transfer USDC and record investment on blockchain
        blockchain_result = self.investment_client.invest_in_startup(
            investor_address=wallet_address,
            founder_address=founder_wallet_address,  # NEW: Pass founder address for USDC transfer
            startup_id=startup.startup_id,
            amount_usdc=amount_usdc
        )
        
        # Save to database
        investment = Investment(
            startup_id=startup.id,
            investor_id=investor_id,
            amount=amount_usdc,
            tx_signature=blockchain_result.get("transaction_signature")
        )
        
        db.add(investment)
        db.commit()
        db.refresh(investment)
        
        # Recalculate credibility
        from app.services.credibility_service import CredibilityService
        credibility_service = CredibilityService()
        credibility_service.calculate_startup_credibility(db, startup.id)
        
        logger.info(f"Investment recorded: {blockchain_result.get('investment_id')}")
        
        return {
            "investment_id": blockchain_result.get("investment_id"),
            "transaction_signature": blockchain_result.get("transaction_signature"),
            "confirmation_url": blockchain_result.get("confirmation_url"),
            "blockchain_proof": blockchain_result.get("blockchain_proof"),
            "amount_usdc": amount_usdc,
            "startup_id": startup_id,
            "investor_id": investor_id,
            "timestamp": blockchain_result.get("timestamp")
        }
    
    def get_transaction_status(
        self,
        transaction_signature: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get status of a USDC transaction.
        
        Returns:
            Transaction status and details
        """
        logger.info(f"Getting transaction status: {transaction_signature}")
        
        investment = db.query(Investment).filter(
            Investment.tx_signature == transaction_signature
        ).first()
        
        if not investment:
            raise ValueError(f"Transaction {transaction_signature} not found")
        
        return {
            "transaction_signature": transaction_signature,
            "status": "confirmed",
            "amount_usdc": investment.amount,
            "startup_id": investment.startup.startup_id if investment.startup else None,
            "investor_id": investment.investor_id,
            "timestamp": investment.timestamp.isoformat() if investment.timestamp else None,
            "explorer_url": f"https://explorer.solana.com/tx/{transaction_signature}?cluster=devnet"
        }

