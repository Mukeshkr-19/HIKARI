#!/bin/bash
# HIKARI v2.0 - Setup Script
# Installs all dependencies and configures the environment

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          HIKARI v2.0 - Setup Script                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Install macOS-specific deps
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS dependencies..."
    brew install portaudio 2>/dev/null || echo "PortAudio already installed or brew not available"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and add your API keys!"
    echo "At minimum, set GOOGLE_AI_STUDIO_KEY or GROQ_API_KEY"
    echo ""
fi

# Create data directory
mkdir -p data

# Install frontend deps
if [ -d "hikari-frontend" ]; then
    echo "Installing frontend dependencies..."
    cd hikari-frontend
    npm install
    cd ..
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Setup complete!                                         ║"
echo "║                                                          ║"
echo "║  Next steps:                                             ║"
echo "║  1. Edit .env and add your API keys                      ║"
echo "║  2. Run: source .venv/bin/activate                       ║"
echo "║  3. Run: python3 hikari.py --text                        ║"
echo "║                                                          ║"
echo "║  Get free API keys:                                      ║"
echo "║  - Google: https://aistudio.google.com                   ║"
echo "║  - Groq: https://console.groq.com                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
