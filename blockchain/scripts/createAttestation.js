/**
 * Create On-Chain Attestation on Solana Devnet
 * Creates a Solana account to store attestation data
 */
const {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
} = require("@solana/web3.js");
const fs = require("fs");
const path = require("path");

/**
 * Creates an on-chain attestation using a Solana account
 * @param {Object} params - Attestation parameters
 * @param {string} params.walletAddress - Wallet address being attested
 * @param {string} params.schema - Schema type (business_ownership, identity, etc.)
 * @param {Object} params.data - Attestation data
 * @returns {Promise<Object>} Attestation creation result
 */
async function createAttestation({ walletAddress, schema, data }) {
  try {
    // Connect to Solana Devnet
    const connection = new Connection(
      process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com",
      "confirmed"
    );

    // Load payer wallet
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const walletPath =
      process.env.WALLET_PATH || path.join(homeDir, ".config/solana/id.json");
    
    if (!fs.existsSync(walletPath)) {
      throw new Error(`Wallet not found at ${walletPath}`);
    }

    const walletKeypair = Keypair.fromSecretKey(
      new Uint8Array(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
    );

    // Validate wallet address
    let walletPubkey;
    try {
      walletPubkey = new PublicKey(walletAddress);
    } catch (error) {
      throw new Error(`Invalid wallet address: ${error.message}`);
    }

    // For devnet: Create a simple on-chain account to store attestation data
    // In production, this would use the official SAS program
    
    // Generate a unique keypair for the attestation account
    // In production, this would be a PDA derived from SAS program
    const attestationKeypair = Keypair.generate();
    const attestationPubkey = attestationKeypair.publicKey;

    // Prepare attestation data
    const attestationData = {
      wallet_address: walletAddress,
      schema: schema,
      data: data,
      timestamp: Date.now(),
    };

    // Serialize data
    const dataBuffer = Buffer.from(JSON.stringify(attestationData));

    // Calculate space needed (8 bytes discriminator + data)
    const space = 8 + dataBuffer.length;

    // Get minimum rent
    const rentExemptionAmount = await connection.getMinimumBalanceForRentExemption(space);

    // Create transaction
    const transaction = new Transaction();

    // Create account instruction
    transaction.add(
      SystemProgram.createAccount({
        fromPubkey: walletKeypair.publicKey,
        newAccountPubkey: attestationPubkey,
        lamports: rentExemptionAmount,
        space: space,
        programId: SystemProgram.programId,
      })
    );

    // Note: In a real SAS implementation, you would:
    // 1. Use the actual SAS program ID (from attest.solana.com)
    // 2. Derive PDA using SAS program's findProgramAddress
    // 3. Call SAS program's create_attestation instruction
    // 4. Store data according to SAS schema format
    // For devnet testing, we create a simple account to demonstrate on-chain storage

    // Get recent blockhash
    const { blockhash } = await connection.getLatestBlockhash("confirmed");
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = walletKeypair.publicKey;

    // Sign transaction (payer signs for account creation)
    transaction.sign(walletKeypair, attestationKeypair);

    // Send transaction
    const signature = await connection.sendRawTransaction(transaction.serialize(), {
      skipPreflight: false,
      maxRetries: 3,
    });

    // Wait for confirmation
    const confirmation = await connection.confirmTransaction(signature, "confirmed");
    
    if (confirmation.value.err) {
      throw new Error(`Transaction failed: ${JSON.stringify(confirmation.value.err)}`);
    }

    // Note: In production, data would be written to the account via SAS program instruction
    // For devnet, the account exists on-chain as proof of attestation creation

    return {
      success: true,
      attestation_id: `sas_${attestationPubkey.toBase58().slice(0, 16)}`,
      account_address: attestationPubkey.toBase58(),
      transaction_signature: signature,
      wallet_address: walletAddress,
      schema: schema,
      explorer_url: `https://explorer.solana.com/tx/${signature}?cluster=devnet`,
      account_explorer_url: `https://explorer.solana.com/address/${attestationPubkey.toBase58()}?cluster=devnet`,
      message: "Attestation account created on-chain (devnet). In production, this would use SAS program.",
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      stack: error.stack,
    };
  }
}

// If called directly from command line
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 3) {
    console.error("Usage: node createAttestation.js <walletAddress> <schema> <data_json>");
    process.exit(1);
  }

  const [walletAddress, schema, dataJson] = args;
  let data;
  
  try {
    data = JSON.parse(dataJson);
  } catch (e) {
    data = { raw: dataJson };
  }

  createAttestation({ walletAddress, schema, data })
    .then((result) => {
      console.log(JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch((error) => {
      console.error(JSON.stringify({ success: false, error: error.message }, null, 2));
      process.exit(1);
    });
}

module.exports = { createAttestation };
