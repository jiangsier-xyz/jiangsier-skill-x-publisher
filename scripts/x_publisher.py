#!/usr/bin/env python3
"""
X (Twitter) Tweet Publishing Tool
Supports: text-only tweets, tweets with image/video media, returns publish results
"""

import os
import sys
import json
import argparse
from typing import Optional, List, Dict
from datetime import datetime

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    tweepy = None
    TWEEPY_AVAILABLE = False

# OAuth 1.0a user-context credentials, read from the environment only.
# All four are required to sign the write operations (create_tweet, media_upload)
# and get_me — see references/x_api.md and CLAUDE.md for why fewer won't work.
REQUIRED_CREDENTIALS = (
    'X_API_KEY',
    'X_API_SECRET',
    'X_ACCESS_TOKEN',
    'X_ACCESS_TOKEN_SECRET',
)

def get_client_data() -> Optional[Dict]:
    """Build the tweepy v1.1 API + v2 Client with OAuth 1.0a user context.

    Credentials come from the environment only. Returns
    {'client', 'api', 'auth'} on success, or None (with a guidance message) if
    tweepy is unavailable or required credentials are missing.
    """
    if not TWEEPY_AVAILABLE:
        print("⚠️  tweepy library not installed, please run: pip3 install tweepy --user")
        return None

    proxy = os.getenv('X_HTTP_PROXY')
    if proxy:
        for var in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY'):
            os.environ[var] = proxy
        print(f"🌐 Using HTTP proxy: {proxy}")

    values = {name: os.getenv(name) for name in REQUIRED_CREDENTIALS}
    missing = [name for name in REQUIRED_CREDENTIALS if not values[name]]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Set the following before running (e.g. in a .env file or your shell):")
        for name in REQUIRED_CREDENTIALS:
            print(f"  export {name}='your-{name.lower().replace('_', '-')}'")
        print("\nGet credentials at: https://developer.twitter.com/en/portal/dashboard")
        return None

    api_key = values['X_API_KEY']
    api_secret = values['X_API_SECRET']
    access_token = values['X_ACCESS_TOKEN']
    access_token_secret = values['X_ACCESS_TOKEN_SECRET']

    try:
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_token_secret
        )
        # OAuth 1.0a user context only — no bearer token. Every operation in
        # this skill (create_tweet, media_upload, get_me) requires user-context
        # auth, so a bearer token would be unused dead weight.
        return {
            'client': tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True,
            ),
            'api': tweepy.API(auth),
            'auth': auth,
        }
    except Exception as e:
        print(f"❌ Failed to initialize X API client: {e}")
        return None


def upload_media(api, media_path: str) -> Optional[str]:
    """Upload media file (image or video)"""
    if not os.path.exists(media_path):
        print(f"❌ Media file not found: {media_path}")
        return None
    
    # Check file size and type
    file_size = os.path.getsize(media_path)
    file_ext = os.path.splitext(media_path)[1].lower()
    
    # Image limit: 5MB
    # Video limit: 512MB
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    video_exts = ['.mp4', '.mov', '.avi', '.webm']
    
    if file_ext in image_exts and file_size > 5 * 1024 * 1024:
        print(f"❌ Image file too large (>5MB): {media_path}")
        return None
    
    if file_ext in video_exts and file_size > 512 * 1024 * 1024:
        print(f"❌ Video file too large (>512MB): {media_path}")
        return None
    
    try:
        print(f"📤 Uploading media: {media_path} ({file_size / 1024:.1f} KB)")
        
        # Use chunked upload for large files
        if file_ext in video_exts:
            media = api.media_upload(
                media_path,
                chunked=True,
                media_category='tweet_video'
            )
        else:
            media = api.media_upload(media_path)
        
        media_id = media.media_id_string
        print(f"✅ Media uploaded successfully, ID: {media_id}")
        return media_id
        
    except Exception as e:
        print(f"❌ Media upload failed: {e}")
        return None

def publish_tweet(client, text: str, media_ids: List[str] = None, reply_to: str = None) -> Optional[Dict]:
    """Publish a tweet"""
    try:
        # Check text length (X limits to 280 characters)
        if len(text) > 280:
            print(f"⚠️  Text length {len(text)} exceeds 280 character limit, will be truncated")
            text = text[:277] + "...publish"
        
        # Build kwargs
        tweet_kwargs = {'text': text}
        if media_ids:
            tweet_kwargs['media_ids'] = media_ids
        if reply_to:
            tweet_kwargs['in_reply_to_tweet_id'] = reply_to
        
        # Publish tweet
        response = client.create_tweet(**tweet_kwargs)
        
        # Extract result
        tweet_data = response.data
        result = {
            'success': True,
            'tweet_id': tweet_data['id'],
            'text': tweet_data['text'],
            'created_at': datetime.now().isoformat(),
            'url': f"https://twitter.com/user/status/{tweet_data['id']}"
        }
        
        return result
        
    except tweepy.errors.Forbidden as e:
        return {
            'success': False,
            'error': 'Insufficient permissions',
            'message': str(e),
            'api_errors': e.api_errors if hasattr(e, 'api_errors') else None
        }
    except tweepy.errors.Unauthorized as e:
        return {
            'success': False,
            'error': 'Authentication failed',
            'message': 'Please check if API keys and tokens are correct',
            'api_errors': e.api_errors if hasattr(e, 'api_errors') else None
        }
    except tweepy.errors.TooManyRequests as e:
        return {
            'success': False,
            'error': 'Rate limit exceeded',
            'message': 'Rate limit triggered, please try again later',
            'api_errors': e.api_errors if hasattr(e, 'api_errors') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'Publish failed',
            'message': str(e)
        }

