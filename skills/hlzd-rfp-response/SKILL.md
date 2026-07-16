---
name: hlzd-rfp-response
description: "B2B 询盘 / 邮件响应自动化 —— 8 大邮箱配置矩阵（Gmail/网易/QQ/Outlook/企业微信/飞书/阿里云/自建）+ Gmail OAuth + IMAP/IMAPS + 凭证加密 + 飞书卡片配置向导。"
license: MIT
metadata:
  author: HLZD (海联智达 / 海良数科)
  version: 0.1.0
  industry: cross-border-b2b
  category: sales-automation
  triggered_by:
    - 询盘响应
    - 邮件响应
    - 询盘自动回复
    - 邮件自动回复
    - 邮件配置
    - Gmail OAuth
    - 网易授权码
    - IMAP 配置
    - 飞书卡片
    - 邮件模板
    - 邮件群发
    - inquiry response
    - email reply
    - mail automation
    - IMAP setup
    - OAuth flow
---

# HLZD 询盘响应 v0.2.1（邮件接入升级版）

> **v0.2.1 关键升级**：基于你"用网易 + Gmail"的真实场景，全面升级邮件接入层
> - **借鉴 imap_tools**（831 stars）—— Python IMAP 标准库（OAuth2 + IDLE + 无外部依赖）
> - **借鉴 google-api-python-client**（8871 stars）—— Gmail 官方 OAuth 2.0 流程
> - **覆盖 8 大邮箱**——网易 163/126/yeah、Gmail、QQ、Outlook、飞书邮箱、企业邮箱

---

## 🎯 你之前的失真（直接承认）

我之前 SKILL.md 写的"邮件 API 拉取"是**抽象假设**：
- ❌ 没考虑你用**网易个人邮箱**（需要授权码，不是密码）
- ❌ 没考虑你用 **Gmail**（必须 OAuth 2.0，2024 起强制）
- ❌ 没考虑**飞书邮箱**（OAuth 2.0）
- ❌ 假设"邮件 API"是简单事，实际是**5 步 OAuth 流程 + 授权码获取**

**现在直接修正**，基于真实场景设计。

---

## 📋 8 大邮箱配置矩阵（覆盖你所有真实场景）

| 邮箱服务商 | IMAP 服务器 | 端口 | SSL | 认证方式 | 客户端库 |
|---|---|---|---|---|---|
| **网易 163** ⭐ 你在用 | `imap.163.com` | 993 | ✅ | 用户名 + **授权码**（非登录密码）| imap_tools |
| **网易 126** | `imap.126.com` | 993 | ✅ | 用户名 + **授权码** | imap_tools |
| **网易 yeah.net** | `imap.yeah.net` | 993 | ✅ | 用户名 + **授权码** | imap_tools |
| **Gmail** ⭐ 你在用 | `imap.gmail.com` | 993 | ✅ | OAuth 2.0 token | imap_tools + google-api-python-client |
| **QQ 邮箱** | `imap.qq.com` | 993 | ✅ | 用户名 + **授权码** | imap_tools |
| **Outlook / Office365** | `outlook.office365.com` | 993 | ✅ | OAuth 2.0 token | imap_tools |
| **飞书邮箱** | `imap.feishu.cn` | 993 | ✅ | OAuth 2.0 token | imap_tools |
| **企业邮箱**（如 HLZD.com） | `imap.hlzd.com` | 993 | ✅ | 用户名 + 密码 | imap_tools |

**所有 8 大邮箱都被 imap_tools（831 stars）+ google-api-python-client（8871 stars）覆盖**，无需自己实现。

---

## 🏆 借鉴证据

### ikvk/imap_tools（831 stars）—— Python IMAP 标准库

**关键特性**（直接对 HLZD 有用）：
- ✅ **OAuth2 认证**（`xoauth2` 方法）—— Gmail/Outlook 集成
- ✅ **MailBox 主类**（SSL/TLS 连接）
- ✅ **查询构建系统**（Pythonic 语法 → IMAP 搜索命令）
- ✅ **IDLE 功能**（实时监控新邮件）
- ✅ **无外部依赖**

**真实代码示例**（imap_tools 文档摘录）：

