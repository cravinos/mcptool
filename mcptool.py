"""
mcptool — Search through Discord messages to find solutions people have figured out.

Usage:
  mcptool search "keyword1 keyword2"          # Search with up to 2 keywords
  mcptool search --server <id>                # Specify server ID
  mcptool search --channel #general            # Search specific channel
  mcptool search --since 2024-06-01           # Only messages since date
  mcptool search --limit 50                   # Max results
  mcptool export --token <TOKEN>              # Export messages to JSON
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class Message:
    id: str
    content: str
    author_name: str
    author_id: str
    channel_id: str
    channel_name: str = ""
    server_id: str = ""
    timestamp: str = ""
    edited_timestamp: str = ""
    has_embeds: bool = False
    has_attachments: bool = False
    reactions_count: int = 0

    @property
    def is_solution_like(self) -> bool:
        """Check if message looks like it contains a solution."""
        indicators = [
            "solution", "worked", "fixed", "answer", "try", 
            "you can", "the issue is", "turns out", "found",
            "here's", "just needed", "was because", "error was"
        ]
        content_lower = self.content.lower()
        return any(indicator in content_lower for indicator in indicators)

    @property
    def solution_score(self) -> int:
        """Score how likely this message is a useful solution."""
        score = 0
        content_lower = self.content.lower()
        
        # Indicators of solutions
        if re.search(r'\d+ (min|hours?|days?)', content_lower):
            score += 1  # Specific time reference
        if re.search(r'error|bug|issue|problem', content_lower):
            score += 1
        if re.search(r'fix(ed|ing)?|solution|worked', content_lower):
            score += 2
        
        # Length bonus (solutions are usually substantive)
        word_count = len(self.content.split())
        if 50 < word_count < 500:
            score += 1
        elif word_count >= 500:
            score += 2
            
        return score


def parse_discord_export(filepath: str) -> list[Message]:
    """Parse messages from Discord export JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = []
    for msg in data.get("messages", []):
        message = Message(
            id=msg.get("id", ""),
            content=msg.get("content", ""),
            author_name=msg.get("author", {}).get("username", "Unknown"),
            author_id=msg.get("author", {}).get("id", ""),
            channel_id=msg.get("channelId", ""),
            server_id="",
            timestamp=msg.get("timestamp", ""),
            edited_timestamp=msg.get("editedTimestamp", ""),
            has_embeds=bool(msg.get("embeds")),
            has_attachments=bool(msg.get("attachments")),
            reactions_count=sum(
                r.get("count", 0) 
                for r in msg.get("reactions", [])
                if isinstance(r, dict)
            ),
        )
        messages.append(message)

    return messages


def search_messages(messages: list[Message], keywords: list[str], limit: int = 50) -> list[tuple[Message, float]]:
    """Search messages for keyword matches. Returns (message, relevance_score)."""
    
    if not keywords:
        return [(m, m.solution_score) for m in messages]

    results = []
    
    for msg in messages:
        content_lower = msg.content.lower()
        
        # Calculate how many keywords match and their positions
        keyword_scores = {}
        for kw in keywords:
            if kw.lower() in content_lower:
                # Weight by position (earlier is more relevant) and exact matches
                first_pos = content_lower.index(kw.lower())
                # Boost for being near start of message
                positional_score = 1.0 / (1 + first_pos / len(content_lower))
                
                # Check if it's a standalone word (not substring)
                is_word = bool(re.search(rf'\b{re.escape(kw)}\b', content_lower, re.IGNORECASE))
                
                keyword_scores[kw] = 1.5 if is_word else 0.8 + positional_score
        
        # Also check author names for user-specific solutions
        for kw in keywords:
            if kw.lower() in msg.author_name.lower():
                keyword_scores[f"@{kw}"] = 0.6

        if not keyword_scores:
            continue

        total_score = sum(keyword_scores.values())
        
        # Boost solution-like messages with relevant keywords
        if msg.is_solution_like and len(keywords) <= 2:
            total_score *= 1.5
            
        results.append((msg, total_score))

    # Sort by relevance score descending
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:limit]


def extract_solutions(messages: list[Message]) -> list[tuple[Message, str]]:
    """Extract solution-like discussions from messages."""
    solutions = []
    
    for msg in messages:
        content_lower = msg.content.lower()
        
        # Pattern matching for common solution formats
        patterns = [
            r'(?:the (issue|problem|error))\s+(?:was|is)\s+.*?(?=\.(?:\s|$))',
            r'(?:solution|fix)\s*:\s*(.+?)(?=\.|$)',
            r'(?:try|just) (?:to|adding)?\s+([^.]{10,})',
            r'found\s+(?:it|the|a)\s+(?:issue|bug|problem).*?(?=\.(?:\s|$))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content_lower)
            if match:
                solutions.append((msg, match.group(0)))
                break

    return solutions


def format_results(results: list[tuple[Message, float]], keywords: list[str]) -> str:
    """Format search results for display."""
    lines = []
    separator = "─" * 72
    
    if len(keywords) == 1:
        kw_display = f'"{keywords[0]}"'
    else:
        kw_display = f'"{keywords[0]} and {keywords[1]}"'
    
    lines.append(f"\n🔍 Search results for keyword{ 's' if len(keywords) > 1 else '' } {kw_display}")
    lines.append(separator + "\n")

    for msg, score in results:
        # Format timestamp
        ts = ""
        try:
            dt = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00'))
            ts = dt.strftime("%Y-%m-%d %H:%M").ljust(20)
        except (ValueError, AttributeError):
            ts = msg.timestamp[:19].ljust(20)

        # Author with score indicator
        author_str = f"{msg.author_name:<20}"
        solution_badge = " ✨" if msg.is_solution_like else ""
        
        lines.append(f"[{ts}] {author_str}  Score: {score:.1f}{solution_badge}")
        lines.append(f"   Channel: #{msg.channel_name or 'general'}")
        
        # Truncate content for display, but show meaningful chunk
        content = msg.content.strip()
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"   {content}")
        
        # Show reactions for popular messages
        if msg.reactions_count > 0:
            lines.append(f"   👍 {msg.reactions_count} reactions")
        
        if msg.edited_timestamp and msg.is_solution_like:
            lines.append("   ✏️ (edited - likely refined solution)")
        
        lines.append("")

    lines.append(separator)
    return "\n".join(lines)


