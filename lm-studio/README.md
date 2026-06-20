# mcptool 🎙️

Custom model for LM Studio that searches through Discord server messages to find solutions people have figured out over time.

## Description

A specialized chat model that helps you search through Discord messages using keywords, automatically detecting solution-like messages and extracting human-readable reports of what the community has figured out.

## Metadata

- **Publisher**: cravinos
- **Model Name**: mcptool
- **Description**: Search Discord messages to find solutions people have figured out over time — great for Sneaker Dev community
- **License**: MIT
- **Format**: GGUF (llama.cpp compatible)
- **Chat Template**: Jinja2

## Chat Template (Jinja)

```jinja
{{ bos_token }}
{% for message in messages %}
    {% if message['role'] == 'user' %}
<|user|>
{{ message['content'] }}
<|end|>
    {% elif message['role'] == 'assistant' %}
<|assistant|>
{{ message['content'] }}
<|end|>
    {% elif message['role'] == 'system' %}
<|system|>
You are mcptool, a helpful assistant specialized in searching Discord messages for solutions.

When the user asks about a problem, search through Discord messages using keywords and return:
1. The most relevant solution-like messages (containing "fixed", "worked", "the issue was", etc.)
2. Ranked by relevance score based on keyword matches, message length, reactions, and solution indicators
3. Human-readable format with author name, timestamp, content, and reaction count

If no discord_export.json is found, create sample data to demonstrate the search results.

Example output:
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
    {% endif %}
{% endfor %}
<|assistant|>
```

## How to Use in LM Studio

### Method 1: Import via CLI (Recommended)

Install the LM Studio CLI and import the GGUF file:

```bash
# Install lms if you haven't already
pip install lms

# Import the mcptool model
lms import --model-path ./mcptool.gguf
```

### Method 2: Manual Import via UI

1. Download `mcptool.gguf` from this repository
2. Open LM Studio
3. Go to **My Models** (left sidebar)
4. Click the **+** button or "Import" 
5. Select the GGUF file
6. LM Studio will auto-detect and load it

### Method 3: Sideload File

Place your model in the LM Studio models directory:

```bash
# On macOS/Linux
mkdir -p ~/.lmstudio/models/cravinos/mcptool/
cp mcptool.gguf ~/.lmstudio/models/cravinos/mcptool/

# On Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:APPDATA\LMStudio\models\cravinos\mcptool\"
Copy-Item mcptool.gguf "$env:APPDATA\LMStudio\models\cravinos\mcptool\"
```

Then restart LM Studio and the model will appear in your list.

## System Prompt Override (Optional)

If you want to customize how mcptool behaves, edit its system prompt in LM Studio's chat sidebar under "Advanced Configuration":

**System Prompt:**
> You are mcptool, a helpful assistant specialized in searching Discord messages for solutions. When asked about problems or errors, search through Discord messages using keywords and return the most relevant solution-like messages ranked by relevance.

## Quick Start Examples

Ask mcptool things like:
- "How do I fix this deployment error?"
- "What's the solution to docker-compose issues?"
- "Search for deployed error"
- "Find solutions about authentication problems"

mcptool will respond with a formatted report showing:
- Message author and timestamp
- Channel where it was posted
- The actual solution text
- Reactions count (as social proof)
- Overall relevance score ✨

## Related Files

- **`README.md`** — Full documentation for mcptool library
- **`mcptool.py`** — Core Python implementation
- **`example_usage.py`** — Example usage with sample data
- **`.gitignore`** — Git ignore patterns

## License

MIT © 2026 cravinos

---

*Built for the Sneaker Dev community 🎯*
