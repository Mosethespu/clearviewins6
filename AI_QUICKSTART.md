# 🤖 AI Analytics - Quick Start Guide

## What You Have Now

Your ClearView Insurance application now has **AI Analytics** powered by a local LLM! Each user type (Admin, Customer, Insurer, Regulator) can ask questions and get intelligent insights about their data.

## ⚡ Quick Setup (3 Steps)

### Step 1: Install Ollama (One-time setup)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Step 2: Download the AI Model

```bash
# Download Llama 3.2 3B (optimized for your i5 16GB system)
ollama pull llama3.2:3b

# This will download ~2GB and take 2-5 minutes
```

### Step 3: Start Ollama Server

```bash
# In a separate terminal, start Ollama
ollama serve

# Keep this running while using the app
```

## 🧪 Test Your Setup

```bash
# Activate your virtual environment
source venv/bin/activate

# Run the test script
python test_ollama.py

# You should see all green checkmarks ✅
```

## 🚀 Start Using AI Analytics

### 1. Start Your Flask App

```bash
# Make sure Ollama is running in another terminal!
source venv/bin/activate
flask run
```

### 2. Access the Feature

1. Login to your dashboard (Admin, Customer, Insurer, or Regulator)
2. Look for the **🤖 AI Analytics** button in the sidebar
3. Click it to open the chat interface
4. Start asking questions!

## 💬 Example Questions You Can Ask

### For Admins:
- "What's the overall health of the insurance system?"
- "Are there any concerning trends in claims?"
- "Which areas need attention based on the data?"
- "Provide insights on user growth patterns"

### For Customers:
- "When should I renew my policies?"
- "Do I have any claims pending?"
- "What's the status of my insurance coverage?"
- "Should I be concerned about any expiring policies?"

### For Insurers:
- "What's our claims approval rate?"
- "Are there patterns in recent claims?"
- "Which policies need attention?"
- "Provide insights on customer requests"

### For Regulators:
- "Are there any compliance concerns?"
- "What trends do you see in the industry?"
- "Highlight any unusual patterns"
- "Provide an overview of market health"

## 🔧 Troubleshooting

### "Ollama is not running"
**Solution:** Start Ollama in another terminal:
```bash
ollama serve
```

### "Model not found"
**Solution:** Pull the model:
```bash
ollama pull llama3.2:3b
```

### Slow Responses
**Solution:** This is normal for CPU inference. Expect 5-15 seconds per response.
- Shorter questions = faster responses
- The first query is slowest (model loading)
- Subsequent queries are faster

### High RAM Usage
**Solution:** The model uses 4-6GB RAM when loaded. This is normal.
- Close other applications if needed
- Model unloads automatically when idle

## 📊 Features

✅ **Context-Aware**: AI knows your role and your data  
✅ **Chat History**: Previous conversations are saved  
✅ **Real Data**: AI analyzes actual database information  
✅ **Privacy**: Everything runs locally - no data leaves your machine  
✅ **Role-Specific**: Different insights for Admin/Customer/Insurer/Regulator  

## 🔒 Privacy & Security

- **100% Local**: No data sent to external servers
- **Offline**: Works without internet connection
- **Secure**: All processing happens on your machine
- **Logged**: Chats are saved in your database for audit

## ⚙️ Advanced Configuration

### Change the Model

Edit `llmservice.py` line 13:
```python
def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
```

Available models for your system:
- `llama3.2:1b` - Fastest, lower quality
- `llama3.2:3b` - **Recommended** - Balanced
- `llama3.1:8b` - Slower, better quality (if you have GPU)

### Disable Chat History

In `app.py`, comment out the chat saving lines in the `/api/ai-chat` route.

### Change Temperature (Creativity)

In `llmservice.py`, adjust the `temperature` value (0.0 = precise, 1.0 = creative):
```python
"temperature": 0.7,  # Current setting
```

## 📝 System Requirements Met ✅

Your system is perfect for this:
- ✅ Intel i5 CPU - Handles Llama 3.2 3B well
- ✅ 16GB RAM - Plenty for model (uses 4-6GB)
- ✅ Integrated Graphics - Not needed, runs on CPU
- ✅ Estimated Performance: 5-15 tokens/second

## 🆘 Need Help?

1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. Run the test script: `python test_ollama.py`
3. Check Flask logs for errors
4. Verify model is pulled: `ollama list`

## 📚 Additional Resources

- Ollama Documentation: https://ollama.com/docs
- Available Models: https://ollama.com/library
- Llama 3.2 Info: https://ollama.com/library/llama3.2

---

**Ready to go?** Run these commands:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Flask
cd /home/mosethe/Music/clearviewins6
source venv/bin/activate
flask run

# Open browser: http://localhost:5000
# Login and click "AI Analytics"! 🎉
```