def extract_solutions_human(messages: list[Message], keywords: Optional[list[str]] = None) -> str:
    """Extract and format solutions people have figured out, as a human-readable report."""
    
    if keywords:
        messages = [m for m in messages 
                   if any(kw.lower() in m.content.lower() for kw in keywords)]
    
    # Filter to likely solution messages
    solutions = []
    for msg in sorted(messages, key=lambda x: x.solution_score + x.reactions_count, reverse=True):
        content_lower = msg.content.lower()
        
        indicators = [
            "solution", "fixed", "worked", "issue was", "error was", 
            "problem is", "turns out", "found it", "try this",
            "just needed", "was because"
        ]
        
        if any(ind in content_lower for ind in indicators) and len(msg.content.split()) > 20:
            solutions.append(msg)

    lines = ["\n✨ Solutions People Have Figured Out"]
    lines.append("═" * 72 + "\n")

    for i, msg in enumerate(solutions[:15]):
        try:
            dt = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime("%b %d, %Y")
        except (ValueError, AttributeError):
            date_str = "Unknown date"

        lines.append(f"{i+1}. {msg.author_name} — {date_str}")
        if msg.reactions_count > 5:
            lines.append(f"   ⬆️ {msg.reactions_count} upvotes")
        
        content = msg.content.strip()
        if len(content) > 250:
            # Try to find the solution portion
            sentences = re.split(r'(?<=[.!?])\s+', content)
            content = " ".join(sentences[:3]) + "..."
        lines.append(f"   {content}")
        lines.append("")

    return "\n".join(lines)


def run_search(query: str, server_id: Optional[str] = None, 
               channel: Optional[str] = None, 
               since: Optional[str] = None,
               limit: int = 50,
               export_file: Optional[str] = None) -> None:
    """Main search function."""
    
    # Parse keywords from query
    keywords = [kw.strip() for kw in query.split() if kw.strip()]
    if not keywords:
        print("Usage: mcptool search 'keyword1 keyword2'")
        return

    # Load messages (from file or export)
    messages_file = "discord_export.json"
    
    if os.path.exists(messages_file):
        messages = parse_discord_export(messages_file)
    elif export_file and os.path.exists(export_file):
        messages = parse_discord_export(export_file)
    else:
        print(f"No Discord export found at '{messages_file}'.")
        print("Run 'mcptool export' first or provide --file <path>")
        return

    # Filter by date if specified
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            messages = [m for m in messages 
                       if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) >= since_dt]
        except ValueError:
            print(f"Invalid date format for --since: {since}")

    # Filter by channel if specified  
    if channel and channel.startswith("#"):
        channel = channel[1:]  # Remove # prefix
    
    # Run search
    results = search_messages(messages, keywords, limit=limit)
    
    # Display both keyword matches and extracted solutions
    formatted = format_results(results, keywords)
    print(formatted)

    # Show top solutions
    print(extract_solutions_human(messages[:100], keywords))


def main():
    """CLI entry point."""
    args = sys.argv[1:]
    
    if not args:
        print(__doc__)
        return
    
    command = args[0]
    remaining = args[1:]

    # Simple argument parsing
    server_id = None
    channel = None
    since = None
    limit = 50
    keywords = []
    query_file = None
    
    i = 0
    while i < len(remaining):
        arg = remaining[i]
        if arg == "--server" and i + 1 < len(remaining):
            server_id = remaining[i + 1]
            i += 2
        elif arg == "--channel" and i + 1 < len(remaining):
            channel = remaining[i + 1]
            i += 2
        elif arg == "--since" and i + 1 < len(remaining):
            since = remaining[i + 1]
            i += 2
        elif arg == "--limit" and i + 1 < len(remaining):
            limit = int(remaining[i + 1])
            i += 2
        elif arg == "--file" and i + 1 < len(remaining):
            query_file = remaining[i + 1]
            i += 2
        else:
            keywords.append(arg)
            i += 1

    if command == "search":
        run_search(
            query=" ".join(keywords),
            server_id=server_id,
            channel=channel,
            since=since,
            limit=limit,
            export_file=query_file,
        )
    elif command == "export":
        print("Export Discord messages to JSON (requires token)")
        # Implementation would use discord.py or discord-api-client
        print('Set DISCORD_TOKEN env var and run: python -m mcptool export')
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
