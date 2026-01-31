import { Connection, PublicKey } from "@solana/web3.js";
import { getAccount } from "@solana/spl-token";

const SOLANA_RPC_URL = "https://api.devnet.solana.com";
const USDC_MINT = "1jxHPpKd5y2L8BVSSQT1pEP3R3VVZ1vfkQiktQZYA52";
const SIGNER_ATA = "4UqagocrXXGaUjzyVvgaNDkSoDXofMsLy2N3sZUZUQNw";

async function check() {
  const connection = new Connection(SOLANA_RPC_URL);
  try {
    const account = await getAccount(connection, new PublicKey(SIGNER_ATA));
    console.log("✓ Signer USDC ATA found");
    console.log(`  Owner: ${account.owner.toString()}`);
    console.log(`  Mint: ${account.mint.toString()}`);
    console.log(`  Amount: ${account.amount.toString()} (raw units)`);
    console.log(`  Amount: ${Number(account.amount) / 1e6} USDC`);
  } catch (e) {
    console.log("✗ Signer USDC ATA not found or error:", e.message);
  }
}

check();