def print_result(result: Dict):
    """Print publish result"""
    print("\n" + "=" * 60)
    
    if result.get('success'):
        print("✅ Tweet published successfully!")
        print("=" * 60)
        print(f"📝 Tweet ID: {result['tweet_id']}")
        print(f"🔗 URL: {result['url']}")
        print(f"⏰ Created At: {result['created_at']}")
        print(f"📄 Preview: {result['text'][:100]}{'...' if len(result['text']) > 100 else ''}")
    else:
        print("❌ Tweet publishing failed")
        print("=" * 60)
        print(f"Error Type: {result.get('error', 'Unknown')}")
        print(f"Error Message: {result.get('message', 'No message')}")
        
        if result.get('api_errors'):
            print("\nAPI Detailed Errors:")
            for error in result['api_errors']:
                print(f"  - {error.get('message', 'Unknown error')}")
                if 'code' in error:
                    print(f"    Error Code: {error['code']}")
    
    print("=" * 60)

def get_user_info(client) -> Optional[Dict]:
    """Get current user information"""
    try:
        # Need to specify user_fields to get public_metrics
        user = client.get_me(user_fields=['public_metrics', 'username', 'name'])
        if user and user.data:
            # Safely get public_metrics
            public_metrics = getattr(user.data, 'public_metrics', {}) or {}
            return {
                'id': user.data.id,
                'username': getattr(user.data, 'username', 'unknown'),
                'name': getattr(user.data, 'name', 'Unknown'),
                'followers_count': public_metrics.get('followers_count', 0),
                'following_count': public_metrics.get('following_count', 0),
                'tweet_count': public_metrics.get('tweet_count', 0)
            }
        return None
    except Exception as e:
        print(f"⚠️  Failed to get user info: {e}")
        return None

def validate_credentials(client_data) -> bool:
    """Verify if authentication credentials are valid"""
    try:
        client = client_data['client']
        user_info = get_user_info(client)
        
        if user_info:
            print(f"\n✅ Authentication successful!")
            print(f"👤 Username: @{user_info['username']}")
            print(f"📛 Display Name: {user_info['name']}")
            print(f"👥 Followers: {user_info['followers_count']:,}")
            print(f"📝 Tweets: {user_info['tweet_count']:,}")
            return True
        else:
            print("\n❌ Authentication failed: Unable to retrieve user information")
            return False
            
    except Exception as e:
        print(f"\n❌ Authentication verification failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='X (Twitter) Tweet Publishing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish text-only tweet
  %(prog)s tweet "Hello, X!"

  # Publish tweet with image
  %(prog)s tweet "Check out this image!" --media /path/to/image.jpg

  # Publish tweet with multiple media
  %(prog)s tweet "My photos:" --media /path/to/photo1.jpg --media /path/to/photo2.png

  # Publish tweet with video
  %(prog)s tweet "Watch this video!" --media /path/to/video.mp4

  # Verify authentication
  %(prog)s verify
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # tweet command
    tweet_parser = subparsers.add_parser('tweet', help='Publish a tweet')
    tweet_parser.add_argument('text', help='Tweet content')
    tweet_parser.add_argument('--media', '-m', action='append',
                             help='Media file path (can be used multiple times, max 4)')
    tweet_parser.add_argument('--reply-to', '-r', default=None,
                             help='Tweet ID to reply to (for threading)')
    
    # verify command
    subparsers.add_parser('verify', help='Verify authentication credentials')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if not TWEEPY_AVAILABLE:
        print("\n❌ Please install tweepy first:")
        print("   pip3 install tweepy --user")
        return
    
    # Get client
    client_data = get_client_data()
    if not client_data:
        return
    
    if args.command == 'verify':
        validate_credentials(client_data)
    
    elif args.command == 'tweet':
        # Verify authentication
        if not validate_credentials(client_data):
            return
        
        client = client_data['client']
        api = client_data['api']
        
        # Upload media
        media_ids = []
        if args.media:
            if len(args.media) > 4:
                print("⚠️  Maximum 4 media files supported, will only use the first 4")
                args.media = args.media[:4]
            
            for media_path in args.media:
                media_id = upload_media(api, media_path)
                if media_id:
                    media_ids.append(media_id)
            
            if args.media and not media_ids:
                print("❌ All media uploads failed, stopping publish")
                return
        
        # Publish tweet
        print(f"\n📤 Publishing tweet...")
        result = publish_tweet(client, args.text, media_ids, reply_to=args.reply_to)
        
        # Print result
        print_result(result)
        
        # Output JSON format (for programmatic processing)
        if result.get('success'):
            print("\n📋 JSON Output:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

def wait_a_while():
    import time
    time.sleep(10)

if __name__ == '__main__':
    main()
    wait_a_while()
