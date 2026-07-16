#!/usr/bin/env python3
"""
HLZD-图片生成 - Agnes Image 2.1 Flash API 客户端
用法:
  py scripts/agnes_client.py --prompt "OCTG oil casing, white background" --size 1024x1024
  py scripts/agnes_client.py --prompt "..." --image-input "https://..." --size 1024x1024
依赖: pip install requests python-dotenv
"""

import argparse
import json
import os
import sys
import io
import time
import warnings

warnings.filterwarnings('ignore')


def _ensure_utf8_stdio():
    """幂等地包装 stdout/stderr 为 UTF-8（避免 orchestrator 等场景下重复包装导致状态损坏）"""
    if sys.platform != 'win32':
        return
    for _name in ('stdout', 'stderr'):
        _stream = getattr(sys, _name, None)
        if _stream is None or not hasattr(_stream, 'buffer'):
            continue
        _encoding = getattr(_stream, 'encoding', None) or ''
        if 'utf-8' in _encoding.lower():
            continue
        _wrapper = io.TextIOWrapper(_stream.buffer, encoding='utf-8', errors='replace')
        setattr(sys, _name, _wrapper)


_ensure_utf8_stdio()


# ============ 配置 ============
DEFAULT_ENDPOINT = 'https://apihub.agnes-ai.com/v1/images/generations'
DEFAULT_MODEL = 'agnes-image-2.1-flash'
DEFAULT_SIZE = '1024x1024'
VALID_SIZES = ['1024x1024', '1024x768', '768x1024']
MAX_RETRIES = 2
TIMEOUT = 300


def get_api_config():
    """
    从环境变量或 .env 文件读取 Agnes 配置
    Returns: (api_key, endpoint, model)
    """
    api_key = os.environ.get('AGNES_API_KEY')
    endpoint = os.environ.get('AGNES_ENDPOINT', DEFAULT_ENDPOINT)
    model = os.environ.get('AGNES_MODEL', DEFAULT_MODEL)

    # 尝试从 CWD/.env 读取（兼容）
    if not api_key:
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip()
                        if k == 'AGNES_API_KEY':
                            api_key = v
                        elif k == 'AGNES_ENDPOINT':
                            endpoint = v
                        elif k == 'AGNES_MODEL':
                            model = v

    if not api_key or api_key == 'your_agnes_api_key_here':
        print("[错误] 未找到 AGNES_API_KEY，请在 .env 中设置", file=sys.stderr)
        sys.exit(1)

    return api_key, endpoint, model


