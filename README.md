# mcptool 🔍

Search through Discord server messages to find solutions people have figured out over time — especially useful for the **Sneaker Dev** community.

## Features

- Search by 1-2 keywords with relevance scoring
- Auto-detects solution-like messages (containing "fixed", "worked", "the issue was", etc.)
- Extract human-readable solution reports
- Filter by date, channel, and server
- Score messages based on content quality + reactions

## Installation

```bash
# Clone the repo
git clone https://github.com/cravinos/mcptool.git
cd mcptool

# Export your Discord messages (requires discord.py or similar)
python -m mcptool export --token YOUR_TOKEN

# Run searches
python -m mcptool search "error fixed"
python -m mcptool search "sneaker"
```

## Usage Examples

### Basic keyword search
```bash
python -m mcptool search "deployed error"
```
Finds messages containing both "deployed" and "error", ranked by relevance.

### Search with date filter
```bash
python -m mcptool search "solution" --since 2024-06-01
```

### Extract just the solutions people figured out
```bash
python -m mcptool extract-solutions --limit 20
```

### Search a specific channel
```bash
python -m mcptool search "fix bug" --channel "#help"
```

## Sample Output

```
───────────────────────────────────────────────────────
🔍 Search results for keyword(s) "deployed error"
───────────────────────────────────────────────────────

[2025-07-23 14:32] sarah_        Score: 9.8 ✨
   Channel: #help
   The issue was that the deployment failed because of a missing environment variable. Turns out it was just needed to set APP_ENV=production. Fixed by adding it to .env!
   👍 14 reactions

[2025-06-15 09:18] dev_mike      Score: 7.2 ✨
   Channel: #general
   Had the same error when deploying last week — just needed to update the docker-compose version and restart. Works now!
   👍 6 reactions

───────────────────────────────────────────────────────
```

## How It Works

1. **Keyword matching** — finds messages containing your search terms (exact word matches ranked higher)
2. **Solution detection** — automatically identifies solution-like messages using patterns like:
   - "the issue was...", "error was..."
   - "fixed", "worked"  
   - "just needed..."
   - "turns out..."
3. **Relevance scoring** — combines keyword match quality, message length (substantive = better), reaction counts, and solution indicators

## For Sneaker Dev

If you're part of the Sneaker Dev Discord server, export messages from:
- `#help` — where solutions are shared
- `#general` — community discoveries
- `open-ticket` — resolved issues

The tool works great for finding patterns like "how did people fix X?" or "what's the solution to Y?".

## License

MIT
