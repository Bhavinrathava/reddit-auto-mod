# Testing Guide for Reddit Auto Mod CLI

This guide will walk you through testing all CLI commands step by step.

## Prerequisites

Before testing, ensure you have:
- Python 3.8 or higher installed
- Git installed
- Node.js and npm installed (for frontend)
- Reddit API credentials ready
- OpenAI API key ready
- MongoDB instance (local or cloud)

## Step 1: Install the Package

### From Source (Recommended for Testing)

```bash
# Navigate to the project directory
cd /path/to/AutoMod

# Install in development mode
pip install -e .

# Verify installation
reddit-auto-mod version
```

Expected output:
```
reddit-auto-mod version 0.1.0
```

## Step 2: Test Config Command

### Test Basic Config

```bash
# Run the config wizard
reddit-auto-mod config
```

You'll be prompted for:
1. Reddit Client ID
2. Reddit Client Secret (hidden input)
3. Reddit User Agent (e.g., "MyTestBot/1.0")
4. Reddit Username
5. Reddit Password (hidden input)
6. OpenAI API Key (hidden input)
7. MongoDB URI (optional)

**Expected behavior**:
- All password inputs should be hidden (shown as ********)
- Should show success message with config file location
- Config file created at: `~/.reddit-auto-mod/config.json`

### Test Show Config

```bash
reddit-auto-mod config --show
```

**Expected output**:
```
============================================================
Current Configuration
============================================================

Reddit Credentials:
  Client ID: abc12345...
  Client Secret: ********...
  User Agent: MyTestBot/1.0
  Username: your_username
  Password: ********

OpenAI API Key: sk-proj-...xyz

MongoDB URI: mongodb://...

Config file location: /home/user/.reddit-auto-mod/config.json
```

### Verify Config File

```bash
# Check if config file exists and has correct permissions
ls -la ~/.reddit-auto-mod/config.json

# On Unix/Linux, should show: -rw------- (600 permissions)
```

## Step 3: Test Setup Command

### Test Setup Status (Before Setup)

```bash
reddit-auto-mod setup --status
```

**Expected output**:
```
============================================================
Setup Status
============================================================

✓ Reddit credentials configured
✓ OpenAI API key configured
✗ No subreddits configured
✗ Database not configured
✓ MongoDB URI configured

Index Files:
(none - no subreddits configured yet)
```

### Test Interactive Setup

```bash
reddit-auto-mod setup
```

**Steps**:
1. Enter subreddit names (one per line), e.g.:
   - `testmoderation` (press Enter)
   - `AskReddit` (press Enter)
   - (press Enter on empty line to finish)

2. Confirm or enter MongoDB database name (default: mainDB)

3. Choose whether to build indexes now (y/n)
   - If you choose 'n', indexes can be built later

**Expected behavior**:
- Creates MongoDB collections:
  - RedditRules
  - RedditSubmissions
  - ProcessedRedditSubmissions
- Creates indexes on key fields
- If building indexes, shows progress for each subreddit
- Shows success message

### Test Setup Status (After Setup)

```bash
reddit-auto-mod setup --status
```

**Expected output**:
```
============================================================
Setup Status
============================================================

✓ Reddit credentials configured
✓ OpenAI API key configured
✓ Subreddits configured: testmoderation, AskReddit
✓ Database configured: mainDB
✓ MongoDB URI configured

Index Files:
  ✗ testmoderation: Index files missing (if no posts in DB)
  ✗ AskReddit: Index files missing (if no posts in DB)
```

**Note**: Index files will only be created if there are posts in the RedditSubmissions collection for those subreddits.

### Test Index Building

```bash
reddit-auto-mod setup --build-indexes
```

**Expected behavior**:
- Loads sentence transformer model
- Connects to MongoDB
- For each subreddit:
  - Fetches posts
  - Generates embeddings (with progress bar)
  - Builds FAISS index
  - Saves index files

**Note**: This will only work if you have posts in the RedditSubmissions collection.

## Step 4: Test Start Command

### Test Start Status (Before Starting)

```bash
reddit-auto-mod start --status
```

**Expected output**:
```
============================================================
Service Status
============================================================

✗ Data Processing API: Not running
✗ Summarization API: Not running
✗ Rule Violation API: Not running
✗ Similarity API: Not running
✗ Frontend: Not running
```

### Test Starting Services

```bash
reddit-auto-mod start
```

**Expected behavior**:
1. Checks prerequisites (config and setup)
2. Starts backend services one by one:
   - Text Summarization (port 8002)
   - Rule Violation (port 8003)
   - Post Similarity (port 8004)
   - Data Processing API (port 8001)
3. Starts frontend (port 5173)
4. Asks if you want to run processing now
5. Starts scheduler
6. Shows service URLs
7. Keeps running until Ctrl+C

**Expected output**:
```
============================================================
Starting Reddit Auto Mod Services
============================================================

Starting Backend Services...
------------------------------------------------------------
Starting Text Summarization on port 8002...
  ✓ Text Summarization started (PID: 12345)
Starting Rule Violation on port 8003...
  ✓ Rule Violation started (PID: 12346)
Starting Post Similarity on port 8004...
  ✓ Post Similarity started (PID: 12347)
Starting Data Processing API on port 8001...
  ✓ Data Processing API started (PID: 12348)

Starting Frontend...
------------------------------------------------------------
Starting Frontend (React)...
  ✓ Frontend started (PID: 12349)
  Frontend will be available at: http://localhost:5173

============================================================
✓ All services started successfully!
============================================================

Service URLs:
  Frontend:             http://localhost:5173
  Data Processing API:  http://localhost:8001
  Summarization API:    http://localhost:8002
  Rule Violation API:   http://localhost:8003
  Similarity API:       http://localhost:8004

Press Ctrl+C to stop all services

Starting daily processing scheduler...
  Job will run every day at 00:00 (midnight)

Do you want to run data processing now? (y/n):
```