def call_agnes(payload, api_key, endpoint, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    """
    调用 Agnes API，支持指数退避重试
    Returns: dict 响应体
    """
    try:
        import requests
    except ImportError:
        print("[错误] requests 未安装，运行: pip install requests", file=sys.stderr)
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    last_error = None
    for retry in range(max_retries + 1):
        try:
            print(f"[Agnes] 调用 (第 {retry + 1} 次)", file=sys.stderr)
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                print(f"[错误] 401 未授权，请检查 AGNES_API_KEY 是否正确", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 400:
                print(f"[错误] 400 参数错误: {resp.text[:200]}", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 429:
                last_error = f"HTTP 429: {resp.text[:200]}"
                if retry < max_retries:
                    wait = 2 ** retry
                    print(f"[警告] 429 限流，{wait}s 后重试", file=sys.stderr)
                    time.sleep(wait)
                    continue
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if retry < max_retries:
                    wait = 2 ** retry
                    print(f"[警告] {last_error[:100]}，{wait}s 后重试", file=sys.stderr)
                    time.sleep(wait)
                    continue

        except requests.exceptions.Timeout:
            last_error = f"请求超时（{timeout}s）"
            if retry < max_retries:
                wait = 2 ** retry
                print(f"[警告] 超时，{wait}s 后重试", file=sys.stderr)
                time.sleep(wait)
                continue
        except requests.exceptions.RequestException as e:
            last_error = f"网络错误: {e}"
            if retry < max_retries:
                wait = 2 ** retry
                print(f"[警告] 网络错误，{wait}s 后重试", file=sys.stderr)
                time.sleep(wait)
                continue

    print(f"[错误] 所有重试失败: {last_error}", file=sys.stderr)
    sys.exit(1)


def generate_t2i(prompt, size=DEFAULT_SIZE, return_url=True):
    """
    T2I 文生图
    Returns: 图片 URL 字符串
    """
    api_key, endpoint, model = get_api_config()

    if size not in VALID_SIZES:
        print(f"[警告] size {size} 不在支持列表 {VALID_SIZES}，使用默认 {DEFAULT_SIZE}", file=sys.stderr)
        size = DEFAULT_SIZE

    payload = {
        'model': model,
        'prompt': prompt,
        'size': size,
        'extra_body': {'response_format': 'url' if return_url else 'b64_json'}
    }

    resp = call_agnes(payload, api_key, endpoint)
    data = resp.get('data', [])
    if not data:
        print(f"[错误] 响应中无 data: {resp}", file=sys.stderr)
        sys.exit(1)

    item = data[0]
    return item.get('url') or item.get('b64_json')


def generate_i2i(prompt, image_url, size=DEFAULT_SIZE, return_url=True):
    """
    I2I 图生图
    image_url: 公网 URL 或 base64 data URI
    Returns: 图片 URL 字符串
    """
    api_key, endpoint, model = get_api_config()

    if size not in VALID_SIZES:
        print(f"[警告] size {size} 不在支持列表 {VALID_SIZES}，使用默认 {DEFAULT_SIZE}", file=sys.stderr)
        size = DEFAULT_SIZE

    payload = {
        'model': model,
        'prompt': prompt,
        'size': size,
        'image': [image_url],
        'extra_body': {'response_format': 'url' if return_url else 'b64_json'}
    }

    resp = call_agnes(payload, api_key, endpoint)
    data = resp.get('data', [])
    if not data:
        print(f"[错误] 响应中无 data: {resp}", file=sys.stderr)
        sys.exit(1)

    item = data[0]
    return item.get('url') or item.get('b64_json')


def download_image(url, save_path):
    """从 URL 下载图片到本地"""
    try:
        import requests
    except ImportError:
        print("[错误] requests 未安装", file=sys.stderr)
        sys.exit(1)

    if url.startswith('data:image'):
        # base64 data URI
        import base64
        header, b64_data = url.split(',', 1)
        img_data = base64.b64decode(b64_data)
    else:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        img_data = resp.content

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        f.write(img_data)
    print(f"[下载] 已保存: {save_path} ({len(img_data)} bytes)", file=sys.stderr)
    return save_path


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='Agnes Image 2.1 Flash 客户端')
    parser.add_argument('--prompt', required=True, help='图像生成/编辑的文本指令')
    parser.add_argument('--image-input', help='I2I 输入图 URL 或 base64 data URI')
    parser.add_argument('--size', default=DEFAULT_SIZE, choices=VALID_SIZES, help='输出尺寸')
    parser.add_argument('--output', help='图片保存路径（默认返回 URL）')
    parser.add_argument('--out-json', help='保存完整响应到 JSON')
    args = parser.parse_args()

    if args.image_input:
        # I2I
        result = generate_i2i(args.prompt, args.image_input, args.size, return_url=bool(args.output or args.out_json))
    else:
        # T2I
        result = generate_t2i(args.prompt, args.size, return_url=bool(args.output or args.out_json))

    if args.output:
        download_image(result, args.output)
    elif args.out_json:
        result_data = {
            'image': result,
            'capability': 'i2i' if args.image_input else 't2i',
            'prompt': args.prompt,
            'size': args.size,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        }
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"[保存] {args.out_json}")
    else:
        print(result)


if __name__ == '__main__':
    main()