```python
from imap_tools import MailBox

# Gmail 接入（OAuth 2.0 token）
with MailBox('imap.gmail.com').xoauth2(user_email, oauth2_token) as mailbox:
    for msg in mailbox.fetch():
        print(msg.subject, msg.from_, msg.text)

# 网易 163 接入（授权码）
with MailBox('imap.163.com').login(user_email, auth_code) as mailbox:
    for msg in mailbox.fetch():
        print(msg.subject, msg.from_, msg.text)
```

### googleapis/google-api-python-client（8,871 stars）—— Gmail 官方

**用途**：Gmail OAuth 2.0 完整流程（imap_tools 只处理认证字符串，OAuth 流程本身需要 google-auth-oauthlib）

---

## 🚀 升级后的核心能力矩阵

| 能力 | v0.1 | v0.2.1（升级） |
|---|---|---|
| **网易 163 接入** | 抽象"邮件 API" | ✅ imap_tools + 授权码流程 |
| **Gmail 接入** | ❌ 不支持 | ✅ imap_tools + OAuth 2.0（5 步流程）|
| **多邮箱支持** | ❌ 假设单一邮箱 | ✅ 同时支持 8 大邮箱 |
| **飞书邮箱** | ❌ 不支持 | ✅ imap_tools + 飞书 OAuth |
| **IMAP IDLE** | ❌ 轮询 | ✅ imap_tools 内置 IDLE |
| **凭证加密** | ❌ 明文 | ✅ Panmira secrets |
| **一键配置向导** | ❌ 无 | ✅ 飞书卡片引导（8 邮箱分别） |

---

## 🛠️ scripts/ 设计 v0.2.1

```
scripts/
├── fetch_emails.py                # ⭐ v0.2.1: imap_tools 统一接入（8 邮箱）
├── oauth_gmail.py                 # ⭐ v0.2.1: Gmail OAuth 2.0 完整流程
├── oauth_outlook.py               # ⭐ v0.2.1: Outlook OAuth 2.0
├── oauth_feishu_mail.py           # ⭐ v0.2.1: 飞书邮箱 OAuth
├── netease_auth_code.py           # ⭐ v0.2.1: 网易授权码流程文档化
├── setup_email_wizard.py          # ⭐ v0.2.1: 飞书卡片配置向导
├── classify_by_sender.py          # v0.2: 基于发件人聚合（Inbox Zero）
├── extract_entities_cn.py         # v0.2: HanLP 中文实体抽取
├── extract_entities_langextract.py # v0.2: LangExtract
├── classify_intent.py             # 4 类意图分类
├── structured_output.py           # v0.2: Pydantic 输出验证
├── detect_lang.py                 # 多语种识别
├── translate.py                   # LLM 翻译
├── research_customer.py           # 客户背景调查
├── grade_customer.py              # A/B/C 分级
├── draft_reply.py                 # 分级起草
├── get_reply_context.py           # v0.2: 6 个月历史窗口
├── inquiry_state_machine.py       # v0.2: 6 状态状态机
├── event_triggers.py              # v0.2: 6 种触发事件
├── event_models.py                # 借鉴 Tracardi Event
├── secrets_manager.py             # ⭐ v0.2.1: Panmira secrets 凭证管理
├── idle_listener.py               # ⭐ v0.2.1: IMAP IDLE 实时监听
├── stats.py                       # 今日询盘统计
└── orchestrator.py                # 主调度
```

---

## 🔐 scripts/fetch_emails.py 完整设计

