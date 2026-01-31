#!/usr/bin/env python3
"""
Distribute test USDC to all investor wallets in the database
This script mints test USDC tokens to investor wallets on devnet
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.db.models import User
from app.utils.logger import logger
import subprocess
import json

def get_all_investor_wallets(db, amount_usdc=10000):
    """Get all investor wallet addresses from database"""
    investors = db.query(User).filter(User.role == "investor").all()
    
    wallet_addresses = []
    for investor in investors:
        if investor.wallet_address:
            wallet_addresses.append(investor.wallet_address.strip())
        else:
            logger.warning(f"Investor {investor.id} ({investor.email}) has no wallet address")
    
    return wallet_addresses

def distribute_to_investors(wallet_addresses, amount_usdc=10000):
    """Call Node.js script to distribute test USDC"""
    if not wallet_addresses:
        logger.warning("No investor wallets found")
        return
    
    # Get script path
    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir.parent / "blockchain" / "scripts" / "distributeTestUSDC.js"
    script_dir = script_path.parent
    
    # Build command
    cmd = ["node", str(script_path)] + wallet_addresses + [str(amount_usdc)]
    
    logger.info(f"Distributing {amount_usdc} test USDC to {len(wallet_addresses)} investors...")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(script_dir),
        env=os.environ.copy()
    )
    
    if result.returncode != 0:
        logger.error(f"Distribution failed: {result.stderr}")
        print(result.stderr)
        return None
    
    # Parse JSON response
    try:
        # Find JSON in output (might have console.log before it)
        output = result.stdout
        json_start = output.find('{')
        if json_start >= 0:
            json_str = output[json_start:]
            data = json.loads(json_str)
            return data
        else:
            logger.warning("No JSON found in output")
            print(result.stdout)
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        print(result.stdout)
        return None

def main():
    """Main function"""
    db = SessionLocal()
    try:
        # Get all investor wallets
        wallet_addresses = get_all_investor_wallets(db, amount_usdc=10000)
        
        if not wallet_addresses:
            print("❌ No investor wallets found in database")
            return
        
        print(f"📋 Found {len(wallet_addresses)} investor wallet(s):")
        for addr in wallet_addresses:
            print(f"   - {addr}")
        print()
        
        # Distribute test USDC
        result = distribute_to_investors(wallet_addresses, amount_usdc=10000)
        
        if result:
            print("\n✅ Distribution Results:")
            print(f"   Total wallets: {result.get('totalWallets', 0)}")
            print(f"   Amount per wallet: {result.get('amountPerWallet', 0)} USDC")
            
            success_count = sum(1 for r in result.get('results', []) if r.get('status') == 'success')
            print(f"   ✅ Success: {success_count}")
            print(f"   ❌ Failed: {len(result.get('results', [])) - success_count}")
        else:
            print("❌ Distribution failed")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
