"""Example: Use mcptool to find solutions in your Discord server."""

from mcptool import Message, parse_discord_export, search_messages, extract_solutions_human


def demo():
    # Example: load messages from export file
    try:
        messages = parse_discord_export("discord_export.json")
    except FileNotFoundError:
        print("No discord_export.json found. Creating example data...")

        # Create sample messages (like what you'd get from Discord export)
        messages = [
            Message(
                id="123",
                content="The issue was that the deployment failed because of a missing environment variable in production.",
                author_name="sarah_",
                channel_id="456",
                timestamp="2025-07-23T14:32:00Z",
                reactions_count=14,
            ),
            Message(
                id="124",
                content="Had the same error when deploying last week — just needed to update the docker-compose version and restart.",
                author_name="dev_mike",
                channel_id="457",
                timestamp="2025-06-15T09:18:00Z",
                reactions_count=6,
            ),
            Message(
                id="125",
                content="Turns out the bug was in how we were handling null values. Fixed it by adding a check.",
                author_name="jane_dev",
                channel_id="456",
                timestamp="2025-08-01T16:45:00Z",
                reactions_count=9,
            ),
        ]

    # Search with keywords
    results = search_messages(messages, ["deployed error"], limit=10)
    
    print("🔍 Top matches:")
    for msg, score in results[:3]:
        print(f"  {msg.author_name}: '{msg.content[:60]}...' (score: {score:.1f})")

    # Extract solutions
    solutions = extract_solutions_human(messages)
    print("\n" + solutions)


if __name__ == "__main__":
    demo()
