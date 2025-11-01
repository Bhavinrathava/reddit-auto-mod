# Configuration File Guide

This guide explains how to use configuration files with Reddit Auto Mod.

## Overview

Reddit Auto Mod supports two ways to configure credentials:

1. **Interactive Wizard**: `reddit-auto-mod config` (prompts for each credential)
2. **Config File Import**: `reddit-auto-mod config --file path/to/config.json` (import from JSON file)

## Configuration File Template

A template configuration file is provided: `config.template.json`

```json
{
  "reddit_credentials": {
    "client_id": "YOUR_REDDIT_CLIENT_ID",
    "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
    "user_agent": "YourBotName/1.0 (by /u/yourusername)",
    "username": "YOUR_REDDIT_USERNAME",
    "password": "YOUR_REDDIT_PASSWORD"
  },
  "openai_api_key": "sk-proj-YOUR_OPENAI_API_KEY_HERE",
  "mongodb_uri": "mongodb://localhost:27017/",
  "mongodb_cert_path": "/path/to/your/certificate.pem",
  "database_name": "mainDB",
  "subreddits": [
    "subreddit1",
    "subreddit2"
  ]
}
```

## Creating Your Config File

### Method 1: Copy the Template

```bash
# Copy the template
cp config.template.json my_config.json

# Edit with your credentials
nano my_config.json  # or use your preferred editor

# Import the config
reddit-auto-mod config --file my_config.json
```

### Method 2: Create from Scratch

Create a file called `my_config.json`:

```json
{
  "reddit_credentials": {
    "client_id": "abc123xyz",
    "client_secret": "def456uvw",
    "user_agent": "MyModBot/1.0 (by /u/myusername)",
    "username": "myusername",
    "password": "mypassword"
  },
  "openai_api_key": "sk-proj-abcdefghijklmnop",
  "mongodb_uri": "mongodb://localhost:27017/"
}
```

Then import it:

```bash
reddit-auto-mod config --file my_config.json
```

## Required Fields

### Minimum Required Configuration

```json
{
  "reddit_credentials": {
    "client_id": "required",
    "client_secret": "required",
    "user_agent": "required",
    "username": "required",
    "password": "required"
  },
  "openai_api_key": "required"
}
```

### Optional Fields

```json
{
  "mongodb_uri": "optional - only if using MongoDB",
  "mongodb_cert_path": "optional - only for X.509 authentication",
  "database_name": "optional - defaults to 'mainDB'",
  "subreddits": "optional - can be set later via setup command"
}
```

## Field Descriptions

### reddit_credentials

- **client_id**: Your Reddit app's client ID (get from https://www.reddit.com/prefs/apps)
- **client_secret**: Your Reddit app's client secret
- **user_agent**: User agent string (format: `AppName/Version (by /u/username)`)
- **username**: Your Reddit username
- **password**: Your Reddit account password

### openai_api_key

