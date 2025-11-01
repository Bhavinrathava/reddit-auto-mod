# Installation Guide

## Quick Install

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/reddit-auto-mod.git
cd reddit-auto-mod

# Install in editable mode
pip install -e .
```

### From PyPI (When Published)

```bash
pip install reddit-auto-mod
```

## Setup

After installation, configure your credentials:

```bash
reddit-auto-mod config
```

This will guide you through setting up:
- Reddit API credentials
- OpenAI API key
- MongoDB connection (optional)

## Verify Installation

Check the installation:

```bash
reddit-auto-mod version
```

View your configuration:

```bash
reddit-auto-mod config --show
```

## Required Credentials

### 1. Reddit API Credentials

1. Visit https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Fill in the form and create the app
5. Note your `client_id` and `client_secret`

### 2. OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy and save it securely

### 3. MongoDB (Optional)

For data persistence, you'll need:
- A MongoDB instance running locally or remotely
- Connection URI (e.g., `mongodb://localhost:27017/`)

## Configuration File Location

Your credentials are stored in:
- **Linux/Mac**: `~/.reddit-auto-mod/config.json`
- **Windows**: `C:\Users\<username>\.reddit-auto-mod\config.json`

The file has restricted permissions (600 on Unix systems) for security.

## System Requirements

- Python 3.8 or higher
- pip package manager
- 2GB+ RAM (for AI models)
- Internet connection

## Dependencies

The package will automatically install:
- praw (Reddit API)
- openai (GPT models)
- fastapi & uvicorn (API servers)
- transformers & torch (Text processing)
- faiss-cpu (Similarity search)
- pymongo (Database)

## Troubleshooting

### Command not found

If `reddit-auto-mod` command is not found, you may need to add Python's Scripts directory to your PATH:

**Windows:**
```
C:\Users\<username>\AppData\Roaming\Python\Python3X\Scripts
```

**Linux/Mac:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Import errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Permission errors on config file

On Unix systems, fix permissions:
```bash
chmod 600 ~/.reddit-auto-mod/config.json
```

## Next Steps

After installation and configuration:

1. Start the backend services (see README.md)
2. Begin using the moderation tools
3. Monitor the queue for processed items

For complete documentation, see [README.md](README.md).
