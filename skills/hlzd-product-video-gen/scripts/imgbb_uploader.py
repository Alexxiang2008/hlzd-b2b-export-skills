#!/usr/bin/env python3
r"""
HLZD-视频生成 - imgbb 图床上传模块
封装 imgbb API（https://api.imgbb.com/1/upload），把本地图片转公网 URL，
供 Agnes Video V2.0 I2V 模式使用。

用法:
  py scripts/imgbb_uploader.py --input D:\path\to\image.png
  py scripts/imgbb_uploader.py --input image.png --out-json upload.json
依赖: pip install requests python-dotenv
"""

import argparse
import base64
import json
import os
import sys
import time
import warnings

warnings.filterwarnings('ignore')


# ============ 配置 ============
DEFAULT_ENDPOINT = 'https://api.imgbb.com/1/upload'
DEFAULT_EXPIRATION = 0  # 0 = 永不过期（imgbb 免费版支持）
MAX_RETRIES = 2


# ============ 配置加载 ============
def get_api_config():
    """
    从环境变量或 .env 文件读取 imgbb 配置
    Returns: (api_key, endpoint)
    """
    api_key = os.environ.get('IMGBB_API_KEY')
    endpoint = os.environ.get('IMGBB_ENDPOINT', DEFAULT_ENDPOINT)

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
                        v = v.strip().strip('"').strip("'")
                        if k == 'IMGBB_API_KEY':
                            api_key = v
                        elif k == 'IMGBB_ENDPOINT':
                            endpoint = v

    if not api_key or api_key == 'your_imgbb_api_key_here':
        print("[错误] 未找到 IMGBB_API_KEY，请在 .env 中设置", file=sys.stderr)
        sys.exit(1)

    return api_key, endpoint


# ============ 文件 → base64 ============
def file_to_base64(file_path):
    """读取本地图片文件，转 base64 字符串（不含前缀）"""
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, 'rb') as f:
        img_bytes = f.read()

    # imgbb 限制 32MB
    size_mb = len(img_bytes) / 1024 / 1024
    if size_mb > 32:
        print(f"[警告] 文件 {size_mb:.1f}MB 超过 imgbb 32MB 限制", file=sys.stderr)

    return base64.b64encode(img_bytes).decode('utf-8')


# ============ 上传 ============
def upload_image(local_path, expiration=DEFAULT_EXPIRATION, max_retries=MAX_RETRIES):
    """
    上传本地图片到 imgbb，返回公网 URL
    local_path: 本地图片路径
    expiration: 过期时间（秒），0 = 永不过期
    Returns: dict {
        url: 公网 URL（https://i.ibb.co/xxx/xxx.png）,
        display_url: 同 url,
        delete_url: 删除 URL,
        filename: 原始文件名,
        size: 文件大小 bytes,
        width: 图片宽度,
        height: 图片高度,
    }
    """
    try:
        import requests
    except ImportError:
        print("[错误] requests 未安装，运行: pip install requests", file=sys.stderr)
        sys.exit(1)

    api_key, endpoint = get_api_config()
    img_b64 = file_to_base64(local_path)

    payload = {
        'key': api_key,
        'image': img_b64,
    }
    if expiration and expiration > 0:
        payload['expiration'] = str(expiration)

    last_error = None
    for retry in range(max_retries + 1):
        try:
            print(f"[imgbb] 上传 {os.path.basename(local_path)} (第 {retry + 1} 次)", file=sys.stderr)
            resp = requests.post(endpoint, data=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                if not data.get('success'):
                    last_error = f"imgbb 返回 success=false: {data}"
                    if retry < max_retries:
                        time.sleep(2 ** retry)
                        continue
                    print(f"[错误] {last_error}", file=sys.stderr)
                    sys.exit(1)

                img_data = data['data']
                return {
                    'url': img_data['url'],
                    'display_url': img_data.get('display_url', img_data['url']),
                    'delete_url': img_data.get('delete_url'),
                    'filename': img_data.get('title', os.path.basename(local_path)),
                    'size': img_data.get('size'),
                    'width': img_data.get('width'),
                    'height': img_data.get('height'),
                    'local_path': local_path,
                }
            elif resp.status_code == 400:
                print(f"[错误] 400 参数错误: {resp.text[:300]}", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 401:
                print("[错误] 401 未授权，请检查 IMGBB_API_KEY", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 429:
                last_error = f"429 限流: {resp.text[:200]}"
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
            last_error = "请求超时"
            if retry < max_retries:
                time.sleep(2 ** retry)
                continue
        except requests.exceptions.RequestException as e:
            last_error = f"网络错误: {e}"
            if retry < max_retries:
                time.sleep(2 ** retry)
                continue

    print(f"[错误] 上传失败: {last_error}", file=sys.stderr)
    sys.exit(1)


# ============ 批量上传 ============
def upload_images(local_paths):
    """
    批量上传图片
    Returns: list of upload results（按输入顺序）
    """
    results = []
    for i, path in enumerate(local_paths):
        print(f"[imgbb 批量] {i+1}/{len(local_paths)}: {os.path.basename(path)}", file=sys.stderr)
        result = upload_image(path)
        results.append(result)
        # 避免触发限流，每张间隔 1 秒
        if i < len(local_paths) - 1:
            time.sleep(1)
    return results


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='imgbb 图床上传')
    parser.add_argument('--input', required=True, help='本地图片路径')
    parser.add_argument('--inputs', help='批量上传，多个路径用逗号分隔')
    parser.add_argument('--expiration', type=int, default=0, help='过期时间（秒），0=永久')
    parser.add_argument('--out-json', help='保存上传结果到 JSON')
    args = parser.parse_args()

    if args.inputs:
        paths = [p.strip() for p in args.inputs.split(',') if p.strip()]
        results = upload_images(paths)
        output = {'count': len(results), 'images': results}
    else:
        result = upload_image(args.input, expiration=args.expiration)
        output = result

    if args.out_json:
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"[保存] {args.out_json}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()