- Your OpenAI API key (get from https://platform.openai.com/api-keys)
- Format: `sk-proj-...`

### mongodb_uri

- MongoDB connection string
- Examples:
  - Local: `mongodb://localhost:27017/`
  - Atlas: `mongodb+srv://username:password@cluster.mongodb.net/`
  - X.509: `mongodb+srv://X509:@cluster.mongodb.net/?authMechanism=MONGODB-X509`

### mongodb_cert_path

- Path to X.509 certificate file for MongoDB authentication
- Only needed if using X.509 authentication
- Supports `~` for home directory
- Example: `~/certificates/mongodb-cert.pem`

### database_name

- Name of the MongoDB database to use
- Default: `mainDB`

### subreddits

- Array of subreddit names to moderate
- Can also be configured via `reddit-auto-mod setup`
- Example: `["AskReddit", "funny", "pics"]`

## Usage Examples

### Example 1: Basic Configuration

```json
{
  "reddit_credentials": {
    "client_id": "abc123",
    "client_secret": "secret456",
    "user_agent": "TestBot/1.0 (by /u/testuser)",
    "username": "testuser",
    "password": "mypassword"
  },
  "openai_api_key": "sk-proj-xyz789"
}
```

Import:
```bash
reddit-auto-mod config --file basic_config.json
```

### Example 2: With MongoDB (Local)

```json
{
  "reddit_credentials": {
    "client_id": "abc123",
    "client_secret": "secret456",
    "user_agent": "ModBot/1.0 (by /u/moduser)",
    "username": "moduser",
    "password": "securepass"
  },
  "openai_api_key": "sk-proj-key123",
  "mongodb_uri": "mongodb://localhost:27017/",
  "database_name": "reddit_moderation"
}
```

### Example 3: With MongoDB Atlas (X.509 Auth)

```json
{
  "reddit_credentials": {
    "client_id": "abc123",
    "client_secret": "secret456",
    "user_agent": "ProdBot/1.0 (by /u/produser)",
    "username": "produser",
    "password": "prodpass"
  },
  "openai_api_key": "sk-proj-prodkey",
  "mongodb_uri": "mongodb+srv://X509:@cluster.mongodb.net/?authMechanism=MONGODB-X509",
  "mongodb_cert_path": "~/certs/mongodb-cert.pem",
  "database_name": "production_db"
}
```

### Example 4: Complete Configuration

```json
{
  "reddit_credentials": {
    "client_id": "myapp123",
    "client_secret": "appsecret456",
    "user_agent": "AutoMod/2.0 (by /u/moderator)",
    "username": "moderator",
    "password": "strongpassword"
  },
  "openai_api_key": "sk-proj-completekeysample",
  "mongodb_uri": "mongodb+srv://user:pass@cluster.mongodb.net/",
  "database_name": "automod_production",
  "subreddits": [
    "technology",
    "programming",
    "python"
  ]
}
```

## Security Best Practices

### 1. File Permissions

Set restrictive permissions on your config file:

```bash
# Unix/Linux/Mac
chmod 600 my_config.json

# This allows only the owner to read/write
```

### 2. Never Commit to Version Control

Add to `.gitignore`:

```gitignore
# Config files with credentials
*config.json
!config.template.json  # Keep template in repo
*.pem
*.key
```

### 3. Use Environment-Specific Files

Keep separate config files for different environments:

```
configs/
├── dev_config.json
├── staging_config.json
└── prod_config.json
```

### 4. Encrypt Sensitive Files

Consider encrypting your config files:

```bash
# Encrypt
gpg -c my_config.json

# Decrypt when needed
gpg my_config.json.gpg

# Then import
reddit-auto-mod config --file my_config.json
```

## Troubleshooting

### "Config file not found"

```bash
# Check the file path
ls -l path/to/config.json

# Use absolute path
reddit-auto-mod config --file /full/path/to/config.json

# Or use ~ for home directory
reddit-auto-mod config --file ~/configs/my_config.json
```

### "Invalid JSON"

Validate your JSON:

```bash
# Using jq
jq . my_config.json

# Using Python
python -m json.tool my_config.json
```

### "Missing required field"

Ensure all required fields are present:
- `reddit_credentials.client_id`
- `reddit_credentials.client_secret`
- `reddit_credentials.user_agent`
- `reddit_credentials.username`
- `reddit_credentials.password`
- `openai_api_key`

### "Configuration already exists"

The import will prompt you:
```
Configuration already exists. Do you want to overwrite it? (y/n):
```

Type `y` to overwrite or `n` to cancel.

## Where Config is Stored

After import, config is stored at:
- **Linux/Mac**: `~/.reddit-auto-mod/config.json`
- **Windows**: `C:\Users\<username>\.reddit-auto-mod\config.json`

View it with:
```bash
reddit-auto-mod config --show
```

## Comparison: Interactive vs File Import

### Interactive Wizard
```bash
reddit-auto-mod config
```

**Pros:**
- Guided step-by-step
- Password hidden when typing
- Helpful prompts and urls

**Cons:**
- Must type everything
- No easy way to reuse config
- Slower for repeat setups

### File Import
```bash
reddit-auto-mod config --file my_config.json
```

**Pros:**
- Fast import
- Reusable across environments
- Easy to version control (with care)
- Can be automated

**Cons:**
- Must create JSON file first
- Passwords visible in file
- Need to ensure valid JSON

## Advanced Usage

### Automated Deployment

```bash
#!/bin/bash
# deploy.sh

# Import config
reddit-auto-mod config --file /secure/configs/prod_config.json

# Run setup
reddit-auto-mod setup --status

# Start services
reddit-auto-mod start
```

### Config Templates for Teams

Create team templates:

```json
{
  "reddit_credentials": {
    "client_id": "TEAM_SHARED_CLIENT_ID",
    "client_secret": "REPLACE_WITH_YOUR_SECRET",
    "user_agent": "TeamBot/1.0 (by /u/REPLACE_USERNAME)",
    "username": "REPLACE_WITH_YOUR_USERNAME",
    "password": "REPLACE_WITH_YOUR_PASSWORD"
  },
  "openai_api_key": "REPLACE_WITH_YOUR_KEY",
  "mongodb_uri": "mongodb://shared-db.company.com:27017/",
  "database_name": "team_moderation"
}
```

Team members replace the `REPLACE_*` values with their credentials.

## Summary

- Use `config.template.json` as a starting point
- Create your config file with real credentials
- Import with `reddit-auto-mod config --file path/to/config.json`
- Keep config files secure and never commit them to version control
- Use file import for automation and team deployments
