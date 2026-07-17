# X（Twitter）发布工具

一个通过官方 [Tweepy](https://docs.tweepy.org/) 库向 X（Twitter）发布推文的命令行小工具（同时也是 Claude Code 技能）。支持纯文本推文、带图片或视频的推文、以回复方式串联的**串推（thread）**，以及凭证验证——并返回详细的发布结果（推文 ID、URL），同时输出一段可供程序化处理的 JSON。

本项目以 [clawhub](https://clawhub.ai) 技能包（`x-publisher`）的形式发布，但 `scripts/` 下的脚本可独立运行，仅需 Python + Tweepy 以及四个环境变量。

## 功能

- 📝 **纯文本推文** —— 快速单条发布
- 🖼️ **图片支持** —— JPG、PNG、GIF、WebP（单条最多 4 张）
- 🎬 **视频支持** —— MP4、MOV、AVI、WebM（分块上传）
- 🧵 **串推（Thread）** —— 一条命令发布多推串联的串推
- 📊 **详细结果** —— 推文 ID、URL、创建时间，并输出 JSON 对象
- ✅ **凭证验证** —— 发布前确认 X API 凭证是否可用

## 前置条件

### 1. 安装 Tweepy

```bash
pip3 install tweepy --user
```

### 2. 获取 X API 凭证

1. 访问 [X 开发者门户](https://developer.twitter.com/en/portal/dashboard)。
2. 创建项目并生成 API 密钥。
3. 确保应用具备 **Read and Write（读写）** 权限。
4. 获取以下四项 **OAuth 1.0a 用户上下文** 凭证：
   - API Key（consumer key / 消费者密钥）
   - API Secret（consumer secret / 消费者密钥密文）
   - Access Token（访问令牌）
   - Access Token Secret（访问令牌密文）

> 四项均为必需。OAuth 1.0a 对每个请求的签名由“消费者密文”与“令牌密文”组合而成，因此消费者密钥对与访问令牌对都不可缺一——本工具不使用 bearer token / 应用级只读路径，因为发布推文、上传媒体、`get_me` 都要求用户上下文认证。

### 3. 配置环境变量

脚本**仅从环境变量读取**凭证，不解析任何配置文件。运行前请先设置以下四个变量（写入 shell 配置，或从 `.env` 文件导出）：

```bash
export X_API_KEY="your-api-key"
export X_API_SECRET="your-api-secret"
export X_ACCESS_TOKEN="your-access-token"
export X_ACCESS_TOKEN_SECRET="your-access-token-secret"
```

若将凭证保存在当前目录的 `.env` 文件中，请先将其载入环境：

```bash
set -a && . ./.env && set +a
```

可选：若网络无法直连 X API，请设置 `X_HTTP_PROXY`。

## 用法

### 验证凭证

在新环境中先运行此命令，确认认证成功并查看账号信息：

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

### 发布纯文本推文

```bash
python3 scripts/x_publisher.py tweet "Hello, X! This is my first tweet."
```

### 发布带媒体的推文

```bash
# 单张图片
python3 scripts/x_publisher.py tweet "Check out this photo!" --media /path/to/image.jpg

# 最多 4 张图片
python3 scripts/x_publisher.py tweet "My photo collection:" \
  --media /path/to/photo1.jpg \
  --media /path/to/photo2.png \
  --media /path/to/photo3.gif

# 视频
python3 scripts/x_publisher.py tweet "Watch this!" --media /path/to/video.mp4
```

### 回复已有推文

```bash
python3 scripts/x_publisher.py tweet "A reply." --reply-to <tweet_id>
```

### 发布串推（Thread）

`scripts/post_thread.py` 可一条命令发布多推串联的串推，每条推文作为上一条的回复。推文内容来自位置参数（每条推文一个参数）；若未提供参数，则从标准输入读取（每行一条推文，空行跳过）。

```bash
# 用参数发布串推
python3 scripts/post_thread.py "串推第一条。" "第二条。" "第三条。"

# 从标准输入发布串推
printf '第一条。\n第二条。\n第三条。\n' | python3 scripts/post_thread.py
```

### 输出

发布成功时，工具会先打印一段可读信息，随后在标准输出打印 JSON 对象（该 JSON 是面向程序化调用方的稳定契约）：

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

`post_thread.py` 同样会逐条打印推文 ID，并输出串推链路摘要，以及包含 `tweet_ids`、`root_tweet_id`、`url`、`texts` 的 JSON 对象。

## 命令参考

| 命令 | 用途 | 示例 |
|---------|---------|---------|
| `verify` | 验证认证 | `x_publisher.py verify` |
| `tweet` | 发布一条推文 | `x_publisher.py tweet "Hello" --media photo.jpg` |
| （串推） | 发布回复串联的串推 | `post_thread.py "第一条" "第二条" "第三条"` |

### `tweet` 参数

| 参数 | 简写 | 说明 | 是否必填 |
|----------|-------|-------------|----------|
| `text` | - | 推文内容 | 是 |
| `--media` | `-m` | 媒体文件路径（可重复，最多 4 个） | 否 |
| `--reply-to` | `-r` | 要回复的推文 ID（用于串联） | 否 |

## 项目结构

```
x-publisher/
├── SKILL.md              # 技能清单与面向用户的文档（clawhub）
├── CLAUDE.md             # 在本仓库中作业的 Claude Code 指引
├── README.md             # 英文 README
├── README.zh-CN.md       # 中文 README（本文件）
├── _meta.json            # clawhub 包元数据
├── .clawhub/origin.json  # clawhub 注册表来源
├── references/
│   └── x_api.md          # X API / Tweepy 参考：方法、错误码、速率限制
└── scripts/
    ├── x_publisher.py    # tweet / media / verify 命令行；共享认证（get_client_data）
    └── post_thread.py    # 回复串联的串推命令行
```

## 架构（面向贡献者）

- **`get_client_data()`** 位于 `scripts/x_publisher.py`，是唯一的认证入口（`post_thread.py` 也会导入它）。它从环境变量读取四项 OAuth 1.0a 凭证，按需设置 `X_HTTP_PROXY`，并返回 `{'client', 'api', 'auth'}`。
- 使用两套 Tweepy 接口：
  - **v1.1**（`tweepy.API` / `OAuth1UserHandler`）—— 用于 `media_upload`，视频采用分块上传（`media_category='tweet_video'`）。
  - **v2**（`tweepy.Client`，开启 `wait_on_rate_limit=True`）—— 用于 `create_tweet` 与 `get_me`。
- 两套接口共用同一组 OAuth 1.0a 凭证。
- 每次发布前，`validate_credentials` 都会调用 `get_me`。失败时 `publish_tweet` 会捕获 `Forbidden` / `Unauthorized` / `TooManyRequests`，返回结构化的错误字典，而不是抛出异常。
- 推文文本超过 280 字符时会被截断为 277 + `"...publish"`。

## API 限制

| 限制 | 取值 |
|-------|-------|
| 推文长度 | 280 字符（超出则截断） |
| 单条媒体数 | 4 张图片和/或视频 |
| 图片大小上限 | 5 MB |
| 视频大小上限 | 512 MB |
| 视频时长上限 | 2 分 20 秒 |
| 发布频率 | 15 分钟内 300 条（受限流） |

## 错误处理

| 错误 | 原因 | 解决 |
|-------|-------|-----|
| 认证失败 | 密钥/令牌错误或过期 | 检查凭证；确认令牌未过期 |
| 权限不足 | 应用无写入权限，或内容违反 X 规则 | 在开发者门户开启写入权限 |
| 触发限流 | 15 分钟内超过 300 条 | 等待几分钟后重试 |
| 媒体文件未找到/过大 | 路径错误或超出大小限制 | 核对路径、格式与大小 |

完整的 X API 错误码与限流窗口见 `references/x_api.md`。

## 注意事项

- **凭证安全** —— 凭证只应存放在环境变量（或已 gitignore 的 `.env`）中，切勿提交到代码库。
- **内容合规** —— 遵守 X 平台规则。
- **频率控制** —— 注意 15 分钟 300 条的限流。
- **媒体版权** —— 确保上传的媒体已获授权或自有版权。

## 参考

- Tweepy：https://docs.tweepy.org/
- X API v2：https://docs.x.com/x-api
- X 开发者门户：https://developer.twitter.com/en/portal/dashboard
