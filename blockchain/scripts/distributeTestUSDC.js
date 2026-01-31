const {
  Connection,
  Keypair,
  PublicKey,
} = require("@solana/web3.js");
const {
  getOrCreateAssociatedTokenAccount,
  mintTo,
  getMint,
} = require("@solana/spl-token");
const fs = require("fs");
const path = require("path");

/**
 * Distributes test USDC to investor wallets on Devnet
 * This mints test tokens to specified wallet addresses
 * @param {Object} params - Distribution parameters
 * @param {string|string[]} params.walletAddresses - Single address or array of addresses
 * @param {number} params.amountUSDC - Amount of test USDC to mint per wallet (default: 10000)
 */
async function distributeTestUSDC({ walletAddresses, amountUSDC = 10000 }) {
  try {
    // Connect to Solana Devnet
    const connection = new Connection("https://api.devnet.solana.com", "confirmed");

    // Load server wallet (mint authority)
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const walletPath = process.env.WALLET_PATH || path.join(homeDir, ".config/solana/id.json");
    const walletKeypair = Keypair.fromSecretKey(
      new Uint8Array(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
    );

    // Get test mint address from environment
    const TEST_USDC_MINT = process.env.DEVNET_USDC_MINT;
    if (!TEST_USDC_MINT || TEST_USDC_MINT === "YOUR_TEST_MINT_ADDRESS_HERE") {
      throw new Error('DEVNET_USDC_MINT not set. Please set it to your test mint address.');
    }

    const usdcMint = new PublicKey(TEST_USDC_MINT);

    // Get mint decimals
    const mintInfo = await getMint(connection, usdcMint);
    const decimals = mintInfo.decimals;

    // Convert USDC amount to token amount
    const tokenAmount = BigInt(Math.floor(amountUSDC * Math.pow(10, decimals)));

    // Normalize to array
    const addresses = Array.isArray(walletAddresses) ? walletAddresses : [walletAddresses];

    console.log(`🚀 Distributing ${amountUSDC} test USDC to ${addresses.length} wallet(s)...`);
    console.log(`📍 Mint Address: ${TEST_USDC_MINT}`);
    console.log(`💰 Amount per wallet: ${amountUSDC} USDC\n`);

    const results = [];

    for (let i = 0; i < addresses.length; i++) {
      const address = addresses[i].trim();
      console.log(`[${i + 1}/${addresses.length}] Processing: ${address}`);

      try {
        // Parse wallet address
        const walletPubkey = new PublicKey(address);

        // Get or create token account
        const tokenAccount = await getOrCreateAssociatedTokenAccount(
          connection,
          walletKeypair,  // Payer
          usdcMint,       // Mint
          walletPubkey    // Owner
        );

        // Mint tokens to this wallet
        await mintTo(
          connection,
          walletKeypair,        // Mint authority (server wallet)
          usdcMint,             // Mint
          tokenAccount.address, // Destination token account
          walletKeypair,        // Mint authority
          tokenAmount           // Amount
        );

        console.log(`  ✅ Minted ${amountUSDC} test USDC to ${address}`);
        console.log(`     Token Account: ${tokenAccount.address.toBase58()}\n`);

        results.push({
          wallet: address,
          tokenAccount: tokenAccount.address.toBase58(),
          amount: amountUSDC,
          status: "success"
        });
      } catch (error) {
        console.error(`  ❌ Failed for ${address}: ${error.message}\n`);
        results.push({
          wallet: address,
          amount: amountUSDC,
          status: "failed",
          error: error.message
        });
      }
    }

    console.log("🎉 Distribution complete!");
    console.log(`✅ Success: ${results.filter(r => r.status === "success").length}`);
    console.log(`❌ Failed: ${results.filter(r => r.status === "failed").length}`);

    return {
      mintAddress: TEST_USDC_MINT,
      totalWallets: addresses.length,
      amountPerWallet: amountUSDC,
      results: results
    };
  } catch (error) {
    console.error("❌ Error distributing test USDC:", error);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error("Usage: node distributeTestUSDC.js <walletAddress1> [walletAddress2] ... [amountUSDC]");
    console.error("Example: node distributeTestUSDC.js BWNLp4fEzpoZ33DLBnto3XsKW7PqxGw83dQHuzKftzDF 10000");
    console.error("Example: node distributeTestUSDC.js addr1 addr2 addr3 5000");
    process.exit(1);
  }

  // Last argument might be amount, check if it's a number
  let amountUSDC = 10000; // Default
  let walletAddresses = args;

  if (args.length > 0 && !isNaN(parseFloat(args[args.length - 1]))) {
    amountUSDC = parseFloat(args[args.length - 1]);
    walletAddresses = args.slice(0, -1);
  }

  distributeTestUSDC({
    walletAddresses: walletAddresses,
    amountUSDC: amountUSDC
  })
    .then((result) => {
      console.log("\n" + JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { distributeTestUSDC };