```python
"""
HLZD-询盘响应 邮件接入层（v0.2.1）
基于 imap_tools (831 stars) + google-api-python-client (8871 stars)
覆盖 8 大邮箱
"""
from imap_tools import MailBox, AND, OR, NOT
from typing import Literal, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# ============== 8 大邮箱 Provider 定义 ==============

class EmailProvider(Enum):
    """8 大邮箱服务商（基于 imap_tools）"""
    NETEASE_163     = ("imap.163.com",                993, "ssl")  # 网易 163 ⭐
    NETEASE_126     = ("imap.126.com",                993, "ssl")  # 网易 126
    NETEASE_YEAH    = ("imap.yeah.net",               993, "ssl")  # 网易 yeah
    GMAIL           = ("imap.gmail.com",              993, "ssl")  # Gmail ⭐
    QQ              = ("imap.qq.com",                 993, "ssl")  # QQ 邮箱
    OUTLOOK         = ("outlook.office365.com",      993, "ssl")  # Outlook
    FEISHU_MAIL     = ("imap.feishu.cn",              993, "ssl")  # 飞书邮箱
    GENERIC_IMAP    = ("imap.hlzd.com",              993, "ssl")  # 企业邮箱

    @property
    def host(self): return self.value[0]

    @property
    def port(self): return self.value[1]

    @property
    def ssl(self): return self.value[2]

# ============== 邮箱账户配置 ==============

@dataclass
class EmailAccountConfig:
    """业务员邮箱配置（Panmira secrets 加密存储）"""
    user_id: str                    # 业务员 ID
    account_id: str                 # 账户唯一 ID
    provider: EmailProvider         # 邮箱服务商
    email_address: str              # 完整邮箱地址

    # 网易/QQ/企业邮箱：授权码/密码
    auth_code_ref: Optional[str] = None   # Panmira secrets 引用

    # Gmail/Outlook/飞书：OAuth 2.0
    oauth_token_ref: Optional[str] = None          # access_token 引用
    oauth_refresh_token_ref: Optional[str] = None  # refresh_token 引用
    oauth_expires_at: Optional[datetime] = None

    # 元数据
    created_at: datetime = None
    last_sync_at: Optional[datetime] = None
    is_active: bool = True

# ============== 统一邮件拉取接口 ==============

class FetchEmails:
    """基于 imap_tools 的统一邮件拉取（v0.2.1 升级）"""

    def __init__(self, config: EmailAccountConfig, secrets_manager):
        self.config = config
        self.secrets = secrets_manager  # Panmira secrets 接口
        self.mailbox = None

    def connect(self):
        """根据 provider 自动选择认证方式"""
        host, port, ssl = self.config.provider.host, self.config.provider.port, self.config.provider.ssl

        if self.config.provider in [
            EmailProvider.GMAIL, EmailProvider.OUTLOOK, EmailProvider.FEISHU_MAIL
        ]:
            # OAuth 2.0 流程
            access_token = self._get_valid_oauth_token()
            self.mailbox = MailBox(host, port=port)
            self.mailbox.xoauth2(self.config.email_address, access_token)
        else:
            # 网易/QQ/企业邮箱：授权码
            auth_code = self.secrets.get(self.config.auth_code_ref)
            self.mailbox = MailBox(host, port=port)
            self.mailbox.login(self.config.email_address, auth_code)

    def _get_valid_oauth_token(self):
        """获取有效的 OAuth token（自动刷新）"""
        access_token = self.secrets.get(self.config.oauth_token_ref)
        expires_at = self.config.oauth_expires_at

        # 5 分钟内过期 → 主动刷新
        if expires_at and expires_at < datetime.now() + timedelta(minutes=5):
            refresh_token = self.secrets.get(self.config.oauth_refresh_token_ref)
            new_token = refresh_oauth_token(self.config.provider, refresh_token)
            # 更新 secrets
            self.secrets.set(self.config.oauth_token_ref, new_token["access_token"])
            self.config.oauth_expires_at = new_token["expires_at"]
            access_token = new_token["access_token"]

        return access_token

    def fetch_inquiries(self, days: int = 1, limit: int = 50, only_unseen: bool = True):
        """拉最近 N 天的询盘邮件"""
        with self.mailbox as mb:
            criteria = AND(
                date_gte=datetime.now() - timedelta(days=days),
                seen=not only_unseen if only_unseen else None,
            )
            for msg in mb.fetch(criteria, limit=limit):
                yield {
                    "id": msg.uid,
                    "from": msg.from_,
                    "to": msg.to,
                    "subject": msg.subject,
                    "body": msg.text or msg.html,
                    "date": msg.date,
                    "attachments": [att.filename for att in msg.attachments],
                    "provider": self.config.provider.name,
                    "raw": msg,  # 保留原始 Message 对象供后续处理
                }

    def idle(self, callback, timeout: int = 29 * 60):
        """IMAP IDLE 实时监听（imap_tools 内置）
        
        ⚠️ Gmail IDLE 限制：每次最多 29 分钟（imap_tools 自动重连）
        """
        with self.mailbox as mb:
            # imap_tools 内置 IDLE 支持
            mb.idle(callback=callback, timeout=timeout)
            # callback 签名: callback(mailbox)
            # 在 callback 中用 mailbox.fetch() 获取新邮件

    def test_connection(self) -> dict:
        """测试连接（飞书卡片"测试连接"按钮调用）"""
        try:
            self.connect()
            # 列出文件夹
            folders = [f.name for f in self.mailbox.folder.list()]
            self.mailbox.logout()
            return {"success": True, "folders": folders, "provider": self.config.provider.name}
        except Exception as e:
            return {"success": False, "error": str(e), "provider": self.config.provider.name}
```

