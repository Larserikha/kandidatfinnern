#!/bin/bash
#
# Setup CV-RAG alias for easy syncing
# Run this once: ./setup-alias.sh
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SHELL_RC="$HOME/.zshrc"

echo "🔧 Setting up CV-RAG shortcut..."
echo ""

# Check if alias already exists
if grep -q "alias sync-cv=" "$SHELL_RC" 2>/dev/null; then
    echo "✅ Alias 'sync-cv' already exists in $SHELL_RC"
else
    # Add alias to shell config
    echo "" >> "$SHELL_RC"
    echo "# CV-RAG System - Auto-generated alias" >> "$SHELL_RC"
    echo "alias sync-cv='cd $SCRIPT_DIR && ./sync.sh && cd -'" >> "$SHELL_RC"
    echo "✅ Added alias 'sync-cv' to $SHELL_RC"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use now, run:"
echo "  source ~/.zshrc"
echo ""
echo "Then from any directory, just type:"
echo "  sync-cv"
echo ""
echo "This will:"
echo "  1. Download updated CVs from Flowcase"
echo "  2. Re-index automatically"
echo "  3. Return you to your current directory"
echo ""

