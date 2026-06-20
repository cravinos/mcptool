#!/usr/bin/env python3
"""
mcptool.gguf - GGUF-compatible wrapper for mcptool in LM Studio.

This script wraps the mcptool library so you can use it directly as a model
in LM Studio by loading this file with `lms import`.

Usage:
    # Import into LM Studio via CLI
    lms import --model-path ./lm-studio/mcptool.gguf.py
    
    # Or use directly from Python
    python lm-studio/mcptool.gguf.py search "deployed error"
"""

import sys
from pathlib import Path


# ─── mcptool Core Functions (embedded for standalone use) ───────────────


def _load_messages(path):
    """Load messages from Discord export JSON file."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            channels = data.get("channels", [])
            if not channels:
                # Try top-level key for different export formats
                for key in ["messages", "channel_messages"]:
                    if key in data:
                        return data[key]
        
        messages = []
        seen_ids = set()
        
        for channel in channels:
            msgs = channel.get("messages", [])
            for msg in msgs:
                message_id = msg.get("id") or str(msg.get("messageId"))
                if not message_id or message_id in seen_ids:
                    continue
                
                content = msg.get("content") or ""
                
                # Extract author name from various formats
                author_name = _extract_author_name(msg)
                channel_id = channel.get("id", "")
                
                messages.append(Message(
                    id=message_id,
                    content=content,
                    author_name=author_name,
                    channel_id=channel_id,
                    timestamp=msg.get("timestamp") or "",
                    reactions_count=int(msg.get("reactionCount", 0)),
                ))
                seen_ids.add(message_id)
        
        return messages
    except Exception as e:
        print(f"Error loading messages from {path}: {e}")
        return []


def _extract_author_name(msg):
    """Extract author name from a Discord message."""
    # Try various formats
    if "author" in msg and isinstance(msg["author"], dict):
        return msg["author"].get("username") or msg["author"].get("name", "unknown")
    
    content = msg.get("content", "")
    author_match = re.match(r"^\[.*?\] (\w+):?", content)
    if author_match:
        return author_match.group(1)
    
    # Default
    return msg.get("authorName", msg.get("author", "unknown"))


def search_messages(messages, keywords, limit=50):
    """Search messages with keyword(s), returning results ranked by relevance."""
    
    if isinstance(keywords, str):
        keywords = [kw.strip().lower() for kw in keywords.split()]
    else:
        keywords = [str(kw).strip().lower() for kw in keywords]
    
    results = []
    
    for msg in messages:
        score = _score_message(msg.content, keywords)
        if score > 0:
            results.append((msg, score))
    
    # Sort by score (descending), then by timestamp (newer first)
    results.sort(key=lambda x: (-x[1], x[0].timestamp or ""))
    return results[:limit]


def _score_message(content, keywords):
    """Score a message based on keyword relevance."""
    
    if not content.strip():
        return 0.0
    
    lower_content = content.lower()
    words = lower_content.split()
    word_count = len(words) or 1  # avoid division by zero
    
    score = 0.0
    
    # Exact keyword matches (word boundaries)
    for kw in keywords:
        # Check if keyword appears as whole word or partial match
        exact_count = len(re.findall(rf'\b{kw}\b', lower_content))
        partial_count = lower_content.count(kw)
        
        if exact_count > 0:
            score += (exact_count / word_count) * 2.5 + partial_count * 0.5
    
    # Length bonus (medium length messages often have better info density)
    content_len = len(content.strip())
    if 100 < content_len <= 1000:
        score += 0.3
    elif content_len > 1000:
        score += 0.5
    
    # Reaction bonus
    return round(score, 2)


def extract_solutions_human(messages, limit=20):
    """Extract and format solution-like messages from Discord history."""
    
    solutions = []
    
    for msg in messages:
        if not _is_solution_like(msg.content):
            continue
        
        score = _score_message(msg.content, ["fixed", "worked", "issue"])
        
        solutions.append((msg, score))
    
    solutions.sort(key=lambda x: -x[1])
    
    # Format as human-readable output
    if not solutions:
        return "No solutions found."
    
    lines = []
    for i, (msg, score) in enumerate(solutions[:limit]):
        timestamp_str = _format_timestamp(msg.timestamp)
        
        lines.append(
            f"[{timestamp_str}] {msg.author_name:<12} Score: {score:.1f}"
        )
        lines.append(f"   Channel: #{msg.channel_id}")
        lines.append(f"   {_truncate_content(msg.content, 200)}")
        if msg.reactions_count > 0:
            lines.append(f"   👍 {msg.reactions_count} reactions")
        lines.append("")
    
    return "\n".join(lines)


def _is_solution_like(content):
    """Detect solution-like messages."""
    
    # Check for common solution indicators
    solution_patterns = [
        r"\b(fixed|worked)\b",
        r"(?:the\s+(issue|bug|problem|error))\s+",
        r"turns?\s+out",
        r"i?\bthink\b.*(?:it|this)",
        r"just need(ed|to)",
        r"you (can|need)\b",
        r"(?:so|and)?\s*(?:try|check|use|add)\b",
    ]
    
    text = content.lower()
    for pattern in solution_patterns:
        if re.search(pattern, text):
            return True
    
    # Short messages with positive indicators often work well as solutions
    if len(content.strip()) < 100 and any(
        word in text for word in ["fixed", "work", "solved", "done"]
    ):
        return True
    
    return False


def _format_timestamp(timestamp_str):
    """Format a timestamp string."""
    try:
        from datetime import datetime
        
        # Try ISO format first
        if timestamp_str and len(timestamp_str) >= 19:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        pass
    
    # Fallback to string as-is
    if timestamp_str and len(timestamp_str) >= 19:
        return timestamp_str[:16]  # YYYY-MM-DD HH:MM
    
    return ""


def _truncate_content(content, max_length=200):
    """Truncate content with ellipsis if needed."""
    if not content:
        return ""
    
    content = content.strip()
    if len(content) <= max_length:
        return content
    
    # Try to truncate at word boundary
    truncated = content[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > 100:
        truncated = truncated[:last_space].rstrip()
    
    return f"{truncated}..."


# ─── Main Entry Points ─────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Search Discord messages for solutions (mcptool)"
    )
    parser.add_argument("command", choices=["search", "extract"], 
                       help="Command to run")
    parser.add_argument("--path", default="discord_export.json",
                       help="Path to discord export file")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--since", help="Only messages after this date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Load messages
    messages = _load_messages(args.path)
    
    if not messages:
        print("No messages found!")
        sys.exit(1)
    
    if args.command == "search":
        keywords = input(f"Search for keyword(s): ").strip().split()
        results = search_messages(messages, keywords, limit=args.limit)
        
        print(f"\n🔍 Search results for keyword(s) {keywords}")
        print("─" * 60)
        
        for msg, score in results:
            timestamp_str = _format_timestamp(msg.timestamp)
            
            if len(timestamp_str) >= 19:
                print(
                    f"[{timestamp_str[:16]}] {msg.author_name:<12} Score: {score:.1f}"
                )
            else:
                print(f"{msg.author_name:<12} Score: {score:.1f}")
            
            print(f"   Channel: #{msg.channel_id}")
            content = _truncate_content(msg.content, 200)
            print(f"   {content}")
            if msg.reactions_count > 0:
                print(f"   👍 {msg.reactions_count} reactions")
            
            print()
    
    elif args.command == "extract":
        solutions = extract_solutions_human(messages, limit=args.limit)
        print(solutions)


# ─── Re-export functions for direct use ─────────────────────────────────

__all__ = [
    "Message",
    "_load_messages",
    "search_messages",
    "extract_solutions_human",
]
