# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is not an application — it is a **Claude Code skill package** published to the clawhub.ai registry (slug: `x-publisher`, see `_meta.json` and `.clawhub/origin.json`). It publishes tweets to X (Twitter) using the Tweepy library. The skill manifest and user-facing docs live in `SKILL.md`; the implementation lives in `scripts/`.

Because this is a skill, the consumer's experience is `SKILL.md` → running `scripts/x_publisher`. When changing behavior, keep `SKILL.md` (usage, examples, limits tables) in sync with the script.

## Commands

Dependency: `tweepy` (installed automatically into `.venv/` by the `scripts/x_publisher` / `scripts/post_thread` wrappers — no manual `pip install`).

```bash
# Verify credentials + show account info (run this first in a new environment)
scripts/x_publisher verify

# Text-only tweet
scripts/x_publisher tweet "Hello, X!"

# Tweet with media (repeat --media up to 4×; images or a single video)
scripts/x_publisher tweet "caption" --media /path/to/file.jpg

# Reply / thread (links tweet to an existing tweet ID)
scripts/x_publisher tweet "reply text" --reply-to <tweet_id>

# Post a multi-tweet thread in one command (chains replies)
scripts/post_thread "First tweet." "Second tweet." "Third tweet."
```

There is no test suite, linter, or build step. To validate a change, run `verify` and publish a test tweet.

## Architecture

### Auth (env-var only, no external files)
`get_client_data()` in `scripts/x_publisher.py` is the single auth entry point — shared with `post_thread.py` via import. It reads **only environment variables**; the skill has no dependency on any config file (no `~/.openclaw/openclaw.json`, no `.env` parsing). Whatever runtime launches the skill is responsible for populating the environment (e.g. sourcing a `.env`), and `SKILL.md` only instructs users to set the four env vars.

The four OAuth 1.0a user-context credentials, all required to sign the write operations (`create_tweet`, `media_upload`) and `get_me`: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`. There is no bearer-token/App-Only path — it was removed because every operation here requires user-context auth, so a bearer token would be dead weight. (Verified against `oauthlib`/`tweepy` source: oauthlib documents `client_key` as mandatory and the signature step crashes without it; `OAuth1UserHandler.__init__` takes `consumer_key, consumer_secret` as required positional params.) `X_HTTP_PROXY` (optional env var) sets `http_proxy`/`https_proxy` globally before constructing the client — needed because the X API is often unreachable without a proxy from some environments.

`get_client_data()` returns a dict `{'client', 'api', 'auth'}`:
- `client` — v2 `tweepy.Client` (`wait_on_rate_limit=True`) used for `create_tweet`, `get_me`.
- `api` — v1.1 `tweepy.API` (`OAuth1UserHandler`) required for `media_upload`, including chunked upload for videos (`media_category='tweet_video'`).
- `auth` — the `OAuth1UserHandler`, retained for parity but not consumed downstream.

Both surfaces must be authenticated with the same OAuth 1.0a credentials. `tweepy` is imported under a try/except at module top so the script can print install guidance instead of crashing on `ImportError`; `publish_tweet` still references `tweepy.errors.*` exception classes (only reached when `get_client_data()` succeeds, so `tweepy` is guaranteed loaded).

### Tweet flow (`main` → `publish_tweet`)
`validate_credentials` runs `get_me` before every publish (auth guard + prints account info). Media is uploaded one file at a time, collecting `media_id_string`s, then passed as `media_ids` to `create_tweet`. On success the script prints a human-readable block followed by a JSON object on stdout (the JSON block is the contract for programmatic callers — see the integration example in `SKILL.md`). On failure, `publish_tweet` catches `Forbidden` / `Unauthorized` / `TooManyRequests` and returns a structured error dict instead of raising.

### Threading (`scripts/post_thread.py`)
A reusable CLI that posts a multi-tweet thread by chaining replies — each tweet is `create_tweet(text, in_reply_to_tweet_id=<previous_id>)`. Tweet texts come from positional args (one per tweet) or, if none are given, one per line from stdin. It imports `get_client_data`, `get_user_info`, and `validate_credentials` from `x_publisher.py`, so both scripts share one auth path. For a single reply to an existing tweet, `scripts/x_publisher tweet ... --reply-to <id>` is enough; `post_thread.py` is for posting a fresh thread in one command.

## Skill-specific notes

- `SKILL.md` frontmatter declares the required `env:` vars; these are what the skill loader expects to be populated in the environment before the script runs.
- `references/x_api.md` is a demand-loaded reference (Tweepy methods, error codes, rate limits) — consult it when extending API usage rather than re-deriving from scratch.
- Tweet text >280 chars is truncated to 277 + `"...publish"` (not a clean cut). If you change truncation, update the "Tweet length" note in `SKILL.md`.
- The `wait_a_while()` tail (10s sleep) is intentional in `x_publisher.py` — do not remove it without checking the skill's runtime expectations.
