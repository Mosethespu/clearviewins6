# AI Analytics Setup Guide

## Overview

The ClearView Insurance platform now includes **AI Analytics** - a local AI assistant powered by Ollama and Llama 3.2 3B that helps users analyze their insurance data and get intelligent insights.

## Key Features

✅ **Completely Local** - Runs on your machine, no cloud API needed  
✅ **Privacy-First** - Your data never leaves your computer  
✅ **Role-Specific** - Tailored insights for Admin, Customer, Insurer, and Regulator  
✅ **Context-Aware** - Automatically analyzes your relevant data  
✅ **Chat History** - Saves conversations for future reference  
✅ **Export Functionality** - Download chat history as CSV  

---

## System Requirements

### Hardware Requirements
- **CPU**: Intel i5 or equivalent (i3 will work but slower)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space for Ollama and model
- **GPU**: Not required (uses CPU inference)

### Software Requirements
- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.8+ (already installed for Flask app)
- **curl**: For Ollama installation

---

## Installation Steps

### Step 1: Install Ollama

Ollama is the local LLM runtime that powers our AI analytics.

```bash
# Download and install Ollama (one command)
curl -fsSL https://ollama.com/install.sh | sh
```

This will:
- Download Ollama binary
- Install it to `/usr/local/bin/ollama`
- Set up systemd service (optional)

### Step 2: Start Ollama Service

```bash
# Option A: Run Ollama in the background (recommended)
ollama serve &

# Option B: Run Ollama in a separate terminal
ollama serve
```

**Note**: Keep this running while using AI Analytics. You can add it to your startup applications.

### Step 3: Pull the Llama 3.2 3B Model

```bash
# Download the Llama 3.2 3B model (optimized for your system)
ollama pull llama3.2:3b
```

This will download approximately 2GB of model files. The download may take 5-10 minutes depending on your internet speed.

**Model Details:**
- **Name**: Llama 3.2 3B
- **Size**: ~2GB
- **RAM Usage**: 4-6GB during inference
- **Speed**: 5-15 tokens/second on Intel i5 CPU
- **Quality**: Excellent for analytics and recommendations

### Step 4: Verify Installation

```bash
# Test if Ollama is running
curl http://localhost:11434/api/tags

# You should see a JSON response listing your installed models
```

### Step 5: Install Python Dependencies

```bash
# Navigate to project directory
cd /home/mosethe/Music/clearviewins6

# Activate virtual environment
source venv/bin/activate

# Install requests library (if not already installed)
pip install requests

# Or install from requirements.txt
pip install -r requirements.txt
```

### Step 6: Run Database Migrations

```bash
# Create migration for AIChat model
flask db migrate -m "Add AIChat model for AI analytics"

# Apply migration
flask db upgrade
```

### Step 7: Start the Flask App

```bash
# Start the application
python app.py

# Or with debug mode
flask run --debug
```

---

## Using AI Analytics

### Accessing AI Analytics

1. **Log in** to your ClearView Insurance account
2. Go to your **Dashboard**
3. Click the **"AI Analytics"** button (green button at top of sidebar)

### For Each User Type

#### 🔴 **Admin Users**
- **Access**: Admin Dashboard → AI Analytics
- **Capabilities**:
  - System-wide statistics and trends
  - User management insights
  - Performance analytics
  - Compliance monitoring
  - Operational efficiency recommendations

**Sample Questions:**
- "What are the current system trends?"
- "Show me user activity insights"
- "What areas need improvement?"
- "How many active policies do we have?"
- "What is our claim approval rate?"

---

#### 🔵 **Customer Users**
- **Access**: Customer Dashboard → AI Analytics
- **Capabilities**:
  - Personal policy details and status
  - Claims information
  - Renewal recommendations
  - Coverage optimization tips
  - Cost-saving suggestions

**Sample Questions:**
- "What is my policy status?"
- "Do I have any expiring policies?"
- "What coverage should I consider?"
- "Show me my claims history"
- "How can I reduce my premium?"

---

#### 🟢 **Insurer Users**
- **Access**: Insurer Dashboard → AI Analytics
- **Capabilities**:
  - Policy performance analysis
  - Claims trends and patterns
  - Risk assessment insights
  - Customer behavior analytics
  - Business optimization recommendations

**Sample Questions:**
- "What are my top performing policies?"
- "Show me claims analysis"
- "What are the risk patterns?"
- "How many pending customer requests do I have?"
- "What's my claim approval rate?"

---

