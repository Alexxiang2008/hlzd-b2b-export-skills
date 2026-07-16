#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hlzd-rfp-response — 8 大邮箱配置矩阵 + 凭证字段校验。

v0.1.0 仅交付配置矩阵 schema + 字段校验；v0.2 接入 IMAP/OAuth 真连接。
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass(frozen=True)
class EmailProvider:
    code: str
    name: str
    protocol: str          # imap / imaps / exchange / pop3 / api
    host: str
    port: int
    auth_method: str       # oauth / password / app_password
    required_fields: tuple
    notes: str


PROVIDERS: Dict[str, EmailProvider] = {
    "gmail": EmailProvider("gmail", "Gmail", "imaps", "imap.gmail.com", 993,
                           "oauth", ("client_id", "client_secret", "refresh_token"),
                           "需在 Google Cloud Console 启用 Gmail API"),
    "netease_163": EmailProvider("netease_163", "网易 163", "imaps", "imap.163.com", 993,
                                  "app_password", ("email", "app_password"),
                                  "授权码 ≠ 登录密码；需在网页端申请"),
    "qq": EmailProvider("qq", "QQ 邮箱", "imaps", "imap.qq.com", 993,
                        "app_password", ("email", "app_password"),
                        "需开启 IMAP/SMTP 服务并生成授权码"),
    "outlook": EmailProvider("outlook", "Outlook 365", "imaps", "outlook.office365.com", 993,
                             "oauth", ("tenant_id", "client_id", "client_secret"),
                             "Azure AD App Registration"),
    "feishu": EmailProvider("feishu", "飞书邮箱", "api", "open.feishu.cn", 0,
                            "app", ("app_id", "app_secret"),
                            "通过 open API 而非 IMAP"),
    "wework": EmailProvider("wework", "企业微信邮箱", "exchangelib", "exmail.qq.com", 993,
                            "oauth", ("corpid", "corp_secret"),
                            "走 Exchange 协议"),
    "aliyun": EmailProvider("aliyun", "阿里云邮", "imaps", "imap.aliyun.com", 993,
                            "password", ("email", "password"),
                            "企业版支持 IMAP"),
    "self_hosted": EmailProvider("self_hosted", "自建邮局", "imaps", "", 993,
                                 "password", ("host", "port", "email", "password"),
                                 "需用户自定义 host + port"),
}


def list_providers() -> List[Dict]:
    return [asdict(p) for p in PROVIDERS.values()]


def validate_credentials(provider_code: str, creds: Dict) -> List[str]:
    """校验凭证是否覆盖 provider 必需字段。返回缺失字段列表。"""
    p = PROVIDERS.get(provider_code)
    if not p:
        return [f"unknown_provider:{provider_code}"]
    return [f for f in p.required_fields if not creds.get(f)]


def recommend_provider(domain: str) -> Optional[str]:
    """根据邮箱域名推荐 provider code。"""
    d = domain.lower().strip()
    if d.endswith(("@gmail.com", "googlemail.com")):
        return "gmail"
    if d.endswith(("@163.com", "@126.com", "@yeah.net")):
        return "netease_163"
    if d.endswith("@qq.com"):
        return "qq"
    if d.endswith(("@outlook.com", "@hotmail.com", "@live.com", "@office365.com")):
        return "outlook"
    if d.endswith("@feishu.cn") or d.endswith("@larksuite.com"):
        return "feishu"
    if d.endswith("@qq.com") or "exmail" in d:
        return "wework"
    if d.endswith(("@aliyun.com", "@alibaba-inc.com")):
        return "aliyun"
    return "self_hosted"
