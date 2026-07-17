# X (Twitter) API Reference

Official Documentation: https://developer.twitter.com/en/docs/twitter-api

## API Versions

Tweepy supports both X API v1.1 and v2:

| Version | Purpose | Description |
|---------|---------|-------------|
| v1.1 | Media upload | Uses tweepy.API |
| v2 | Tweeting, querying | Uses tweepy.Client |

## Authentication Methods

### OAuth 1.0a (User Authentication)

Used for write operations like tweeting and media upload:

```python
auth = tweepy.OAuth1UserHandler(
    api_key, api_secret,
    access_token, access_token_secret
)

# API v1.1
api = tweepy.API(auth)

# API v2
client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)
```

### OAuth 2.0 (Bearer Token)

Used for read-only queries:

```python
client = tweepy.Client(bearer_token="your-bearer-token")
```

## Core Methods

### Publishing Tweets

```python
# Text-only
client.create_tweet(text="Hello, X!")

# With media
client.create_tweet(
    text="Check this out!",
    media_ids=["media_id_1", "media_id_2"]
)

# Reply to a tweet
client.create_tweet(
    text="This is a reply",
    in_reply_to_tweet_id="tweet_id_to_reply"
)

# Quote a tweet
client.create_tweet(
    text="Check out this tweet",
    quote_tweet_id="tweet_id_to_quote"
)
```

### Uploading Media

```python
# Simple upload
media = api.media_upload("/path/to/image.jpg")
media_id = media.media_id_string

# Chunked upload (for large files)
media = api.media_upload(
    "/path/to/video.mp4",
    chunked=True,
    media_category="tweet_video"
)

# With progress callback
def progress_callback(bytes_read):
    print(f"Uploaded: {bytes_read} bytes")

media = api.media_upload(
    "/path/to/video.mp4",
    chunked=True,
    media_category="tweet_video",
    progress_callback=progress_callback
)
```

### Media Categories

| Category | Description | Purpose |
|----------|-------------|---------|
| tweet_image | Regular images | Tweet images |
| tweet_video | Videos | Tweet videos |
| tweet_gif | GIF animations | Tweet GIFs |
| amplify_video | Promoted videos | Advertising |

### Getting User Information

```python
# Get current user
me = client.get_me()
print(me.data.username)

# Get specific user
user = client.get_user(username="twitter")
print(user.data.id)

# Get user details
user = client.get_user(
    username="twitter",
    user_fields=["created_at", "description", "public_metrics"]
)
```

### Getting Tweets

```python
# Get specific tweet
tweet = client.get_tweet("tweet_id")
print(tweet.data.text)

# Get user's tweets
tweets = client.get_users_tweets("user_id")
for tweet in tweets.data:
    print(tweet.text)
```

### Deleting Tweets

```python
client.delete_tweet("tweet_id")
```

## Error Handling

### Common Error Codes

| Error Code | Description | Suggested Action |
|------------|-------------|------------------|
| 88 | Rate limit | Wait and retry |
| 130 | Service overload | Retry later |
| 186 | Tweet too long | Shorten content |
| 187 | Duplicate tweet | Modify content and resend |
| 324 | Invalid media | Check media file |
| 326 | User restricted | Check account status |
| 327 | Already retweeted | No action needed |

### Exception Types

```python
from tweepy.errors import (
    HTTPException,
    Forbidden,
    NotFound,
    TooManyRequests,
    Unauthorized
)

try:
    client.create_tweet(text="Hello")
except Forbidden as e:
    print(f"Insufficient permissions: {e}")
except TooManyRequests as e:
    print(f"Rate limit: {e}")
    print(f"Reset time: {e.response.headers.get('x-rate-limit-reset')}")
except Unauthorized as e:
    print(f"Authentication failed: {e}")
```

## Rate Limits

### API v2 Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST tweets | 200 | 15 minutes |
| POST tweets (ads) | 600 | 15 minutes |
| GET tweets | 900 | 15 minutes |
| GET users | 900 | 15 minutes |

### Checking Remaining Quota

```python
# Check response headers
response = client.get_me()
print(response.headers.get('x-rate-limit-remaining'))
print(response.headers.get('x-rate-limit-reset'))
```

## Data Objects

### Tweet Object

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique tweet ID |
| text | string | Tweet content |
| author_id | string | Author ID |
| created_at | string | Creation time |
| public_metrics | object | Public metrics |
| entities | object | Entities (hashtags, URLs, etc.) |

### User Object

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique user ID |
| username | string | Username (after @) |
| name | string | Display name |
| created_at | string | Registration time |
| public_metrics | object | Followers, following, tweet counts |
| description | string | Profile bio |

### Public Metrics

| Field | Type | Description |
|-------|------|-------------|
| retweet_count | int | Retweet count |
| reply_count | int | Reply count |
| like_count | int | Like count |
| quote_count | int | Quote count |
| impression_count | int | Impression count |

## Best Practices

1. **Use environment variables** to store credentials
2. **Enable rate limit waiting** with `wait_on_rate_limit=True`
3. **Handle exceptions** wrap all API calls in try-except
4. **Logging** log key operations and errors
5. **Media preprocessing** check file size and format before upload

## Official Resources

- Tweepy: https://docs.tweepy.org/
- X API v2: https://developer.twitter.com/en/docs/twitter-api
- X API Rate Limits: https://developer.twitter.com/en/docs/twitter-api/rate-limits