#### 🟡 **Regulator Users**
- **Access**: Regulator Dashboard → AI Analytics
- **Capabilities**:
  - Industry compliance metrics
  - Market oversight data
  - Regulatory trend analysis
  - Risk monitoring insights
  - Compliance recommendations

**Sample Questions:**
- "Show compliance overview"
- "What are industry trends?"
- "Any compliance concerns?"
- "How many insurance companies are active?"
- "What's the industry claim rate?"

---

## Features

### 1. **Interactive Chat Interface**
- Real-time responses (5-10 seconds typical)
- Clean, modern UI with message bubbles
- Typing indicator while AI is processing
- Auto-scroll to latest messages

### 2. **Context-Aware Analysis**
The AI automatically has access to:
- Your role and permissions
- Relevant data summary (shown in sidebar)
- Historical context from your session

### 3. **Data Summary Sidebar**
Shows key metrics relevant to your role:
- **Admin**: Total users, policies, claims
- **Customer**: Owned policies, monitored policies, pending requests
- **Insurer**: Company policies, claims, customer requests
- **Regulator**: Insurance companies, compliance metrics

### 4. **Sample Questions**
Quick-start buttons with pre-written questions to help you get started.

### 5. **Chat History**
- All conversations are saved to database
- Review past insights anytime
- Export chat history as CSV

### 6. **Clear History**
- One-click to clear all chat history
- Useful for starting fresh sessions

### 7. **Export Chat**
- Download all conversations as CSV
- Format: Timestamp, Question, Response
- Useful for reports and documentation

---

## Troubleshooting

### Issue: "Ollama is not running"

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# If not running, start it
ollama serve &

# Verify it's accessible
curl http://localhost:11434/api/tags
```

---

### Issue: "Model not found"

**Solution:**
```bash
# List installed models
ollama list

# If llama3.2:3b is not listed, pull it
ollama pull llama3.2:3b

# Verify installation
ollama list | grep llama3.2
```

---

### Issue: Slow responses (>30 seconds)

**Possible Causes & Solutions:**

1. **High system load**
   ```bash
   # Check CPU usage
   top
   
   # Close unnecessary applications
   ```

2. **Insufficient RAM**
   ```bash
   # Check memory usage
   free -h
   
   # Close memory-intensive apps
   # Or upgrade to 16GB RAM
   ```

3. **Model too large**
   ```bash
   # Switch to smaller, faster model
   ollama pull llama3.2:1b
   
   # Update llmservice.py line 11:
   # model: str = "llama3.2:1b"
   ```

---

### Issue: "Unable to connect to Ollama"

**Solution:**
```bash
# Check Ollama port
netstat -tuln | grep 11434

# If port is in use by another service, change Ollama port
OLLAMA_HOST=127.0.0.1:11435 ollama serve &

# Update llmservice.py line 10:
# base_url: str = "http://localhost:11435"
```

---

### Issue: Database migration errors

**Solution:**
```bash
# Reset migrations (CAUTION: Development only)
flask db downgrade
flask db upgrade

# Or recreate database
# CAUTION: This will delete all data
rm instance/clearviewins.db
python app.py
```

---

## Performance Optimization

### For Faster Responses

1. **Use Smaller Model**
   ```bash
   # Install 1B parameter model (2x faster)
   ollama pull llama3.2:1b
   
   # Update llmservice.py to use it
   ```

2. **Close Background Apps**
   - Close browser tabs
   - Stop unnecessary services
   - Free up RAM

3. **Optimize Prompts**
   - Ask specific questions
   - Avoid very long queries
   - One question at a time

### For Better Quality

1. **Use Larger Model (if you have 32GB RAM)**
   ```bash
   ollama pull llama3.1:8b
   
   # Update llmservice.py model parameter
   ```

2. **Provide Context**
   - Be specific in questions
   - Mention relevant policy numbers
   - Include time periods

---

## Advanced Configuration

### Change Model

Edit `/home/mosethe/Music/clearviewins6/llmservice.py`:

```python
# Line 10-11
def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
    # Change model to one of:
    # - "llama3.2:1b" (fastest, 2GB RAM)
    # - "llama3.2:3b" (recommended, 4-6GB RAM)
    # - "llama3.1:8b" (best quality, 16GB+ RAM)
