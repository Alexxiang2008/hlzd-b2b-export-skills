# hlzd-rfp-response — Deep Dive

> 本文件收纳 SKILL.md 因 500 行约束移出的细节章节，仅供 deep-load 参考。


```python
"""
飞书 IM 卡片配置向导
用户点击飞书卡片按钮 → 引导配置邮箱
"""
from enum import Enum

class EmailSetupStep(Enum):
    SELECT_PROVIDER = 1      # 选择邮箱服务商
    AUTH_NETEASE = 2          # 网易授权码流程
    OAUTH_GMAIL = 3           # Gmail OAuth 流程
    OAUTH_OUTLOOK = 4         # Outlook OAuth 流程
    OAUTH_FEISHU = 5          # 飞书邮箱 OAuth 流程
    TEST_CONNECTION = 6       # 测试连接
    SUCCESS = 7                # 配置成功

def email_setup_card(user_id: str, step: EmailSetupStep = EmailSetupStep.SELECT_PROVIDER):
    """生成飞书卡片（按当前步骤）"""
    if step == EmailSetupStep.SELECT_PROVIDER:
        return {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "🔗 绑定询盘邮箱"}},
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": "请选择你的邮箱服务商"}},
                    {"tag": "action", "actions": [
                        {"tag": "button", "text": {"content": "📧 网易 163/126"}, "value": {"step": "AUTH_NETEASE", "provider": "netease"}},
                        {"tag": "button", "text": {"content": "📧 Gmail"}, "value": {"step": "OAUTH_GMAIL"}},
                        {"tag": "button", "text": {"content": "📧 QQ 邮箱"}, "value": {"step": "AUTH_NETEASE", "provider": "qq"}},
                        {"tag": "button", "text": {"content": "📧 Outlook"}, "value": {"step": "OAUTH_OUTLOOK"}},
                        {"tag": "button", "text": {"content": "📧 飞书邮箱"}, "value": {"step": "OAUTH_FEISHU"}},
                        {"tag": "button", "text": {"content": "📧 企业邮箱"}, "value": {"step": "AUTH_NETEASE", "provider": "imap"}},
                    ]}
                ]
            }
        }

    elif step == EmailSetupStep.AUTH_NETEASE:
        return {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "📧 网易邮箱配置"}},
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content":
                        "**3 步完成配置**：\n\n"
                        "**Step 1**: 登录 https://mail.163.com\n"
                        "**Step 2**: 设置 → POP3/SMTP/IMAP → 开启 IMAP/SMTP 服务\n"
                        "**Step 3**: 客户端授权密码 → 生成授权码（手机短信验证）\n\n"
                        "把生成的授权码填在下面："
                    }},
                    {"tag": "input", "name": "email", "placeholder": {"tag": "plain_text", "content": "your_email@163.com"}},
                    {"tag": "input", "name": "auth_code", "placeholder": {"tag": "plain_text", "content": "授权码（非登录密码）"}},
                    {"tag": "action", "actions": [
                        {"tag": "button", "text": {"content": "🔗 测试连接"}, "type": "primary", "value": {"step": "TEST_CONNECTION"}},
                    ]}
                ]
            }
        }

    elif step == EmailSetupStep.OAUTH_GMAIL:
        return {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "📧 Gmail 配置（OAuth 2.0）"}},
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content":
                        "**点击下方按钮跳转到 Google 授权页面**：\n\n"
                        "授权后 HLZD-询盘响应 即可访问你的 Gmail 询盘邮件。\n"
                        "**不会发送邮件**，只读取。"
                    }},
                    {"tag": "action", "actions": [
                        {"tag": "button", "text": {"content": "🔐 跳转 Google 授权"}, "type": "primary", "url": "https://panmira.hlzd.com/oauth/gmail/start"}},
                    ]}
                ]
            }
        }

    elif step == EmailSetupStep.TEST_CONNECTION:
        # 飞书卡片交互回调：执行 test_connection
        # 返回成功/失败卡片
        ...
```

---

## 📚 references/ 设计 v0.2.1

