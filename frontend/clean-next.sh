#!/bin/bash
echo "🧹 Cleaning Next.js cache and node_modules..."
rm -rf .next
rm -rf node_modules/.cache
echo "✅ Cache cleared!"
echo ""
echo "If issues persist, you can also run:"
echo "  npm run dev -- --turbo  (if using Turbopack)"
