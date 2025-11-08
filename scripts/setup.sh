#!/bin/bash

# CV-RAG System Setup Script
# This script sets up the Python environment and installs dependencies

set -e  # Exit on error

echo "🚀 CV-RAG System Setup"
echo "======================"
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Python 3.8+ is available
required_version="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Error: Python 3.8 or higher is required"
    echo "   Your version: $python_version"
    exit 1
fi
echo "✅ Python version OK"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
echo "This might take a few minutes (downloading PyTorch and models)..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo "⚙️  Setting up environment variables..."
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists, skipping..."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created from .env.example"
        echo "   ⚠️  IMPORTANT: Edit .env and add your FLOWCASE_API_KEY"
    else
        echo "⚠️  .env.example not found, creating basic .env file..."
        cat > .env << EOF
# Flowcase API Configuration
FLOWCASE_API_KEY=your_api_key_here
FLOWCASE_API_URL=https://bekk.flowcase.com/api
EOF
        echo "✅ Basic .env file created"
        echo "   ⚠️  IMPORTANT: Edit .env and add your FLOWCASE_API_KEY"
    fi
fi
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/cvs
mkdir -p data/chromadb
echo "✅ Data directories created"
echo ""

# Test imports
echo "🧪 Testing imports..."
python3 << EOF
try:
    import chromadb
    import sentence_transformers
    import torch
    print("✅ All core libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF
echo ""

# Download embedding model
echo "🤖 Downloading embedding model (this happens only once)..."
python3 << EOF
from sentence_transformers import SentenceTransformer
import config

print(f"Downloading model: {config.EMBEDDING_MODEL}")
try:
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    print("✅ Model downloaded and cached successfully")
    print(f"   Model dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    print(f"❌ Error downloading model: {e}")
    exit(1)
EOF
echo ""

# Print next steps
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "==========="
echo "1. Edit .env file and add your FLOWCASE_API_KEY:"
echo "   nano .env  # or use your preferred editor"
echo ""
echo "2. (Optional) Set up MCP configuration for Claude Desktop / ChatGPT Desktop:"
echo "   python scripts/setup_mcp.py"
echo ""
echo "3. Synkroniser CVer fra Flowcase:"
echo "   ./sync.sh --full"
echo ""
echo "4. Restart Claude Desktop / ChatGPT Desktop (if you set up MCP)"
echo ""
echo "For more information, see README.md"



