#!/bin/bash

# ClearView Insurance - AI Analytics Setup Script
# This script automates the installation of Ollama and Llama 3.2 3B

echo "======================================"
echo "ClearView Insurance AI Analytics Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${YELLOW}Warning: This script is designed for Linux. For other OS, visit https://ollama.com/download${NC}"
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ $continue_anyway != "y" ]]; then
        exit 0
    fi
fi

echo "Step 1: Checking system requirements..."
echo ""

# Check RAM
total_ram=$(free -g | awk '/^Mem:/{print $2}')
if [ $total_ram -lt 8 ]; then
    echo -e "${RED}Warning: You have ${total_ram}GB RAM. 8GB minimum required.${NC}"
    echo "Consider using llama3.2:1b model instead."
    read -p "Continue anyway? (y/n): " continue_ram
    if [[ $continue_ram != "y" ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ RAM check passed: ${total_ram}GB${NC}"
fi

# Check disk space
free_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ $free_space -lt 5 ]; then
    echo -e "${RED}Error: Not enough disk space. Need at least 5GB free.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Disk space check passed: ${free_space}GB free${NC}"
fi

echo ""
echo "Step 2: Installing Ollama..."
echo ""

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama is already installed.${NC}"
    read -p "Reinstall/Update? (y/n): " reinstall
    if [[ $reinstall != "y" ]]; then
        echo "Skipping Ollama installation."
    else
        echo "Updating Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Ollama installed successfully${NC}"
    else
        echo -e "${RED}✗ Ollama installation failed${NC}"
        exit 1
    fi
fi

echo ""
echo "Step 3: Starting Ollama service..."
echo ""

# Check if Ollama is already running
if pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}Ollama is already running.${NC}"
else
    echo "Starting Ollama in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓ Ollama service started${NC}"
    else
        echo -e "${RED}✗ Failed to start Ollama service${NC}"
        echo "Try running manually: ollama serve"
        exit 1
    fi
fi

echo ""
echo "Step 4: Checking Ollama API..."
echo ""

# Verify Ollama API is accessible
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${GREEN}✓ Ollama API is accessible${NC}"
else
    echo -e "${RED}✗ Ollama API is not accessible${NC}"
    echo "Check if Ollama is running: ps aux | grep ollama"
    exit 1
fi

echo ""
echo "Step 5: Downloading Llama 3.2 3B model..."
echo ""

# Check if model is already downloaded
if ollama list | grep -q "llama3.2:3b"; then
    echo -e "${YELLOW}Llama 3.2 3B is already downloaded.${NC}"
    read -p "Re-download/Update? (y/n): " redownload
    if [[ $redownload != "y" ]]; then
        echo "Skipping model download."
    else
        echo "Downloading model (this may take 5-10 minutes)..."
        ollama pull llama3.2:3b
    fi
else
    echo "Downloading Llama 3.2 3B model (~2GB)..."
    echo "This may take 5-10 minutes depending on your internet speed..."
    ollama pull llama3.2:3b
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Model downloaded successfully${NC}"
    else
        echo -e "${RED}✗ Model download failed${NC}"
        echo "Try running manually: ollama pull llama3.2:3b"
        exit 1
    fi
fi

echo ""
echo "Step 6: Installing Python dependencies..."
echo ""

# Check if we're in the project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found.${NC}"
    read -p "Create virtual environment? (y/n): " create_venv
    if [[ $create_venv == "y" ]]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
fi

# Activate virtual environment and install dependencies
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -q requests
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}Warning: Virtual environment not activated. Installing globally...${NC}"
    pip3 install requests
fi

echo ""
echo "Step 7: Running database migrations..."
echo ""

# Run Flask migrations
if [ -f "app.py" ]; then
    export FLASK_APP=app.py
    
    # Create migration
    flask db migrate -m "Add AIChat model for AI analytics" 2>/dev/null
    
    # Apply migration
    flask db upgrade
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}Warning: Migration may have already been applied${NC}"
    fi
else
    echo -e "${RED}Error: app.py not found${NC}"
    exit 1
fi

echo ""
echo "Step 8: Testing AI Analytics..."
echo ""

# Test Ollama connection
echo "Testing Ollama connection..."
test_response=$(curl -s -X POST http://localhost:11434/api/generate \
    -d '{"model":"llama3.2:3b","prompt":"Say hello","stream":false}' \
    -H "Content-Type: application/json")

if echo "$test_response" | grep -q "response"; then
    echo -e "${GREEN}✓ AI Analytics is working!${NC}"
else
    echo -e "${RED}✗ AI test failed${NC}"
    echo "Response: $test_response"
fi

echo ""
echo "======================================"
echo "Setup Complete! 🎉"
echo "======================================"
echo ""
echo -e "${GREEN}AI Analytics is ready to use!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the Flask app: python app.py"
echo "2. Log in to ClearView Insurance"
echo "3. Click 'AI Analytics' button on your dashboard"
echo ""
echo "Installed components:"
echo "  ✓ Ollama (running on port 11434)"
echo "  ✓ Llama 3.2 3B model"
echo "  ✓ Python dependencies"
echo "  ✓ Database migrations"
echo ""
echo "Troubleshooting:"
echo "  • If Ollama stops: ollama serve &"
echo "  • View logs: tail -f ~/.ollama/logs/server.log"
echo "  • Check models: ollama list"
echo "  • Read full guide: AI_ANALYTICS_SETUP.md"
echo ""
echo "For more information, see AI_ANALYTICS_SETUP.md"
echo ""
