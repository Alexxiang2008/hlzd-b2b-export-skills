#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hlzd-rfp-response lib 测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import (  # noqa: E402
    PROVIDERS, list_providers, validate_credentials, recommend_provider,
)


def test_8_providers_present():
    codes = {p["code"] for p in list_providers()}
    expected = {"gmail", "netease_163", "qq", "outlook", "feishu",
                "wework", "aliyun", "self_hosted"}
    assert codes == expected, f"missing: {expected - codes}"


def test_gmail_requires_oauth_fields():
    missing = validate_credentials("gmail", {})
    assert set(missing) == {"client_id", "client_secret", "refresh_token"}


def test_163_requires_app_password():
    missing = validate_credentials("netease_163", {"email": "x@163.com"})
    assert missing == ["app_password"]


def test_unknown_provider():
    errs = validate_credentials("nope", {})
    assert any("unknown_provider" in e for e in errs)


def test_recommend_gmail():
    assert recommend_provider("buyer@gmail.com") == "gmail"
    assert recommend_provider("Buyer@GoogleMail.COM") == "gmail"


def test_recommend_163_and_qq():
    assert recommend_provider("buyer@163.com") == "netease_163"
    assert recommend_provider("buyer@qq.com") == "qq"


def test_recommend_outlook_variants():
    assert recommend_provider("a@outlook.com") == "outlook"
    assert recommend_provider("a@HOTMAIL.com") == "outlook"


def test_recommend_unknown_falls_to_self_hosted():
    assert recommend_provider("a@unknown-corp.cn") == "self_hosted"
