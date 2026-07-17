---
name: X (Twitter) Publisher
description: Publish tweets to X (Twitter) using the official Tweepy library. Supports text-only tweets, tweets with images or videos, and returns detailed publish results including tweet ID and URL. Requires X API credentials (API Key, API Secret, Access Token, Access Token Secret).
env:
  - X_API_KEY
  - X_API_SECRET
  - X_ACCESS_TOKEN
  - X_ACCESS_TOKEN_SECRET
---

# X (Twitter) Tweet Publishing Tool

Publish tweets using the official Tweepy library, supporting text-only, image, video, and other media types.

## Features

- 📝 **Text-Only Tweets** - Quickly publish text content
- 🖼️ **Image Support** - Supports JPG, PNG, GIF, WebP formats (up to 4 images)
- 🎬 **Video Support** - Supports MP4, MOV, AVI, WebM formats
- 📊 **Detailed Results** - Returns tweet ID, URL, creation time, and more
- ✅ **Auth Verification** - Supports verifying API credentials

## Prerequisites

### 1. Install Dependencies

```bash
pip3 install tweepy --user
```

### 2. Get X API Credentials

1. Visit https://developer.twitter.com/en/portal/dashboard
2. Create a project and generate API keys
3. Obtain the following credentials:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

### 3. Configure Environment Variables

The skill reads its credentials **only from the environment**. Set these four variables before running (in your shell rc, or export them from a `.env` file):

```bash
export X_API_KEY="your-api-key"
export X_API_SECRET="your-api-secret"
export X_ACCESS_TOKEN="your-access-token"
export X_ACCESS_TOKEN_SECRET="your-access-token-secret"
```

If you keep them in a `.env` file in the current directory, load it into your environment first, e.g.:

```bash
set -a && . ./.env && set +a
```

Optionally, set `X_HTTP_PROXY` if the X API is not reachable directly from your environment.

## Usage

### Verify Authentication

Before first use, verify your credentials:

```bash
python3 scripts/x_publisher.py verify
```

Example output:
```
✅ Authentication successful!
👤 Username: @your_username
📛 Display Name: Your Name
👥 Followers: 1,234
📝 Tweets: 5,678
```

### Publish Text-Only Tweet

```bash
python3 scripts/x_publisher.py tweet "Hello, X! This is my first tweet."
```

### Publish Tweet with Images

```bash
# Single image
python3 scripts/x_publisher.py tweet "Check out this photo!" --media /path/to/image.jpg

# Multiple images (up to 4)
python3 scripts/x_publisher.py tweet "My photo collection:" \
  --media /path/to/photo1.jpg \
  --media /path/to/photo2.png \
  --media /path/to/photo3.gif
```

### Publish Tweet with Video

```bash
python3 scripts/x_publisher.py tweet "Watch this video!" --media /path/to/video.mp4
```

### Publish a Thread

Post a multi-tweet thread in one command. Each tweet is published as a reply to the previous one.

```bash
# Thread from positional arguments (one tweet per argument)
python3 scripts/post_thread.py "First tweet of the thread." "Second tweet." "Third tweet."

# Thread from stdin (one tweet per line)
printf 'First tweet.\nSecond tweet.\nThird tweet.\n' | python3 scripts/post_thread.py
```

To reply to a single existing tweet (rather than start a new thread), use the `--reply-to` flag:

```bash
python3 scripts/x_publisher.py tweet "A reply." --reply-to <tweet_id>
```

## Output

After successful publishing, you will get:

```
============================================================
✅ Tweet published successfully!
============================================================
📝 Tweet ID: 1234567890123456789
🔗 URL: https://twitter.com/user/status/1234567890123456789
⏰ Created At: 2024-02-03T15:30:45.123456
📄 Preview: Hello, X! This is my first tweet.
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

## Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `verify` | Verify authentication | `x_publisher.py verify` |
| `tweet` | Publish a tweet | `x_publisher.py tweet "Hello" --media photo.jpg` |
| (thread) | Publish a reply-chained thread | `post_thread.py "First" "Second" "Third"` |

### tweet Command Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `text` | - | Tweet content | Yes |
| `--media` | `-m` | Media file path | No |

## Supported Media Formats

### Images
- **JPG/JPEG** - Recommended format
- **PNG** - Supports transparency
- **GIF** - Supports animation
- **WebP** - Modern format

**Limits**:
- Maximum 4 images
- Maximum 5MB per image

### Videos
- **MP4** - Recommended format
- **MOV** - QuickTime format
- **AVI** - Common format
- **WebM** - Modern format

**Limits**:
- Maximum 512MB per video
- Maximum duration: 2 minutes 20 seconds

## Error Handling

### Authentication Failure

```
❌ Authentication failed: Unable to retrieve user information
```

**Solution**:
- Check if API keys and tokens are correct
- Ensure tokens are not expired
- Verify network connectivity

### Insufficient Permissions

```
❌ Tweet publishing failed
Error Type: Insufficient permissions
Error Message: You are not allowed to create a Tweet with these settings
```

**Solution**:
- Ensure the app has "Write" permissions
- Check if you violate X platform rules

### Rate Limit Exceeded

```
❌ Tweet publishing failed
Error Type: Rate limit exceeded
Error Message: Rate limit exceeded
```

**Solution**:
- Wait a few minutes and retry
- X API rate limit: 300 tweets per 15 minutes

### Media Upload Failure

```
❌ Media file not found: /path/to/image.jpg
```

**Solution**:
- Check if the file path is correct
- Verify file format is supported
- Check if file size exceeds the limit

## Use Cases

### Use Case 1: Automated Publishing

```bash
# Publish daily summary
python3 scripts/x_publisher.py tweet "📊 Today's Market Summary: BTC $43,250 (+2.3%)" 
```

### Use Case 2: Publishing with Images

```bash
# Publish screenshots or charts
python3 scripts/x_publisher.py tweet "📈 Today's chart" --media ~/charts/btc_today.png
```

### Use Case 3: Batch Publishing Script

```bash
#!/bin/bash
# publish_news.sh

CONTENT="🚀 Breaking News: ..."
IMAGE="/path/to/news_image.jpg"

python3 scripts/x_publisher.py tweet "$CONTENT" --media "$IMAGE"
```

### Use Case 4: Integration with Other Tools

```python
import subprocess
import json

result = subprocess.run(
    ['python3', 'scripts/x_publisher.py', 'tweet', 'Hello!', '--media', 'photo.jpg'],
    capture_output=True,
    text=True
)

# Parse JSON output
output_lines = result.stdout.split('\n')
for line in output_lines:
    if line.strip().startswith('{'):
        tweet_info = json.loads(line)
        print(f"Tweet ID: {tweet_info['tweet_id']}")
        print(f"URL: {tweet_info['url']}")
```

## API Limits

| Limit Type | Value | Description |
|------------|-------|-------------|
| Tweet length | 280 characters | Will be truncated if exceeded |
| Media count | 4 | Images and/or videos |
| Image size | 5 MB | Per image |
| Video size | 512 MB | Per video |
| Video duration | 2 min 20 sec | Maximum duration |
| Publish rate | 300/15 min | Rate limit |

## Notes

1. **Credential Security** - Do not leak API keys, store them in environment variables
2. **Content Compliance** - Follow X platform rules, avoid violating content
3. **Rate Control** - Be aware of API rate limits, avoid frequent publishing
4. **Media Copyright** - Ensure uploaded media files are copyrighted or authorized

## References

- Tweepy Documentation: https://docs.tweepy.org/
- X API Documentation: https://developer.twitter.com/en/docs/twitter-api
- X Developer Portal: https://developer.twitter.com/en/portal/dashboard