```

### Adjust Temperature

Lower temperature = more focused, deterministic responses  
Higher temperature = more creative, varied responses

```python
# In llmservice.py, line 45-47
"options": {
    "temperature": 0.7,  # Change to 0.3-1.0
    "top_p": 0.9,
    "top_k": 40,
}
```

### Increase Timeout

For slower systems or complex queries:

```python
# In llmservice.py, line 53
timeout=60,  # Change to 120 for 2 minutes
```

---

## Security & Privacy

### Data Privacy
- ✅ **All AI processing happens locally** on your machine
- ✅ **No data is sent to external APIs**
- ✅ **Chat history stored in local database**
- ✅ **No internet connection required** (after initial setup)

### Access Control
- ✅ **Role-based permissions** - Users only see their own data
- ✅ **Login required** - Must be authenticated to access AI
- ✅ **Session-based** - Each user has isolated context

### Best Practices
- 🔒 Don't share your account credentials
- 🔒 Clear chat history after sensitive queries
- 🔒 Export and backup important conversations
- 🔒 Keep Ollama updated for security patches

---

## Updating Ollama & Models

### Update Ollama
```bash
# Download latest version
curl -fsSL https://ollama.com/install.sh | sh

# Restart Ollama service
pkill ollama
ollama serve &
```

### Update Models
```bash
# Pull latest version of model
ollama pull llama3.2:3b

# Verify update
ollama list
```

---

## Alternative Models

If Llama 3.2 3B doesn't work well for you:

### Faster Options (Lower RAM)
```bash
# Llama 3.2 1B - 2GB RAM, very fast
ollama pull llama3.2:1b

# Phi-3 Mini - 2.5GB RAM, fast and accurate
ollama pull phi3:mini
```

### Higher Quality Options (More RAM)
```bash
# Llama 3.1 8B - 16GB+ RAM, best quality
ollama pull llama3.1:8b

# Mixtral 8x7B - 32GB+ RAM, enterprise grade
ollama pull mixtral:8x7b
```

After pulling a new model, update `llmservice.py` line 11 to use it.

---

## Uninstalling

If you need to remove AI Analytics:

### Remove Ollama
```bash
# Stop service
pkill ollama

# Remove binary
sudo rm /usr/local/bin/ollama

# Remove models and data
rm -rf ~/.ollama
```

### Remove from Application
```bash
# Remove AIChat table from database
flask shell
>>> from extension import db
>>> db.drop_table('ai_chat')
>>> exit()

# Remove from codebase
# - Delete llmservice.py
# - Remove AIChat from models.py
# - Remove AI routes from app.py
# - Remove AI Analytics buttons from templates
```

---

## Support & Resources

### Official Ollama Resources
- **Website**: https://ollama.com
- **GitHub**: https://github.com/ollama/ollama
- **Discord**: https://discord.gg/ollama
- **Documentation**: https://github.com/ollama/ollama/tree/main/docs

### Model Information
- **Llama 3.2**: https://ollama.com/library/llama3.2
- **Model Cards**: https://github.com/meta-llama/llama-models

### ClearView Support
- Check `app.py` for route implementations
- Check `llmservice.py` for AI integration logic
- Check `templates/ai_analytics.html` for frontend code

---

## FAQ

**Q: Do I need internet to use AI Analytics?**  
A: Only for initial setup (downloading Ollama and model). After that, it works completely offline.

**Q: How much does this cost?**  
A: $0. Ollama and Llama 3.2 are completely free and open-source.

**Q: Can I use ChatGPT or Claude instead?**  
A: Yes, but you'd need API keys and pay per request. Ollama is free and runs locally.

**Q: Will this slow down my computer?**  
A: During AI queries, it will use ~50-70% CPU for 5-10 seconds. The rest of the time, it uses minimal resources.

**Q: Can multiple users use AI Analytics simultaneously?**  
A: Yes, but responses will be queued and may take longer during concurrent use.

**Q: What if I don't have 16GB RAM?**  
A: Use the 1B model (`llama3.2:1b`) which only needs 4-6GB RAM total.

**Q: Can I use this on Windows or Mac?**  
A: Yes! Ollama supports Windows, Mac, and Linux. Installation steps are similar.

**Q: How accurate is the AI?**  
A: Very accurate for data analysis and recommendations. It uses your actual database data for context.

**Q: Can I customize the AI's personality?**  
A: Yes, edit the system prompt in `llmservice.py` `_build_system_prompt()` method.

---

## Changelog

### Version 1.0 (Initial Release)
- ✅ Ollama integration with Llama 3.2 3B
- ✅ Role-based AI analytics for all user types
- ✅ Context-aware data analysis
- ✅ Chat history storage and export
- ✅ Real-time chat interface
- ✅ Setup instructions and troubleshooting guide

---

**Last Updated**: December 4, 2025  
**Tested On**: Ubuntu 22.04 LTS with Intel i5 and 16GB RAM  
**Status**: Production Ready ✅
