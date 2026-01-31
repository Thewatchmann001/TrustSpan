#!/usr/bin/env python3
"""
Fund investor wallet with USDC from backend signer directly
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
import asyncio
import time
import base58

# Configuration
SOLANA_RPC_URL = "https://api.devnet.solana.com"
USDC_MINT = "1jxHPpKd5y2L8BVSSQT1pEP3R3VVZ1vfkQiktQZYA52"
AMOUNT_USDC = 1000  # Transfer 1000 USDC
DECIMALS = 6

# Backend signer
SIGNER_SECRET_KEY = "4XUgo1fspxBpPCywdfZovwmMaPmnLLNb7yucqdDiPmuLQmgqty77UwyGd484C6EQ9K1vTdT4mVGztSogHfoA6xTk"

# Investor wallet to fund
INVESTOR_WALLET = "3sLCCLDy783dBufq3ZNsNqdj3mF8BJiD9qvdGvjHyDw5"


async def main():
    print("🔄 Funding investor wallet with USDC...")
    print(f"   Signer: {SIGNER_SECRET_KEY[:20]}...")
    print(f"   Recipient: {INVESTOR_WALLET}")
    print(f"   Amount: {AMOUNT_USDC} USDC\n")
    
    # Parse keypair
    secret_bytes = base58.b58decode(SIGNER_SECRET_KEY)
    signer = Keypair.from_bytes(secret_bytes)
    signer_pubkey = signer.pubkey()
    
    print(f"✓ Signer loaded: {signer_pubkey}\n")
    
    # Parse pubkeys
    investor_pubkey = Pubkey.from_string(INVESTOR_WALLET)
    usdc_mint = Pubkey.from_string(USDC_MINT)
    
    # Connect to RPC
    async with AsyncClient(SOLANA_RPC_URL) as client:
        try:
            # Get latest blockhash
            print("📤 Getting latest blockhash...")
            response = await client.get_latest_blockhash(Confirmed)
            blockhash = response.value.blockhash
            print(f"✓ Blockhash: {blockhash}\n")
            
            # Use solders to build instructions
            from solders.instruction import Instruction, AccountMeta
            import struct
            import hashlib
            
            # Token program constants
            TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
            RENT_PROGRAM_ID = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
            ATA_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
            
            # Manual ATA calculation
            # ATA formula: find_pda(seeds=["account", owner, token_program, mint], program_id=ATA_PROGRAM)
            def calculate_ata(owner: Pubkey, mint: Pubkey) -> Pubkey:
                seeds = b"account" + bytes(owner) + bytes(TOKEN_PROGRAM_ID) + bytes(mint)
                for nonce in range(256):
                    seed_bytes = seeds + bytes([nonce])
                    sha = hashlib.sha256(seed_bytes + bytes(ATA_PROGRAM_ID)).digest()
                    if sha[31] >= 251:  # Not on curve
                        pda = Pubkey(sha[:32])
                        return pda
                return None
            
            signer_ata = calculate_ata(signer_pubkey, usdc_mint)
            investor_ata = calculate_ata(investor_pubkey, usdc_mint)
            
            print(f"✓ Signer ATA: {signer_ata}")
            print(f"✓ Investor ATA: {investor_ata}\n")
            
            # Check if investor ATA exists
            print(f"🔍 Checking if investor ATA exists...")
            account_info = await client.get_account_info(investor_ata, Confirmed)
            ata_exists = account_info.value is not None
            if ata_exists:
                print(f"✓ Investor ATA already exists\n")
            else:
                print(f"✗ Investor ATA does not exist, will create it\n")
            
            # Build instructions
            instructions = []
            
            # Create investor ATA if it doesn't exist
            if not ata_exists:
                print(f"📝 Creating investor ATA...")
                
                # Create Associated Token Account instruction
                # Program: ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL
                # accounts: [payer, ata, owner, mint, system, token_program, rent]
                data = bytes.fromhex("05")  # Create instruction data
                accounts = [
                    AccountMeta(signer_pubkey, True, True),   # payer
                    AccountMeta(investor_ata, False, True),   # ata
                    AccountMeta(investor_pubkey, False, False),  # owner
                    AccountMeta(usdc_mint, False, False),     # mint
                    AccountMeta(SYSTEM_PROGRAM_ID, False, False),  # system program
                    AccountMeta(TOKEN_PROGRAM_ID, False, False),   # token program
                    AccountMeta(RENT_PROGRAM_ID, False, False),    # rent
                ]
                
                create_ata = Instruction(ATA_PROGRAM_ID, data, accounts)
                instructions.append(create_ata)
                print(f"✓ Instruction created\n")
            
            # Transfer USDC
            print(f"📤 Creating transfer instruction...")
            
            # Transfer Checked instruction
            # Instruction discriminator for TransferChecked is [0x0c] (12)
            transfer_amount = int(AMOUNT_USDC * (10 ** DECIMALS))
            data = struct.pack('<BQ', 0x0c, transfer_amount) + struct.pack('<B', DECIMALS)
            
            accounts = [
                AccountMeta(signer_ata, False, True),     # source
                AccountMeta(usdc_mint, False, False),     # mint
                AccountMeta(investor_ata, False, True),   # destination
                AccountMeta(signer_pubkey, True, False),  # authority
                AccountMeta(TOKEN_PROGRAM_ID, False, False),  # token program
            ]
            
            transfer = Instruction(TOKEN_PROGRAM_ID, data, accounts)
            instructions.append(transfer)
            print(f"✓ Instruction created\n")
            
            # Create transaction
            print(f"📝 Creating VersionedTransaction...")            
            # Get fresh blockhash just before sending
            response = await client.get_latest_blockhash(Confirmed)
            blockhash = response.value.blockhash
            
            message = MessageV0.try_compile(
                payer=signer_pubkey,
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=blockhash,
            )
            
            tx = VersionedTransaction(message, [signer])
            print(f"✓ Transaction created with {len(instructions)} instruction(s)\n")
            
            # Send transaction
            print(f"📤 Sending transaction...")
            signature = await client.send_transaction(tx)
            sig_str = str(signature.value)
            print(f"✓ Transaction sent: {sig_str}\n")
            
            # Wait for confirmation
            print(f"⏳ Waiting for confirmation (up to 30 seconds)...")
            for i in range(30):
                await asyncio.sleep(1)
                status = await client.get_signature_statuses([signature.value])
                if status.value[0] is not None:
                    if status.value[0].err is None:
                        print(f"✅ Transaction confirmed after {i+1} seconds!\n")
                        print(f"✓ Successfully funded {INVESTOR_WALLET} with {AMOUNT_USDC} USDC")
                        print(f"✓ Signature: {sig_str}")
                        return True
                    else:
                        print(f"✗ Transaction failed: {status.value[0].err}")
                        return False
            
            print(f"⚠ Transaction not yet confirmed, but sent successfully")
            print(f"Signature: {sig_str}")
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
