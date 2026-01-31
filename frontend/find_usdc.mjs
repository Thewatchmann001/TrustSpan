import { Connection, PublicKey } from "@solana/web3.js";
import { getAssociatedTokenAddressSync } from "@solana/spl-token";

const connection = new Connection("https://api.devnet.solana.com");
const USDC_MINT = new PublicKey("1jxHPpKd5y2L8BVSSQT1pEP3R3VVZ1vfkQiktQZYA52");
const PHANTOM_WALLET = new PublicKey("3sLCCLDy783dBufq3ZNsNqdj3mF8BJiD9qvdGvjHyDw5");

async function check() {
  // Check the ATA for Phantom wallet
  const phantomAta = getAssociatedTokenAddressSync(USDC_MINT, PHANTOM_WALLET);
  console.log(`Phantom wallet: ${PHANTOM_WALLET.toString()}`);
  console.log(`Expected ATA: ${phantomAta.toString()}\n`);
  
  // Get all token accounts for this wallet
  const tokenAccounts = await connection.getParsedTokenAccountsByOwner(PHANTOM_WALLET, {
    programId: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
  });
  
  console.log(`Found ${tokenAccounts.value.length} token account(s):\n`);
  
  for (const account of tokenAccounts.value) {
    const data = account.account.data.parsed.info;
    console.log(`Account: ${account.pubkey.toString()}`);
    console.log(`  Mint: ${data.mint}`);
    console.log(`  Balance: ${data.tokenAmount.uiAmount} tokens`);
    console.log(`  Decimals: ${data.tokenAmount.decimals}\n`);
  }
}

check();