```
references/
├── email_setup_guide.md           # ⭐ v0.2.1: 8 大邮箱配置教程
│   ├── 网易 163 授权码获取步骤（带截图描述）
│   ├── Gmail OAuth 流程图
│   ├── Outlook OAuth 流程
│   ├── 飞书邮箱 OAuth
│   ├── QQ 邮箱授权码获取
│   └── 企业邮箱配置
├── imap_servers.md                # ⭐ v0.2.1: 8 大邮箱 IMAP 服务器列表
├── oauth_flow_diagrams.md         # ⭐ v0.2.1: OAuth 完整流程图
├── secrets_management.md          # ⭐ v0.2.1: Panmira secrets 加密规范
├── netease_auth_code_steps.md     # ⭐ v0.2.1: 网易授权码 5 步获取流程
├── gmail_oauth_setup.md           # ⭐ v0.2.1: Gmail OAuth 项目配置（Google Cloud Console）
├── inquiry_categories.md          # v0.1 保留
├── grade_rubric.md                # v0.1 保留
├── reply_templates.md             # v0.1 保留
├── state_machine_diagram.md       # v0.2 保留
├── event_triggers.md              # v0.2 保留
├── sender_grouping_strategy.md   # v0.2 保留
├── reply_context_6months.md       # v0.2 保留
├── hanlp_chinese_ner.md           # v0.2 保留
├── langextract_patterns.md       # v0.2 保留
├── multilingual_handling.md       # v0.1 保留
├── customer_research_sources.md   # v0.1 保留
├── cultural_etiquette.md          # v0.1 保留
└── examples/
    ├── case_chinese_inquiry.md
    ├── case_english_inquiry.md
    ├── case_russian_inquiry.md
    ├── case_arabic_inquiry.md
    ├── case_sender_grouping.md
    ├── case_state_transitions.md
    ├── case_grade_a_reply.md
    ├── case_grade_b_reply.md
    ├── case_grade_c_reply.md
    └── case_spam_handling.md
```

---

## 🔑 Gmail OAuth 完整配置（Google Cloud Console）

```bash
# 1. 创建 Google Cloud 项目
# https://console.cloud.google.com/projectcreate
# 项目名: HLZD-Inquiry-Response

# 2. 启用 Gmail API
# APIs & Services → Library → 搜索 "Gmail API" → Enable

# 3. 配置 OAuth 同意屏幕
# APIs & Services → OAuth consent screen
# - User type: External
# - App name: HLZD 询盘响应
# - Scopes: ../auth/gmail.readonly, openid, ../auth/userinfo.email
# - Test users: 添加业务员邮箱

# 4. 创建 OAuth 2.0 Client ID
# APIs & Services → Credentials → Create Credentials → OAuth client ID
# - Application type: Web application
# - Authorized redirect URIs: https://panmira.hlzd.com/oauth/gmail/callback

# 5. 下载 client_secret.json
# → 保存到 Panmira secrets: gmail_client_secret
```

---

## 🛠️ 网易授权码获取完整步骤（图文）

```
Step 1: 登录 https://mail.163.com

Step 2: 顶部菜单 → 设置 → POP3/SMTP/IMAP
        ↓
        勾选 ✅ IMAP/SMTP 服务
        勾选 ✅ IMAP 协议（推荐）
        ↓
        保存

Step 3: 顶部菜单 → 设置 → 客户端授权密码
        ↓
        业务名称输入: HLZD 询盘响应
        ↓
        点击 "开启" → 弹出短信验证
        ↓
        输入手机收到的验证码
        ↓
        生成授权码（16 位字符，类似 ABCD-EFGH-IJKL-MNOP）

Step 4: 把授权码粘贴到 Panmira 飞书卡片表单
        ↓
        点击 "测试连接"
        ↓
        看到 ✅ "连接成功" → 配置完成
```

**关键点**：授权码**不是登录密码**，是网易提供的 IMAP 应用专用密码。

---

## ⚙️ 完整 Gmail OAuth 5 步流程

```
Step 1: 业务员在飞书 IM 收到 "绑定 Gmail" 卡片
        ↓ 点击 "跳转 Google 授权"
        ↓
Step 2: 浏览器跳转到 Google 授权页（mail.google.com）
        ↓ 业务员登录 + 选择授权范围
        ↓
Step 3: Google 回调到 https://panmira.hlzd.com/oauth/gmail/callback?code=xxx&state=xxx
        ↓
Step 4: Panmira 后端用 code 换 access_token + refresh_token
        ↓ 加密存储到 Panmira secrets
        ↓
Step 5: HLZD-询盘响应 启动 IMAP IDLE 监听
        ↓ 新询盘自动分类 + 起草回复
```

---

## 🔧 自动串联规则（v0.2.1 升级）

```markdown
## 自动串联

### 邮箱配置触发
- 飞书卡片 "绑定邮箱" 按钮 → setup_email_wizard.py → 多步配置
- OAuth 回调路由 /oauth/gmail/callback → 自动存储 token + 启动 IDLE

### IMAP IDLE 实时监听（v0.2.1 新增）
- 每邮箱一个 IDLE 监听进程
- 新邮件到达 → INQUIRY_RECEIVED 事件 → classify + translate + research + grade + draft
- Gmail IDLE 限制 29 分钟 → imap_tools 自动重连

### 凭证自动刷新
- OAuth access_token 过期前 5 分钟 → 自动用 refresh_token 刷新
- 网易授权码不刷新（如过期用户需重新输入）

### 上游（被谁触发）
- HLZD-日报助手: 每日 9:00 主动拉邮箱
- HLZD-询盘响应 IDLE: 实时监听新邮件
- HLZD-客户画像: 客户画像加载
- 飞书卡片: 业务员手动触发

### 下游
- INQUIRY_RECEIVED → classify → translate → research → grade → draft
- QUOTE_REQUEST 分类 → HLZD-智能报价
- LOGISTICS_INQUIRY 分类 → HLZD-物流装箱
- AFTER_SALE 分类 → HLZD-日报助手 标记紧急
- DEADLINE_APPROACHING → 升级主管
- AGENT_REPLIED → 更新 HLZD-客户画像 stats
```

