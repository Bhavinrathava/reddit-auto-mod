# Credentials Flow Documentation

## Overview

The Reddit Auto Mod system uses a **two-step credential management approach**:

1. **User Setup** (One-time): Users manually enter credentials via CLI
2. **Backend Usage** (Automatic): Backend services automatically load credentials from config file

## How It Works

### Step 1: User Configuration (Manual Input)

Users run the CLI configuration command:

```bash
reddit-auto-mod config
```

This launches an **interactive wizard** that prompts for:

1. **Reddit API Credentials**:
   - Client ID (typed manually)
   - Client Secret (typed manually, hidden input)
   - User Agent (typed manually)
   - Username (typed manually)
   - Password (typed manually, hidden input)

2. **OpenAI API Key** (typed manually, hidden input)

3. **MongoDB URI** (optional, typed manually)

**Example Session:**
```
============================================================
Reddit Auto Mod - Configuration Setup
============================================================

This wizard will help you configure your credentials.
All credentials are stored locally in: ~/.reddit-auto-mod/config.json

------------------------------------------------------------
REDDIT API CREDENTIALS
------------------------------------------------------------
You can obtain these from: https://www.reddit.com/prefs/apps

Reddit Client ID: abc123xyz
Reddit Client Secret: ******** (hidden as you type)
Reddit User Agent (e.g., 'MyBot/1.0'): MyModBot/1.0
Reddit Username: my_username
Reddit Password: ******** (hidden as you type)

------------------------------------------------------------
OPENAI API KEY
------------------------------------------------------------
You can obtain this from: https://platform.openai.com/api-keys

OpenAI API Key: ******** (hidden as you type)

------------------------------------------------------------
MONGODB CONNECTION (Optional)
------------------------------------------------------------
Leave blank to skip MongoDB configuration

MongoDB Connection URI: mongodb://localhost:27017/

Saving configuration...

============================================================
✓ Configuration saved successfully!
============================================================
```

### Step 2: Storage (Automatic)

Credentials are **automatically saved** to a secure JSON file:

**Location:**
- **Linux/Mac**: `~/.reddit-auto-mod/config.json`
- **Windows**: `C:\Users\<username>\.reddit-auto-mod\config.json`

**File Permissions:**
- Unix systems: `600` (owner read/write only)
- Windows: Standard user-only permissions

**File Structure:**
```json
{
  "reddit_credentials": {
    "client_id": "abc123xyz",
    "client_secret": "your_secret",
    "user_agent": "MyModBot/1.0",
    "username": "my_username",
    "password": "my_password"
  },
  "openai_api_key": "sk-proj-...",
  "mongodb_uri": "mongodb://localhost:27017/"
}
```

### Step 3: Backend Usage (Automatic Loading)

When backend services start, they **automatically load credentials** from the config file:

#### RedditWrapper Usage:
```python
from cli.config import ConfigManager

config_manager = ConfigManager()
credentials = config_manager.get_reddit_credentials()

# credentials now contains the Reddit API credentials
reddit = RedditWrapper(credentials=credentials, subreddits=["mysubreddit"])
```

#### RuleViolation Service Usage:
```python
from cli.config import ConfigManager

config_manager = ConfigManager()
api_key = config_manager.get_openai_key()

# api_key now contains the OpenAI API key
client = OpenAI(api_key=api_key)
```

#### DataProcessingAPI Usage:
```python
# When called without credentials parameter, loads from config
reddit = initiateRedditObject()  # Loads from config automatically

# OR can still accept manual credentials (for API calls)
reddit = initiateRedditObject(credentials=manual_creds)
```

## Credential Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: User Configuration (One-time Setup)            │
│  Command: reddit-auto-mod config                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ User manually types credentials
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Interactive Prompts:                                    │
│  - Reddit Client ID: _______                            │
│  - Reddit Client Secret: ********                       │
│  - Reddit User Agent: _______                           │
│  - Reddit Username: _______                             │
│  - Reddit Password: ********                            │
│  - OpenAI API Key: ********                             │
│  - MongoDB URI: _______                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Saves automatically
                  ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Secure Storage                                 │
│  File: ~/.reddit-auto-mod/config.json                   │
│  Permissions: 600 (owner only)                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Backend services read from here
                  ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Automatic Loading by Backend Services          │
│                                                          │
│  ┌────────────────┐  ┌──────────────────────┐          │
│  │ RedditWrapper  │  │  RuleViolation API   │          │
│  │ Loads Reddit   │  │  Loads OpenAI Key    │          │
│  │ credentials    │  │  from config         │          │
│  └────────────────┘  └──────────────────────┘          │
│                                                          │
│  ┌────────────────────────────────────────┐            │
│  │  DataProcessingAPI                     │            │
│  │  Loads credentials for orchestration   │            │
│  └────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## No Manual File Editing Required

**Key Point**: Users **DO NOT** need to manually create or edit the config file. The CLI handles everything:

1. ✅ Creates the directory if it doesn't exist
2. ✅ Creates the config file
3. ✅ Sets proper permissions
4. ✅ Validates and saves credentials
5. ✅ Provides feedback on success/failure

## Managing Credentials

### View Configuration (with sensitive data masked):
```bash
reddit-auto-mod config --show
```

Output:
```
============================================================
Current Configuration
============================================================

Reddit Credentials:
  Client ID: cF0iy7hJ...
  Client Secret: ********...
  User Agent: MyBot/1.0
  Username: my_username
  Password: ********

OpenAI API Key: sk-proj-...xyz

MongoDB URI: mongodb://localhost:27017/

Config file location: /home/user/.reddit-auto-mod/config.json
```

### Update Configuration:
```bash
# Run config again to overwrite
reddit-auto-mod config
```

You'll be asked: "Configuration already exists. Do you want to overwrite it? (y/n)"

### Clear Configuration:
```bash
reddit-auto-mod config --clear
```

This permanently deletes the config file.

## Security Features

1. **Hidden Input**: Passwords and API keys are hidden while typing (using `getpass`)
2. **Restricted Permissions**: Config file has 600 permissions on Unix systems
3. **Local Storage**: Credentials stored locally on user's machine, not in cloud
4. **No Version Control**: Config file path excluded from git (in `.gitignore`)
5. **Fallback to Environment Variables**: Services can fall back to env vars if config missing

## Fallback Mechanism
