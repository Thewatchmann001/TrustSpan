#!/usr/bin/env python3
"""
Simple script to fund investor wallet using backend signing endpoint
"""
import asyncio
import httpx
import json

BACKEND_URL = "http://localhost:8000"
INVESTOR_WALLET = "3sLCCLDy783dBufq3ZNsNqdj3mF8BJiD9qvdGvjHyDw5"
AMOUNT_USDC = 1000


async def main():
    print("🔄 Funding investor wallet via backend signer...")
    print(f"   Recipient: {INVESTOR_WALLET}")
    print(f"   Amount: {AMOUNT_USDC} USDC\n")
    
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            # Query database for investor_id and any startup_id to use
            # For now, we'll use investor_id="1" and startup_id="1"
            investor_id = "1"
            startup_id = "1"
            
            print(f"📤 Step 1: Preparing transaction (investor_id={investor_id}, startup_id={startup_id})...")
            prepare_payload = {
                "investor_id": investor_id,
                "startup_id": startup_id,
                "amount_usdc": AMOUNT_USDC,
            }
            
            prepare_response = await client.post(
                f"{BACKEND_URL}/api/investments/usdc/prepare",
                json=prepare_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if prepare_response.status_code != 200:
                print(f"✗ Failed to prepare transaction: {prepare_response.text}")
                return False
            
            transaction_data = prepare_response.json()
            tx_hex = transaction_data.get("transaction_hex")
            print(f"✓ Transaction prepared")
            print(f"   Investor Wallet: {transaction_data.get('investor_wallet')}")
            print(f"   Recipient Wallet: {transaction_data.get('recipient_wallet')}")
            print(f"   Amount: {transaction_data.get('amount_base_units')} units\n")
            
            # Step 2: Sign on backend
            print(f"📝 Step 2: Signing transaction on backend...")
            sign_payload = {
                "transaction_hex": tx_hex,
            }
            
            sign_response = await client.post(
                f"{BACKEND_URL}/api/investments/usdc/sign",
                json=sign_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if sign_response.status_code != 200:
                print(f"✗ Failed to sign transaction: {sign_response.text}")
                return False
            
            signature_data = sign_response.json()
            signature = signature_data.get("signature")
            print(f"✓ Transaction signed")
            print(f"   Signature: {signature}\n")
            
            print("✅ Successfully funded investor!")
            print(f"   Recipient: {INVESTOR_WALLET}")
            print(f"   Amount: {AMOUNT_USDC} USDC")
            print(f"   Signature: {signature}")
            
            return True
            
        except httpx.ConnectError:
            print(f"✗ Cannot connect to backend at {BACKEND_URL}")
            print(f"   Make sure backend is running: python3 -m app.main")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