### Test Service Status (While Running)

Open a new terminal and run:

```bash
reddit-auto-mod start --status
```

**Expected output**:
```
============================================================
Service Status
============================================================

✓ Data Processing API: Running
✓ Summarization API: Running
✓ Rule Violation API: Running
✓ Similarity API: Running
✓ Frontend: Running
```

### Verify Services Manually

While services are running, test each endpoint:

```bash
# Test Summarization API
curl http://localhost:8002/health

# Test Rule Violation API
curl http://localhost:8003/health

# Test Similarity API
curl http://localhost:8004/health

# Test Data Processing API
curl http://localhost:8001/health

# Test Frontend (should return HTML)
curl http://localhost:5173
```

Each health endpoint should return:
```json
{"status":"healthy"}
```

### Test Graceful Shutdown

In the terminal where services are running, press `Ctrl+C`:

**Expected behavior**:
- Shows "Received shutdown signal..."
- Stops all services gracefully
- Shows "✓ [Service] stopped" for each service
- Exits cleanly

## Common Test Scenarios

### Scenario 1: Fresh Installation

```bash
# 1. Install
cd /path/to/AutoMod
pip install -e .

# 2. Configure
reddit-auto-mod config

# 3. Setup
reddit-auto-mod setup

# 4. Start
reddit-auto-mod start
```

### Scenario 2: Update Configuration

```bash
# View current config
reddit-auto-mod config --show

# Update config (will prompt to overwrite)
reddit-auto-mod config

# Verify update
reddit-auto-mod config --show
```

### Scenario 3: Add New Subreddit

```bash
# Run setup again (will prompt to overwrite)
reddit-auto-mod setup

# Enter new list of subreddits
# Choose not to build indexes immediately

# Build indexes later
reddit-auto-mod setup --build-indexes
```

### Scenario 4: Check Everything is Working

```bash
# 1. Check config
reddit-auto-mod config --show

# 2. Check setup
reddit-auto-mod setup --status

# 3. Start services
reddit-auto-mod start

# 4. In another terminal, check status
reddit-auto-mod start --status

# 5. Access frontend in browser
# Open: http://localhost:5173

# 6. Stop services (Ctrl+C in first terminal)
```

## Troubleshooting Tests

### Test 1: Missing Config

```bash
# Clear config
reddit-auto-mod config --clear

# Try to run setup without config
reddit-auto-mod setup
```

**Expected**: Should show error message asking to run config first

### Test 2: Missing Setup

```bash
# Try to start without setup
reddit-auto-mod start
```

**Expected**: Should show error message asking to run setup first

### Test 3: Port Already in Use

```bash
# Start services
reddit-auto-mod start

# In another terminal, try to start again
reddit-auto-mod start
```

**Expected**: Should fail because ports are already in use

## Verification Checklist

Use this checklist to verify everything works:

- [ ] `reddit-auto-mod version` shows version
- [ ] `reddit-auto-mod config` creates config file
- [ ] `reddit-auto-mod config --show` displays masked credentials
- [ ] Config file has restricted permissions (Unix: 600)
- [ ] `reddit-auto-mod setup` creates MongoDB collections
- [ ] `reddit-auto-mod setup --status` shows configuration status
- [ ] `reddit-auto-mod start` launches all services
- [ ] All health endpoints return {"status":"healthy"}
- [ ] Frontend is accessible at http://localhost:5173
- [ ] `reddit-auto-mod start --status` shows all services running
- [ ] Ctrl+C stops all services gracefully
- [ ] Services don't leave zombie processes

## Performance Tests

### Test Index Building Performance

```bash
# Time the index building
time reddit-auto-mod setup --build-indexes
```

Measure:
- Time per subreddit
- Memory usage during embedding generation

### Test Service Startup Time

```bash
# Time the startup
time reddit-auto-mod start <<< "n"
```

(The `<<< "n"` automatically answers "n" to the processing prompt)

## Automated Testing Script

Create a test script:

```bash
#!/bin/bash
# test_cli.sh

echo "Testing Reddit Auto Mod CLI"
echo "==========================="
echo

# Test 1: Version
echo "Test 1: Version command"
reddit-auto-mod version
echo

# Test 2: Config show (should fail if no config)
echo "Test 2: Config show"
reddit-auto-mod config --show || echo "No config found (expected)"
echo

# Test 3: Setup status
echo "Test 3: Setup status"
reddit-auto-mod setup --status
echo

# Test 4: Start status (services not running)
echo "Test 4: Start status (should show not running)"
reddit-auto-mod start --status
echo

echo "All tests completed!"
```

Run with:
```bash
chmod +x test_cli.sh
./test_cli.sh
```

## Next Steps After Testing

Once all tests pass:

1. Add actual subreddit rules to MongoDB RedditRules collection
2. Add historical posts to RedditSubmissions collection
3. Build indexes with real data
4. Start services and monitor for any issues
5. Access frontend and test moderation workflow

## Getting Help

If tests fail:
1. Check error messages carefully
2. Verify all prerequisites are installed
3. Check logs in terminal output
4. Verify credentials are correct
5. Ensure MongoDB is running and accessible
6. Check if ports are available (8001-8004, 5173)
