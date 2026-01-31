const {
  Connection,
  PublicKey,
} = require("@solana/web3.js");
const {
  getAssociatedTokenAddress,
  getAccount,
  getMint,
} = require("@solana/spl-token");

/**
 * Check USDC token balance for a wallet address
 * @param {string} walletAddress - Solana wallet address
 * @param {string} mintAddress - USDC mint address (optional, uses DEVNET_USDC_MINT if not provided)
 */
async function checkTokenBalance(walletAddress, mintAddress = null) {
  try {
    const connection = new Connection("https://api.devnet.solana.com", "confirmed");
    
    // Get mint address
    const TEST_USDC_MINT = mintAddress || process.env.DEVNET_USDC_MINT;
    if (!TEST_USDC_MINT || TEST_USDC_MINT === "YOUR_TEST_MINT_ADDRESS_HERE") {
      throw new Error('DEVNET_USDC_MINT not set. Please set it to your test mint address.');
    }

    const usdcMint = new PublicKey(TEST_USDC_MINT);
    const walletPubkey = new PublicKey(walletAddress);

    // Get associated token account address
    const tokenAccount = await getAssociatedTokenAddress(
      usdcMint,
      walletPubkey
    );

    console.log(`\n📊 Token Balance Check`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`Wallet Address: ${walletAddress}`);
    console.log(`Token Account:  ${tokenAccount.toBase58()}`);
    console.log(`Mint Address:   ${TEST_USDC_MINT}`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

    try {
      // Get token account info
      const tokenAccountInfo = await getAccount(connection, tokenAccount);
      const mintInfo = await getMint(connection, usdcMint);
      
      // Calculate balance (accounting for decimals)
      const balance = Number(tokenAccountInfo.amount) / Math.pow(10, mintInfo.decimals);
      
      console.log(`✅ Token Account EXISTS`);
      console.log(`💰 Balance: ${balance.toLocaleString()} USDC`);
      console.log(`📝 Owner: ${tokenAccountInfo.owner.toBase58()}`);
      console.log(`🔢 Decimals: ${mintInfo.decimals}`);
      console.log(`\n🔗 View on Explorer:`);
      console.log(`   Token Account: https://explorer.solana.com/address/${tokenAccount.toBase58()}?cluster=devnet`);
      console.log(`   Wallet: https://explorer.solana.com/address/${walletAddress}?cluster=devnet`);
      
      return {
        wallet: walletAddress,
        tokenAccount: tokenAccount.toBase58(),
        balance: balance,
        balanceRaw: tokenAccountInfo.amount.toString(),
        decimals: mintInfo.decimals,
        exists: true
      };
    } catch (error) {
      if (error.message.includes("could not find account")) {
        console.log(`❌ Token Account DOES NOT EXIST`);
        console.log(`   This means no USDC has been minted/transferred to this wallet yet.`);
        console.log(`\n💡 To create the token account and mint USDC:`);
        console.log(`   1. Run: node distributeTestUSDC.js ${walletAddress} 10000`);
        console.log(`   2. Or make an investment (auto-creates token account)`);
        
        return {
          wallet: walletAddress,
          tokenAccount: tokenAccount.toBase58(),
          balance: 0,
          exists: false
        };
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error("❌ Error checking token balance:", error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error("Usage: node checkTokenBalance.js <walletAddress> [mintAddress]");
    console.error("Example: node checkTokenBalance.js HJMkzfHxzXNXKdbgu9HkUPqQYqz9QjeDLRFtvyEgRs7S");
    process.exit(1);
  }

  const walletAddress = args[0];
  const mintAddress = args[1] || null;

  checkTokenBalance(walletAddress, mintAddress)
    .then((result) => {
      console.log("\n" + JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { checkTokenBalance };
