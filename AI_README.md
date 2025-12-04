# 🤖 AI Analytics - Quick Start

## What is this?

AI Analytics is a **local AI assistant** that helps you analyze your insurance data and get intelligent insights. It runs completely on your machine using **Ollama** and **Llama 3.2 3B**.

## ✨ Features

- 💬 **Interactive Chat** - Ask questions in natural language
- 🎯 **Role-Specific** - Tailored for Admin, Customer, Insurer, Regulator
- 🔒 **100% Private** - All data stays on your machine
- 📊 **Context-Aware** - Automatically analyzes your relevant data
- 💾 **Chat History** - Save and export conversations
- 🚀 **Fast** - 5-15 seconds per response on Intel i5

## 🚀 Quick Setup (2 minutes)

```bash
# Run the automated setup script
./setup_ai_analytics.sh
```

That's it! The script will:
1. ✅ Install Ollama
2. ✅ Download Llama 3.2 3B model
3. ✅ Set up Python dependencies
4. ✅ Run database migrations
5. ✅ Test the AI connection

## 📖 Manual Setup

If you prefer manual installation, see **[AI_ANALYTICS_SETUP.md](AI_ANALYTICS_SETUP.md)** for detailed instructions.

## 🎯 How to Use

1. **Log in** to ClearView Insurance
2. Go to your **Dashboard**
3. Click **"AI Analytics"** button (green button at top of sidebar)
4. Start asking questions!

### Example Questions

**For Customers:**
- "What is my policy status?"
- "Do I have any expiring policies?"
- "What coverage should I consider?"

**For Insurers:**
- "What are my top performing policies?"
- "Show me claims analysis"
- "What are the risk patterns?"

**For Admins:**
- "What are the current system trends?"
- "Show me user activity insights"
- "What areas need improvement?"

**For Regulators:**
- "Show compliance overview"
- "What are industry trends?"
- "Any compliance concerns?"

## 💻 System Requirements

- **CPU**: Intel i5 or equivalent (your system ✅)
- **RAM**: 16GB (your system ✅)
- **Storage**: 5GB free space
- **GPU**: Not required (uses CPU)

## 🔧 Troubleshooting

### AI is offline?

```bash
# Start Ollama
ollama serve &

# Check if running
curl http://localhost:11434/api/tags
```

### Slow responses?

```bash
# Use faster 1B model
ollama pull llama3.2:1b

# Then update llmservice.py line 11:
# model: str = "llama3.2:1b"
```

## 📚 Documentation

- **Full Setup Guide**: [AI_ANALYTICS_SETUP.md](AI_ANALYTICS_SETUP.md)
- **Ollama Docs**: https://ollama.com
- **Llama 3.2 Info**: https://ollama.com/library/llama3.2

## 🆘 Need Help?

Check the comprehensive guide: **AI_ANALYTICS_SETUP.md**

It includes:
- Detailed installation steps
- Performance optimization tips
- Advanced configuration
- Complete troubleshooting guide
- FAQ section

## 🎉 You're Ready!

Start exploring your insurance data with AI-powered insights!

---

**Last Updated**: December 4, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