---

## ✅ 验证清单 v0.2.1

- [ ] 网易 163 邮箱能拉取（用授权码）
- [ ] 网易 126 邮箱能拉取
- [ ] Gmail 能拉取（OAuth 2.0）
- [ ] QQ 邮箱能拉取（授权码）
- [ ] Outlook 能拉取（OAuth 2.0）
- [ ] 飞书邮箱能拉取（OAuth 2.0）
- [ ] 企业邮箱能拉取（密码）
- [ ] IMAP IDLE 实时监听生效
- [ ] OAuth token 自动刷新
- [ ] 飞书卡片配置向导可用
- [ ] 凭证加密存储（Panmira secrets）
- [ ] 错误提示友好（网易授权码错误 vs Gmail OAuth 错误分开提示）

---

## 🚀 性能目标 v0.2.1

| 路径 | v0.1 | v0.2.1 |
|---|---|---|
| 网易 163 拉取（10 封）| 不支持 | **< 5s** |
| Gmail 拉取（10 封）| 不支持 | **< 5s** |
| OAuth token 刷新 | 不支持 | **< 1s** |
| IMAP IDLE 响应 | 轮询（30s）| **< 1s**（实时）|
| 凭证加密 | 不支持 | **< 100ms** |
| 测试连接 | 不支持 | **< 2s** |

---

## ⚠️ 已知限制（v0.2.1 接受）

1. **Gmail IDLE 限制**：每次最多 29 分钟（imap_tools 自动重连，无缝处理）
2. **网易授权码过期**：需要用户重新输入（网易策略，无 OAuth 替代）
3. **企业邮箱 SSL 证书**：自建邮件服务器可能需要手动配置证书
4. **OAuth 客户端密钥**：需要 Google Cloud Console 配置（一次性）
5. **凭证备份**：Panmira secrets 损坏 = 重新配置（建议业务做本地备份）

---

## 🛣️ 后续路线

| 版本 | 新增 |
|---|---|
| v0.2.1 | ✅ **8 大邮箱接入** + imap_tools + google-api-python-client + Panmira secrets |
| **v0.3** | 飞书邮箱 IM 通道直连（不走 IMAP） |
| **v0.3** | 邮件附件 OCR（PDF/Word 询盘附件识别） |
| v0.4 | 邮件自动回复模板（业务员预设回复模板） |
| v0.4 | 多账号轮询（一个业务员多个邮箱） |

---

## 📂 文件位置

```
目标位置: ~/.claude/skills/hlzd-inquiry-response/
SKILL.md: ~/.claude/skills/hlzd-inquiry-response/SKILL.md
references/: ~/.claude/skills/hlzd-inquiry-response/references/
  ├── email_setup_guide.md           ⭐ v0.2.1
  ├── imap_servers.md                ⭐ v0.2.1
  ├── oauth_flow_diagrams.md         ⭐ v0.2.1
  ├── secrets_management.md          ⭐ v0.2.1
  ├── netease_auth_code_steps.md     ⭐ v0.2.1
  └── gmail_oauth_setup.md           ⭐ v0.2.1
scripts/: ~/.claude/skills/hlzd-inquiry-response/scripts/
  ├── fetch_emails.py                ⭐ v0.2.1: imap_tools 接入 8 邮箱
  ├── oauth_gmail.py                 ⭐ v0.2.1: Gmail OAuth 5 步流程
  ├── oauth_outlook.py               ⭐ v0.2.1
  ├── oauth_feishu_mail.py           ⭐ v0.2.1
  ├── netease_auth_code.py           ⭐ v0.2.1
  ├── secrets_manager.py             ⭐ v0.2.1: Panmira secrets
  ├── idle_listener.py               ⭐ v0.2.1: IMAP IDLE 实时监听
  └── setup_email_wizard.py          ⭐ v0.2.1: 飞书卡片配置向导
```

---

**END of HLZD-询盘响应 v0.2.1 SKILL.md**

**关键借鉴 2 个开源项目**：
- 🏆 **ikvk/imap_tools**（831 stars）—— Python IMAP 标准库（OAuth2 + IDLE + 查询构建 + 无外部依赖）
- 🏆 **google-api-python-client**（8,871 stars）—— Gmail 官方 OAuth 2.0 客户端

**8 大邮箱覆盖**：网易 163/126/yeah + Gmail + QQ + Outlook + 飞书邮箱 + 企业邮箱 ⭐ 直接解决你的问题

**3 大新增能力**：
1. 网易授权码流程（5 步引导）+ Gmail OAuth 5 步流程
2. Panmira secrets 加密存储 + 自动刷新
3. IMAP IDLE 实时监听 + 飞书卡片配置向导