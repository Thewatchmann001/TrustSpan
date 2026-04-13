#!/bin/bash

# TrustSpan SL - Environment Setup Script
# This script helps set up the development environment

echo "🚀 TrustSpan SL - Blockchain Setup"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# Solana Configuration
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com

# Wallet Configuration
# Path to your Solana wallet keypair file
# Default: ~/.config/solana/id.json
WALLET_PATH=~/.config/solana/id.json

# Program IDs (will be set after deployment)
CERTIFICATE_REGISTRY_PROGRAM_ID=CertReg1111111111111111111111111111111
STARTUP_REGISTRY_PROGRAM_ID=StartReg1111111111111111111111111111111
INVESTMENT_LEDGER_PROGRAM_ID=InvLedg1111111111111111111111111111111

# API Configuration (if needed)
API_PORT=3000
API_ENV=development
EOF
    echo "✅ .env file created!"
else
    echo "ℹ️  .env file already exists"
fi

# Check Solana CLI
if command -v solana &> /dev/null; then
    echo "✅ Solana CLI found"
    solana --version
else
    echo "❌ Solana CLI not found. Please install it first."
    echo "   Visit: https://docs.solana.com/cli/install-solana-cli-tools"
fi

# Check Anchor
if command -v anchor &> /dev/null; then
    echo "✅ Anchor found"
    anchor --version
else
    echo "❌ Anchor not found. Please install it first."
    echo "   Run: cargo install --git https://github.com/coral-xyz/anchor avm --locked --force"
fi

# Check Rust
if command -v rustc &> /dev/null; then
    echo "✅ Rust found"
    rustc --version
else
    echo "❌ Rust not found. Please install it first."
    echo "   Visit: https://rustup.rs/"
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js found"
    node --version
else
    echo "❌ Node.js not found. Please install it first."
    echo "   Visit: https://nodejs.org/"
fi

echo ""
echo "📦 Installing Node.js dependencies..."
npm install

echo ""
echo "🎯 Setup complete! Next steps:"
echo "1. Configure Solana: solana config set --url devnet"
echo "2. Create wallet: solana-keygen new (if needed)"
echo "3. Airdrop SOL: solana airdrop 2 \$(solana address)"
echo "4. Build programs: anchor build"
echo "5. Deploy: anchor deploy --provider.cluster devnet"

