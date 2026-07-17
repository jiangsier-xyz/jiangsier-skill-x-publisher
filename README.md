# X (Twitter) Publisher

A small command-line tool (and Claude Code skill) for publishing tweets to X (Twitter) via the official [Tweepy](https://docs.tweepy.org/) library. It supports text-only tweets, tweets with images or video, reply-chained **threads**, and credential verification — and returns detailed publish results (tweet ID, URL) including a JSON block for programmatic use.

The project ships as a [clawhub](https://clawhub.ai) skill package (`x-publisher`), but the scripts under `scripts/` work standalone with nothing more than Python + Tweepy and four environment variables.

## Features

- 📝 **Text-only tweets** — quick single-shot publishing
- 🖼️ **Image support** — JPG, PNG, GIF, WebP (up to 4 images per tweet)
- 🎬 **Video support** — MP4, MOV, AVI, WebM (chunked upload)
- 🧵 **Threads** — publish a multi-tweet thread in one command, chained as replies
- 📊 **Detailed results** — tweet ID, URL, creation time, plus a JSON object on stdout
- ✅ **Auth verification** — confirm your X API credentials before publishing

## Prerequisites

### 1. Install Tweepy

```bash
pip3 install tweepy --user
```

### 2. Get X API credentials

1. Visit the [X Developer Portal](https://developer.twitter.com/en/portal/dashboard).
2. Create a project and generate your API keys.
3. Make sure the app has **Read and Write** permissions.
4. Obtain the four **OAuth 1.0a user-context** credentials:
   - API Key (consumer key)
   - API Secret (consumer secret)
   - Access Token
   - Access Token Secret

> All four are required. OAuth 1.0a signs every request with a composite key built from the consumer secret and the token secret, so the consumer pair and the access-token pair are both load-bearing — there is no bearer-token / app-only path, because every operation here (tweeting, media upload, `get_me`) requires user-context auth.

### 3. Configure environment variables

The scripts read credentials **only from the environment** — no config files are parsed. Set the four variables before running, either in your shell rc or by exporting them from a `.env` file:

```bash
export X_API_KEY="your-api-key"
export X_API_SECRET="your-api-secret"
export X_ACCESS_TOKEN="your-access-token"
export X_ACCESS_TOKEN_SECRET="your-access-token-secret"
```

If you keep them in a `.env` file in the current directory, load it into your environment first:

```bash
set -a && . ./.env && set +a
```

Optionally, set `X_HTTP_PROXY` if the X API is not reachable directly from your network.

## Usage

### Verify credentials

Run this first in a new environment to confirm authentication and see the account:

```bash
python3 scripts/x_publisher.py verify
```

```
✅ Authentication successful!
👤 Username: @your_username
📛 Display Name: Your Name
👥 Followers: 1,234
📝 Tweets: 5,678
```

### Publish a text-only tweet

```bash
python3 scripts/x_publisher.py tweet "Hello, X! This is my first tweet."
```

### Publish a tweet with media

```bash
# Single image
python3 scripts/x_publisher.py tweet "Check out this photo!" --media /path/to/image.jpg

# Up to 4 images
python3 scripts/x_publisher.py tweet "My photo collection:" \
  --media /path/to/photo1.jpg \
  --media /path/to/photo2.png \
  --media /path/to/photo3.gif

# A video
python3 scripts/x_publisher.py tweet "Watch this!" --media /path/to/video.mp4
```

### Reply to an existing tweet

```bash
python3 scripts/x_publisher.py tweet "A reply." --reply-to <tweet_id>
```

### Publish a thread

`scripts/post_thread.py` publishes a multi-tweet thread in one command, chaining each tweet as a reply to the previous one. Tweet texts come from positional arguments (one per tweet), or — if none are given — from stdin (one tweet per line, blank lines skipped).

```bash
# Thread from arguments
python3 scripts/post_thread.py "First tweet of the thread." "Second tweet." "Third tweet."

# Thread from stdin
printf 'First tweet.\nSecond tweet.\nThird tweet.\n' | python3 scripts/post_thread.py
```

### Output

On success, the publisher prints a human-readable block followed by a JSON object on stdout (the JSON is the stable contract for programmatic callers):

```
============================================================
✅ Tweet published successfully!
============================================================
📝 Tweet ID: 1234567890123456789
🔗 URL: https://twitter.com/user/status/1234567890123456789
⏰ Created At: 2024-02-03T15:30:45.123456
📄 Preview: Hello, X! ...
============================================================

📋 JSON Output:
{
  "success": true,
  "tweet_id": "1234567890123456789",
  "text": "Hello, X! This is my first tweet.",
  "created_at": "2024-02-03T15:30:45.123456",
  "url": "https://twitter.com/user/status/1234567890123456789"
}
```

`post_thread.py` similarly prints each tweet's ID as it goes, then a chain summary and a JSON object with `tweet_ids`, `root_tweet_id`, `url`, and `texts`.

## Command reference

| Command | Purpose | Example |
|---------|---------|---------|
| `verify` | Verify authentication | `x_publisher.py verify` |
| `tweet` | Publish a tweet | `x_publisher.py tweet "Hello" --media photo.jpg` |
| (thread) | Publish a reply-chained thread | `post_thread.py "First" "Second" "Third"` |

### `tweet` arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `text` | - | Tweet content | Yes |
| `--media` | `-m` | Media file path (repeatable, max 4) | No |
| `--reply-to` | `-r` | Tweet ID to reply to (for threading) | No |

## Project structure

```
x-publisher/
├── SKILL.md              # Skill manifest + user-facing docs (clawhub)
├── CLAUDE.md             # Guidance for Claude Code agents working in this repo
├── README.md             # This file (English)
├── README.zh-CN.md       # Chinese README
├── _meta.json            # clawhub package metadata
├── .clawhub/origin.json  # clawhub registry origin
├── references/
│   └── x_api.md          # X API / Tweepy reference: methods, error codes, rate limits
└── scripts/
    ├── x_publisher.py    # tweet / media / verify CLI; shared auth (get_client_data)
    └── post_thread.py    # reply-chained thread CLI
```

## Architecture (for contributors)

- **`get_client_data()`** in `scripts/x_publisher.py` is the single auth entry point (also imported by `post_thread.py`). It reads the four OAuth 1.0a credentials from the environment, applies `X_HTTP_PROXY` if set, and returns `{'client', 'api', 'auth'}`.
- Two Tweepy surfaces are used:
  - **v1.1** (`tweepy.API` / `OAuth1UserHandler`) — required for `media_upload`, including chunked upload for videos (`media_category='tweet_video'`).
  - **v2** (`tweepy.Client` with `wait_on_rate_limit=True`) — used for `create_tweet` and `get_me`.
- Both surfaces share the same OAuth 1.0a credentials.
- `validate_credentials` runs `get_me` before every publish. On failure, `publish_tweet` catches `Forbidden` / `Unauthorized` / `TooManyRequests` and returns a structured error dict instead of raising.
- Tweet text over 280 characters is truncated to 277 + `"...publish"`.

## API limits

| Limit | Value |
|-------|-------|
| Tweet length | 280 characters (truncated if exceeded) |
| Media per tweet | 4 images and/or videos |
| Max image size | 5 MB |
| Max video size | 512 MB |
| Max video duration | 2 min 20 sec |
| Publish rate | 300 tweets / 15 min (rate limited) |

## Error handling

| Error | Cause | Fix |
|-------|-------|-----|
| Authentication failed | Wrong / expired keys or tokens | Check credentials; ensure tokens aren't expired |
| Insufficient permissions | App lacks Write permission, or content violates X rules | Enable Write in the developer portal |
| Rate limit exceeded | >300 tweets / 15 min | Wait a few minutes and retry |
| Media file not found / too large | Bad path or over size limit | Verify path, format, and size |

See `references/x_api.md` for the full list of X API error codes and rate-limit windows.

## Notes

- **Credential security** — keep credentials in the environment (or a gitignored `.env`); never commit them.
- **Content compliance** — follow X's platform rules.
- **Rate control** — respect the 300-tweets-per-15-minutes limit.
- **Media copyright** — ensure uploaded media is licensed or authorized.

## References

- Tweepy: https://docs.tweepy.org/
- X API v2: https://docs.x.com/x-api
- X Developer Portal: https://developer.twitter.com/en/portal/dashboard
