#!/usr/bin/env python3
"""Post an X (Twitter) thread by chaining replies.

Each tweet is posted as a reply to the previous one, forming a thread. Tweet
texts come from positional arguments (one per tweet); if none are given, texts
are read from stdin, one per line (blank lines are skipped).

Authentication is shared with x_publisher.py and reads credentials only from
the environment (OAuth 1.0a user context). Run `python3 scripts/x_publisher.py
verify` first to confirm creds.

Usage:
  # Thread from positional args
  python3 scripts/post_thread.py "First tweet." "Second tweet." "Third tweet."

  # Thread from stdin (one tweet per line)
  printf 'First tweet.\\nSecond tweet.\\nThird tweet.\\n' | \
    python3 scripts/post_thread.py

On success prints the chained tweet IDs and the root tweet URL, plus a JSON
object on stdout describing the thread.
"""

import sys
import json
import argparse

from x_publisher import (
    get_client_data, get_user_info, validate_credentials, TWEEPY_AVAILABLE,
)


def post_thread(client, texts):
    """Post `texts` as a chained thread. Returns list of tweet IDs, or None on failure."""
    prev_id = None
    ids = []
    for i, text in enumerate(texts, 1):
        kwargs = {'text': text}
        if prev_id is not None:
            kwargs['in_reply_to_tweet_id'] = prev_id
        response = client.create_tweet(**kwargs)
        tweet_id = response.data['id']
        ids.append(tweet_id)
        print(f"T{i}/{len(texts)}: {tweet_id}")
        prev_id = tweet_id
    return ids


def main():
    parser = argparse.ArgumentParser(
        description='Post an X (Twitter) thread by chaining replies.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="If no tweet texts are given as arguments, reads one tweet per line from stdin.",
    )
    parser.add_argument('texts', nargs='*', help='Tweet text(s); one tweet per argument.')
    args = parser.parse_args()

    if not TWEEPY_AVAILABLE:
        print("❌ tweepy is not installed. Run: pip3 install tweepy --user")
        return

    texts = args.texts or [line for line in sys.stdin.read().splitlines() if line.strip()]
    if len(texts) < 2:
        print("❌ Need at least 2 tweets to form a thread.")
        print("   Pass them as arguments, or pipe one tweet per line via stdin.")
        return

    client_data = get_client_data()
    if not client_data:
        return

    if not validate_credentials(client_data):
        return

    client = client_data['client']
    user_info = get_user_info(client) or {}
    username = user_info.get('username', 'user')

    print(f"\n📤 Posting thread ({len(texts)} tweets)...")
    ids = post_thread(client, texts)
    if ids is None:
        return

    root_url = f"https://twitter.com/{username}/status/{ids[0]}"
    print("\n" + "=" * 60)
    print("✅ Thread published successfully!")
    print("=" * 60)
    print("🔗 Chain: " + " -> ".join(ids))
    print(f"🌐 URL: {root_url}")
    print("=" * 60)

    print("\n📋 JSON Output:")
    print(json.dumps({
        'success': True,
        'tweet_ids': ids,
        'root_tweet_id': ids[0],
        'url': root_url,
        'texts': texts,
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
