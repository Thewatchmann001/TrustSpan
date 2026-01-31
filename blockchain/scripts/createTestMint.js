const {
  Connection,
  Keypair,
} = require("@solana/web3.js");
const {
  createMint,
  getOrCreateAssociatedTokenAccount,
  mintTo,
} = require("@solana/spl-token");
const fs = require("fs");
const path = require("path");

/**
 * Creates a test USDC token mint on Solana Devnet
 * This is for development only - tokens have no real value
 */
async function createTestMint() {
  try {
    const connection = new Connection("https://api.devnet.solana.com", "confirmed");
    
    // Load wallet
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const walletPath = process.env.WALLET_PATH || path.join(homeDir, ".config/solana/id.json");
    const walletKeypair = Keypair.fromSecretKey(
      new Uint8Array(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
    );

    console.log("🚀 Creating test USDC mint on Devnet...");
    console.log("📍 Wallet:", walletKeypair.publicKey.toBase58());
    
    // Create mint (6 decimals, like real USDC)
    console.log("\n⏳ Creating mint...");
    const testMint = await createMint(
      connection,
      walletKeypair,               // Payer
      walletKeypair.publicKey,     // Mint authority (can mint more tokens)
      null,                         // Freeze authority (null = no freeze)
      6                             // Decimals (same as real USDC)
    );

    console.log("\n✅ Test USDC Mint created!");
    console.log("🎯 Mint Address:", testMint.toBase58());
    console.log("\n📝 Add this to your .env file:");
    console.log(`   DEVNET_USDC_MINT=${testMint.toBase58()}`);
    
    // Create token account and mint some test tokens
    console.log("\n⏳ Creating token account and minting test tokens...");
    const tokenAccount = await getOrCreateAssociatedTokenAccount(
      connection,
      walletKeypair,
      testMint,
      walletKeypair.publicKey
    );

    // Mint 1,000,000 test "USDC" (1,000,000 * 10^6 = 1,000,000,000,000 raw units)
    const amount = BigInt(1000000 * Math.pow(10, 6));
    await mintTo(
      connection,
      walletKeypair,
      testMint,
      tokenAccount.address,
      walletKeypair,  // Mint authority
      amount
    );

    console.log("\n✅ Minted 1,000,000 test USDC to your wallet");
    console.log("💼 Token Account:", tokenAccount.address.toBase58());
    console.log("\n🎉 Test mint setup complete!");
    console.log("\n⚠️  REMEMBER: These are test tokens on devnet with NO real value");
    console.log("   Use this mint address in your investUSDC.js script");
    
    return {
      mintAddress: testMint.toBase58(),
      tokenAccount: tokenAccount.address.toBase58(),
      amount: "1000000",
    };
  } catch (error) {
    console.error("❌ Error creating test mint:", error);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  createTestMint()
    .then((result) => {
      console.log("\n" + JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { createTestMint };