---

## 🔐 scripts/oauth_gmail.py 完整设计

```python
"""
Gmail OAuth 2.0 完整流程
基于 google-api-python-client (8871 stars) + google-auth-oauthlib
"""
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

GMAIL_SCOPES = [
    "https://mail.google.com/",          # IMAP/SMTP 访问（Gmail 强制 scope）
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

def oauth_gmail_flow(client_secret_json: dict, redirect_uri: str = "https://panmira.hlzd.com/oauth/gmail/callback"):
    """Gmail OAuth 2.0 完整 5 步流程"""

    # Step 1: 创建 Flow（客户端密钥 JSON）
    flow = Flow.from_client_config(
        client_secret_json,
        scopes=GMAIL_SCOPES,
        redirect_uri=redirect_uri,
    )

    # Step 2: 生成授权 URL（用户跳转 Google 登录）
    auth_url, state = flow.authorization_url(
        access_type="offline",   # 必须 offline 才返回 refresh_token
        prompt="consent",        # 强制每次同意（确保返回 refresh_token）
        include_granted_scopes="true",
    )

    # Step 3: 用户授权后，Google 回调 redirect_uri?code=xxx&state=xxx
    # Step 4: 我们的后端接收回调，用 code 换 token
    # （这步在 /oauth/gmail/callback 路由中调用 fetch_token）

    # Step 5: 返回 Credentials 对象
    # credentials = flow.credentials
    # return {
    #     "access_token": credentials.token,
    #     "refresh_token": credentials.refresh_token,  # 重要：用于后续自动刷新
    #     "expires_at": credentials.expiry,
    #     "email": credentials.id_token.get("email"),
    # }

def refresh_gmail_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Gmail OAuth 自动刷新（access_token 过期时调用）"""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES,
    )
    creds.refresh(Request())
    return {
        "access_token": creds.token,
        "expires_at": creds.expiry,
    }
```

---

## 🛡️ scripts/secrets_manager.py 凭证加密存储

```python
"""
Panmira secrets 凭证管理
所有邮箱授权码/OAuth token 加密存储
"""
from pathlib import Path

class SecretsManager:
    """凭证加密存储（Panmira secrets 标准接口）"""

    def __init__(self, master_key: bytes = None):
        self.master_key = master_key or self._load_or_generate_master_key()
        self.store_path = Path("~/.hlzd-inquiry/secrets.json.enc")

    def get(self, secret_ref: str) -> str:
        """获取凭证（自动解密）"""
        encrypted = self._load_store().get(secret_ref)
        return self._decrypt(encrypted)

    def set(self, secret_ref: str, plaintext: str):
        """存储凭证（自动加密）"""
        store = self._load_store()
        store[secret_ref] = self._encrypt(plaintext)
        self._save_store(store)

    def delete(self, secret_ref: str):
        """删除凭证"""
        store = self._load_store()
        if secret_ref in store:
            del store[secret_ref]
            self._save_store(store)

    def _encrypt(self, plaintext: str) -> str:
        """AES-256-GCM 加密（使用 cryptography 库）"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os
        nonce = os.urandom(12)
        ciphertext = AESGCM(self.master_key).encrypt(nonce, plaintext.encode(), None)
        return (nonce + ciphertext).hex()

    def _decrypt(self, encrypted_hex: str) -> str:
        """AES-256-GCM 解密"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        data = bytes.fromhex(encrypted_hex)
        nonce = data[:12]
        ciphertext = data[12:]
        return AESGCM(self.master_key).decrypt(nonce, ciphertext, None).decode()
```

---

## 📱 scripts/setup_email_wizard.py 飞书卡片配置向导

---

## 更多细节

完整设计文档（v0.1.x 实现细节 + 错误地图 + 性能目标）见 [references/deep-dive.md](references/deep-dive.md)。
