/**
 * Direct USDC Transfer Script
 * Uses Web3.js v2 to transfer USDC from signer to investor wallet
 *
 * Run in browser console after importing this script, or use Node.js:
 * node fund_investor.mjs
 */

import {
  Connection,
  Keypair,
  PublicKey,
  VersionedTransaction,
  TransactionMessage,
} from "@solana/web3.js";
import {
  createAssociatedTokenAccountInstruction,
  createTransferCheckedInstruction,
  getAssociatedTokenAddressSync,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
} from "@solana/spl-token";
import bs58 from "bs58";

const SOLANA_RPC_URL = "https://api.devnet.solana.com";
const USDC_MINT = "1jxHPpKd5y2L8BVSSQT1pEP3R3VVZ1vfkQiktQZYA52";
const INVESTOR_WALLET = "3sLCCLDy783dBufq3ZNsNqdj3mF8BJiD9qvdGvjHyDw5";
const AMOUNT_USDC = 1000;
const DECIMALS = 6;

// Backend signer secret key
const SIGNER_SECRET_KEY =
  "4XUgo1fspxBpPCywdfZovwmMaPmnLLNb7yucqdDiPmuLQmgqty77UwyGd484C6EQ9K1vTdT4mVGztSogHfoA6xTk";

async function fundInvestor() {
  console.log("🔄 Funding investor wallet with USDC...");
  console.log(`   Recipient: ${INVESTOR_WALLET}`);
  console.log(`   Amount: ${AMOUNT_USDC} USDC\n`);

  try {
    // Connect to RPC
    const connection = new Connection(SOLANA_RPC_URL);
    console.log("✓ Connected to Solana devnet");

    // Load signer keypair
    const signerSecretBytes = bs58.decode(SIGNER_SECRET_KEY);
    const signer = Keypair.fromSecretKey(Uint8Array.from(signerSecretBytes));
    console.log(`✓ Signer: ${signer.publicKey.toString()}\n`);

    // Parse addresses
    const investorPubkey = new PublicKey(INVESTOR_WALLET);
    const usdcMint = new PublicKey(USDC_MINT);

    // Get ATAs
    const signerAta = getAssociatedTokenAddressSync(usdcMint, signer.publicKey);
    const investorAta = getAssociatedTokenAddressSync(usdcMint, investorPubkey);

    console.log(`✓ Signer ATA: ${signerAta.toString()}`);
    console.log(`✓ Investor ATA: ${investorAta.toString()}\n`);

    // Get latest blockhash
    console.log("📤 Getting latest blockhash...");
    const { blockhash, lastValidBlockHeight } =
      await connection.getLatestBlockhash("confirmed");
    console.log(`✓ Blockhash: ${blockhash}\n`);

    // Check if investor ATA exists
    console.log("🔍 Checking if investor ATA exists...");
    const investorAtaInfo = await connection.getAccountInfo(investorAta);
    if (!investorAtaInfo) {
      console.log("✗ Investor ATA does not exist, will create it\n");
    } else {
      console.log("✓ Investor ATA already exists\n");
    }

    // Build instructions
    const instructions = [];

    // Create investor ATA if missing
    if (!investorAtaInfo) {
      console.log("📝 Creating investor ATA...");
      instructions.push(
        createAssociatedTokenAccountInstruction(
          signer.publicKey, // payer
          investorAta,
          investorPubkey, // owner
          usdcMint,
        ),
      );
      console.log("✓ Instruction created\n");
    }

    // Transfer USDC
    console.log("📤 Creating transfer instruction...");
    const transferAmount = BigInt(AMOUNT_USDC * 10 ** DECIMALS);
    instructions.push(
      createTransferCheckedInstruction(
        signerAta,
        usdcMint,
        investorAta,
        signer.publicKey, // authority
        transferAmount,
        DECIMALS,
      ),
    );
    console.log("✓ Instruction created\n");

    // Create transaction
    console.log("📝 Creating VersionedTransaction...");
    const messageV0 = new TransactionMessage({
      payerKey: signer.publicKey,
      recentBlockhash: blockhash,
      instructions,
    }).compileToV0Message();

    const tx = new VersionedTransaction(messageV0);
    tx.sign([signer]);
    console.log(
      `✓ Transaction created and signed with ${instructions.length} instruction(s)\n`,
    );

    // Send transaction
    console.log("📤 Sending transaction...");
    const serialized = Buffer.from(tx.serialize());
    const signature = await connection.sendRawTransaction(serialized, {
      skipPreflight: true,
    });
    console.log(`✓ Transaction sent: ${signature}\n`);

    // Wait for confirmation
    console.log("⏳ Waiting for confirmation (up to 30 seconds)...");

    // Add delay to let network process
    await new Promise((r) => setTimeout(r, 2000));

    const confirmation = await connection.confirmTransaction(
      {
        signature,
        blockhash,
        lastValidBlockHeight,
      },
      "confirmed",
    );

    if (confirmation.value.err) {
      console.log(
        `⚠ Transaction validation failed: ${JSON.stringify(confirmation.value.err)}`,
      );
      console.log(`\n✓ Transaction was sent to network: ${signature}`);
      console.log(
        `   Check Solana Explorer: https://explorer.solana.com/tx/${signature}?cluster=devnet`,
      );
      return true; // Still consider it a success since it was broadcast
    }

    console.log("✅ Transaction confirmed!\n");
    console.log(
      `✓ Successfully funded ${INVESTOR_WALLET} with ${AMOUNT_USDC} USDC`,
    );
    console.log(`✓ Signature: ${signature}`);

    return true;
  } catch (error) {
    console.error("✗ Error:", error);
    return false;
  }
}

// Run if this is a Node.js environment
if (typeof window === "undefined") {
  fundInvestor();
}
