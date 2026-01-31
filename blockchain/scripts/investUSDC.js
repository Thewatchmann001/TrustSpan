const {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionInstruction,
} = require("@solana/web3.js");
const {
  getAssociatedTokenAddress,
  createAssociatedTokenAccountInstruction,
  createTransferCheckedInstruction,
  getMint,
  getAccount,
  getOrCreateAssociatedTokenAccount,
  mintTo,
  TOKEN_PROGRAM_ID,
} = require("@solana/spl-token");
const fs = require("fs");
const path = require("path");

/**
 * Transfers test USDC on Devnet and records investment on Solana Devnet
 * THIS IS DEVNET ONLY - NO REAL MONEY INVOLVED
 * @param {Object} params - Investment parameters
 * @param {string} params.investorAddress - Solana address of the investor
 * @param {string} params.founderAddress - Solana address of the founder (to receive USDC)
 * @param {string} params.startupId - Startup ID receiving investment
 * @param {number} params.amountUSDC - Amount in test USDC (devnet only, no real value)
 * @returns {Promise<Object>} Investment record with transaction signatures
 */
async function investUSDC({ investorAddress, founderAddress, startupId, amountUSDC }) {
  try {
    // Validate inputs
    if (!investorAddress || typeof investorAddress !== 'string') {
      throw new Error('Investor address is required and must be a string');
    }
    
    if (!founderAddress || typeof founderAddress !== 'string') {
      throw new Error('Founder address is required and must be a string');
    }
    
    investorAddress = investorAddress.trim();
    founderAddress = founderAddress.trim();
    
    if (investorAddress.length === 0 || founderAddress.length === 0) {
      throw new Error('Investor and founder addresses cannot be empty');
    }
    
    if (investorAddress.length < 32 || investorAddress.length > 44 || 
        founderAddress.length < 32 || founderAddress.length > 44) {
      throw new Error(`Invalid address length. Solana addresses must be 32-44 characters.`);
    }
    
    // Validate base58 characters
    const base58Regex = /^[1-9A-HJ-NP-Za-km-z]+$/;
    if (!base58Regex.test(investorAddress) || !base58Regex.test(founderAddress)) {
      throw new Error(`Invalid address format: contains non-base58 characters.`);
    }
    
    // Connect to Solana Devnet (TEST NETWORK - NO REAL MONEY)
    const connection = new Connection(
      "https://api.devnet.solana.com",
      "confirmed"
    );

    // Load server wallet (for signing transactions and paying fees)
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const walletPath =
      process.env.WALLET_PATH || path.join(homeDir, ".config/solana/id.json");
    const walletKeypair = Keypair.fromSecretKey(
      new Uint8Array(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
    );

    // IMPORTANT: Devnet test token mint (NOT mainnet USDC)
    // Replace with your test mint address (run createTestMint.js first)
    const TEST_USDC_MINT = process.env.DEVNET_USDC_MINT || 
      "YOUR_TEST_MINT_ADDRESS_HERE"; // ← Must be set to your test mint address
    
    if (TEST_USDC_MINT === "YOUR_TEST_MINT_ADDRESS_HERE") {
      throw new Error('DEVNET_USDC_MINT not set. Please run createTestMint.js first and set DEVNET_USDC_MINT environment variable.');
    }

    const usdcMint = new PublicKey(TEST_USDC_MINT);

    // Parse addresses
    const investorPubkey = new PublicKey(investorAddress);
    const founderPubkey = new PublicKey(founderAddress);

    // Get associated token addresses (for USDC token accounts)
    const investorTokenAccount = await getAssociatedTokenAddress(
      usdcMint,
      investorPubkey
    );
    
    const founderTokenAccount = await getAssociatedTokenAddress(
      usdcMint,
      founderPubkey
    );

    // Check if token accounts exist
    const investorTokenAccountInfo = await connection.getAccountInfo(investorTokenAccount);
    const founderTokenAccountInfo = await connection.getAccountInfo(founderTokenAccount);

    // Create transaction for USDC transfer and investment record
    const transaction = new Transaction();

    // PHASE 1: Create token accounts if needed
    if (!investorTokenAccountInfo) {
      transaction.add(
        createAssociatedTokenAccountInstruction(
          walletKeypair.publicKey, // Payer
          investorTokenAccount,    // Token account
          investorPubkey,          // Owner
          usdcMint                 // Mint
        )
      );
    }

    if (!founderTokenAccountInfo) {
      transaction.add(
        createAssociatedTokenAccountInstruction(
          walletKeypair.publicKey, // Payer
          founderTokenAccount,     // Token account
          founderPubkey,           // Owner
          usdcMint                 // Mint
        )
      );
    }

    // PHASE 2: Mint USDC directly to founder (devnet only - no investor signature needed)
    // In production, this would be a transfer from investor to founder with investor signature
    // Get mint decimals
    let decimals = 6; // Default USDC decimals
    try {
      const mintInfo = await getMint(connection, usdcMint);
      decimals = mintInfo.decimals;
    } catch (error) {
      console.warn("Could not get mint info, using default 6 decimals");
    }

    // Convert USDC to token amount (accounting for decimals)
    const mintAmount = BigInt(Math.floor(amountUSDC * Math.pow(10, decimals)));

    // For devnet: Mint directly to founder (bypasses investor signature requirement)
    // This simulates the investment without requiring the investor to sign
    // In production, the investor would transfer from their own account
    console.log(`💰 Minting ${amountUSDC} test USDC directly to founder (devnet only - no manual distribution needed)...`);
    
    // Ensure founder token account exists
    if (!founderTokenAccountInfo) {
      transaction.add(
        createAssociatedTokenAccountInstruction(
          walletKeypair.publicKey, // Payer
          founderTokenAccount,     // Token account
          founderPubkey,           // Owner
          usdcMint                 // Mint
        )
      );
    }
    
    // Mint USDC directly to founder's account BEFORE building the investment transaction
    // This is done in a separate step so we don't need investor signatures
    try {
      const founderTokenAccountForMint = await getOrCreateAssociatedTokenAccount(
        connection,
        walletKeypair,
        usdcMint,
        founderPubkey
      );
      
      // Mint directly to founder (server wallet is mint authority)
      await mintTo(
        connection,
        walletKeypair,              // Mint authority (server wallet)
        usdcMint,                   // Mint
        founderTokenAccountForMint.address, // Destination
        walletKeypair,              // Mint authority
        mintAmount                  // Amount
      );
      
      console.log(`✅ Minted ${amountUSDC} test USDC to founder's wallet`);
    } catch (mintError) {
      console.error(`❌ Failed to mint USDC to founder: ${mintError.message}`);
      throw new Error(`Failed to mint test USDC: ${mintError.message}`);
    }
    
    // Note: We're NOT transferring from investor to founder
    // Instead, we're minting directly to founder (devnet testing approach)
    // This means:
    // - ✅ No investor signature needed
    // - ✅ No manual USDC distribution needed
    // - ✅ Works automatically
    // - ✅ Still records investment on-chain
    // In production, you would:
    // 1. Check investor has enough USDC
    // 2. Have investor sign a transfer transaction (via frontend wallet)
    // 3. Transfer from investor → founder

    // PHASE 3: Create Investment PDA (record the transfer)
    const timestamp = Date.now().toString().slice(-8); // Last 8 digits
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    const investmentId = `INV-${timestamp}-${random}`;

    // Program IDs (must be declared before use)
    const investmentProgramId = new PublicKey(
      "FEQJZDk4afcXbSrRj7iW3PieNtrmeT2Hjtt5BCmoNfRr"
    );
    const startupProgramId = new PublicKey(
      "DqwhC5DDZZmL4E1f4YYQJ9R121NurZV8ttk2dfGoYnTj"
    );

    // Find PDAs
    const [investmentPDA] = await PublicKey.findProgramAddress(
      [Buffer.from("investment"), Buffer.from(investmentId)],
      investmentProgramId
    );

    const [startupPDA] = await PublicKey.findProgramAddress(
      [Buffer.from("startup"), Buffer.from(startupId)],
      startupProgramId
    );

    // Instruction discriminator for record_investment: [155, 193, 148, 245, 206, 136, 154, 35]
    const instructionDiscriminator = Buffer.from([
      155, 193, 148, 245, 206, 136, 154, 35,
    ]);

    // Serialize strings (Anchor format: 4 bytes length + UTF-8)
    const serializeString = (str) => {
      const utf8 = Buffer.from(str, "utf-8");
      const len = Buffer.alloc(4);
      len.writeUInt32LE(utf8.length, 0);
      return Buffer.concat([len, utf8]);
    };

    // Serialize u64 (8 bytes little-endian)
    const serializeU64 = (num) => {
      const buf = Buffer.alloc(8);
      // Convert USDC to lamports (1 USDC = 1,000,000 for demo)
      const amount = BigInt(Math.floor(num * 1_000_000));
      buf.writeBigUInt64LE(amount, 0);
      return buf;
    };

    const args = Buffer.concat([
      serializeString(investmentId),
      serializeString(startupId),
      serializeU64(amountUSDC),
    ]);

    const instructionData = Buffer.concat([instructionDiscriminator, args]);

    // Investment record instruction
    const investmentInstruction = new TransactionInstruction({
      keys: [
        {
          pubkey: investmentPDA,
          isSigner: false,
          isWritable: true,
        },
        {
          pubkey: walletKeypair.publicKey,
          isSigner: true,
          isWritable: true,
        },
        {
          pubkey: startupPDA,
          isSigner: false,
          isWritable: false,
        },
        {
          pubkey: SystemProgram.programId,
          isSigner: false,
          isWritable: false,
        },
      ],
      programId: investmentProgramId,
      data: instructionData,
    });

    transaction.add(investmentInstruction);

    // Get recent blockhash and sign transaction
    const { blockhash } = await connection.getLatestBlockhash("confirmed");
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = walletKeypair.publicKey;
    
    // Sign transaction (server wallet signs for both transfer and record)
    // NOTE: In production, investor should sign the USDC transfer
    transaction.sign(walletKeypair);
    
    // Send transaction
    const signature = await connection.sendRawTransaction(
      transaction.serialize(),
      {
        skipPreflight: false,
        maxRetries: 3,
      }
    );

    // Confirm transaction
    await connection.confirmTransaction(signature, "confirmed");

    // Return investment data
    return {
      investmentId,
      transactionSignature: signature,
      usdcTransferSignature: signature, // Same signature (combined transaction)
      confirmationUrl: `https://explorer.solana.com/tx/${signature}?cluster=devnet`,
      blockchainProof: {
        network: "Solana Devnet (TEST - NO REAL MONEY)",
        programId: investmentProgramId.toString(),
        accountAddress: investmentPDA.toString(),
        transactionSignature: signature,
        amountUSDC,
        founderAddress: founderAddress,
        investorAddress: investorAddress,
        usdcMint: TEST_USDC_MINT,
        status: "confirmed",
      },
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error("Error processing investment:", error);
    throw new Error(`Failed to process investment: ${error.message}`);
  }
}

// CLI usage (updated for founder address)
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 4) {
    console.error(
      "Usage: node investUSDC.js <investorAddress> <founderAddress> <startupId> <amountUSDC>"
    );
    process.exit(1);
  }

  investUSDC({
    investorAddress: args[0],
    founderAddress: args[1],
    startupId: args[2],
    amountUSDC: parseFloat(args[3]),
  })
    .then((result) => {
      console.log(JSON.stringify(result, null, 2));
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { investUSDC };
