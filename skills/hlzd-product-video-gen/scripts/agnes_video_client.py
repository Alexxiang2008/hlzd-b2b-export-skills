#!/usr/bin/env python3
"""
HLZD-视频生成 - Agnes Video V2.0 API 客户端
支持 4 种生成模式:
  1. T2V (文生视频)
  2. I2V (图生视频·单图)
  3. 多图I2V (extra_body.image 数组)
  4. Keyframes (extra_body.mode = keyframes)

用法:
  py scripts/agnes_video_client.py --prompt "..." --image "https://..." --duration 10
  py scripts/agnes_video_client.py --prompt "..." --keyframes "url1,url2" --mode keyframes
  py scripts/agnes_video_client.py --poll --video-id video_xxx
依赖: pip install requests python-dotenv
"""

import argparse
import json
import os
import sys
import time
import warnings

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）


# ============ 配置 ============
DEFAULT_CREATE_ENDPOINT = 'https://apihub.agnes-ai.com/v1/videos'
DEFAULT_RESULT_ENDPOINT = 'https://apihub.agnes-ai.com/agnesapi'
DEFAULT_MODEL = 'agnes-video-v2.0'

# Agnes 标准宽高比 → 推荐分辨率（横版16:9）
ASPECT_RATIO_PRESETS = {
    '16:9': {'width': 1280, 'height': 720},
    '9:16': {'width': 720, 'height': 1280},
    '1:1':  {'width': 768, 'height': 768},
    '4:3':  {'width': 1024, 'height': 768},
    '3:4':  {'width': 768, 'height': 1024},
}

# 分辨率档位（480p / 720p / 1080p）
RESOLUTION_SCALE = {
    '480p': 0.5,
    '720p': 1.0,
    '1080p': 1.5,
}

# 时长 → num_frames (8n+1 规则，24fps)
DURATION_TO_FRAMES = {
    3: 81,    # 3 秒
    5: 121,   # 5 秒
    8: 201,   # 8 秒
    10: 241,  # 10 秒
    15: 361,  # 15 秒
    18: 441,  # 18 秒（Agnes 硬上限）
}

MAX_FRAMES = 441
DEFAULT_FRAME_RATE = 24
MAX_RETRIES = 2
POLL_INTERVAL = 10   # 轮询间隔（秒）
POLL_TIMEOUT = 300   # 单段最大轮询时长（秒）


# ============ 配置加载 ============
def get_api_config():
    """
    从环境变量或 .env 文件读取 Agnes 视频配置
    Returns: (api_key, create_endpoint, result_endpoint, model)
    """
    api_key = os.environ.get('AGNES_API_KEY')
    create_endpoint = os.environ.get('AGNES_VIDEO_ENDPOINT', DEFAULT_CREATE_ENDPOINT)
    result_endpoint = os.environ.get('AGNES_VIDEO_RESULT_ENDPOINT', DEFAULT_RESULT_ENDPOINT)
    model = os.environ.get('AGNES_VIDEO_MODEL', DEFAULT_MODEL)

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
                        if k == 'AGNES_API_KEY':
                            api_key = v
                        elif k == 'AGNES_VIDEO_ENDPOINT':
                            create_endpoint = v
                        elif k == 'AGNES_VIDEO_RESULT_ENDPOINT':
                            result_endpoint = v
                        elif k == 'AGNES_VIDEO_MODEL':
                            model = v

    if not api_key or api_key == 'your_agnes_api_key_here':
        print("[错误] 未找到 AGNES_API_KEY，请在 .env 中设置", file=sys.stderr)
        sys.exit(1)

    return api_key, create_endpoint, result_endpoint, model


# ============ HTTP 工具 ============
def call_with_retry(method, url, api_key, max_retries=MAX_RETRIES, timeout=60, **kwargs):
    """
    通用 HTTP 调用，支持指数退避重试
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
            print(f"[Agnes] {method} {url} (第 {retry + 1} 次)", file=sys.stderr)
            if method == 'POST':
                resp = requests.post(url, headers=headers, timeout=timeout, **kwargs)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout, **kwargs)

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                print("[错误] 401 未授权，请检查 AGNES_API_KEY", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code == 400:
                print(f"[错误] 400 参数错误: {resp.text[:300]}", file=sys.stderr)
                sys.exit(1)
            elif resp.status_code in (429, 503):
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if retry < max_retries:
                    wait = 2 ** retry
                    print(f"[警告] {resp.status_code} 限流/繁忙，{wait}s 后重试", file=sys.stderr)
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
            last_error = f"请求超时 ({timeout}s)"
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


# ============ 参数解析与标准化 ============
def resolve_frames(duration_sec):
    """
    根据目标时长解析 num_frames
    遵循 8n+1 规则 + ≤441 限制
    """
    if duration_sec > 18:
        duration_sec = 18  # 硬上限
        print(f"[警告] 时长截断到 18 秒（Agnes 单段上限）", file=sys.stderr)

    # 选最接近的预定义档位
    best = min(DURATION_TO_FRAMES.keys(), key=lambda k: abs(k - duration_sec))
    frames = DURATION_TO_FRAMES[best]

    # 二次校验：必须是 8n+1 且 ≤ 441
    if frames > MAX_FRAMES:
        frames = MAX_FRAMES

    return frames


def resolve_size(aspect_ratio, resolution):
    """
    根据宽高比 + 分辨率档位解析 width/height
    """
    if aspect_ratio not in ASPECT_RATIO_PRESETS:
        print(f"[警告] aspect_ratio {aspect_ratio} 不在支持列表，使用 16:9", file=sys.stderr)
        aspect_ratio = '16:9'

    base = ASPECT_RATIO_PRESETS[aspect_ratio]
    scale = RESOLUTION_SCALE.get(resolution, 1.0)

    width = int(base['width'] * scale)
    height = int(base['height'] * scale)

    # Agnes 标准化映射后的常见输出（不强制相等，让 API 自行 normalize）
    return width, height


# ============ 4 种创建模式 ============
def create_t2v(prompt, duration=10, aspect_ratio='16:9', resolution='720p',
               seed=None, negative_prompt=None):
    """
    T2V 文生视频
    Returns: task dict（含 video_id）
    """
    api_key, create_endpoint, _, model = get_api_config()
    width, height = resolve_size(aspect_ratio, resolution)
    num_frames = resolve_frames(duration)

    payload = {
        'model': model,
        'prompt': prompt,
        'width': width,
        'height': height,
        'num_frames': num_frames,
        'frame_rate': DEFAULT_FRAME_RATE,
    }
    if seed is not None:
        payload['seed'] = seed
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt

    return call_with_retry('POST', create_endpoint, api_key, json=payload)


def create_i2v(prompt, image_url, duration=10, aspect_ratio='16:9', resolution='720p',
               seed=None, negative_prompt=None):
    """
    I2V 图生视频（单图）
    image_url: 公网 URL 或 base64 data URI
    Returns: task dict
    """
    api_key, create_endpoint, _, model = get_api_config()
    width, height = resolve_size(aspect_ratio, resolution)
    num_frames = resolve_frames(duration)

    payload = {
        'model': model,
        'prompt': prompt,
        'image': image_url,
        'width': width,
        'height': height,
        'num_frames': num_frames,
        'frame_rate': DEFAULT_FRAME_RATE,
    }
    if seed is not None:
        payload['seed'] = seed
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt

    return call_with_retry('POST', create_endpoint, api_key, json=payload)


def create_multi_image(prompt, image_urls, duration=10, aspect_ratio='16:9', resolution='720p',
                       seed=None, negative_prompt=None):
    """
    多图I2V：extra_body.image = [URL1, URL2, ...]
    image_urls: list of URL
    Returns: task dict
    """
    if not isinstance(image_urls, list) or len(image_urls) < 2:
        print(f"[错误] 多图模式需要至少 2 张图片，传入 {len(image_urls) if isinstance(image_urls, list) else 0}", file=sys.stderr)
        sys.exit(1)

    api_key, create_endpoint, _, model = get_api_config()
    width, height = resolve_size(aspect_ratio, resolution)
    num_frames = resolve_frames(duration)

    payload = {
        'model': model,
        'prompt': prompt,
        'extra_body': {'image': image_urls},
        'width': width,
        'height': height,
        'num_frames': num_frames,
        'frame_rate': DEFAULT_FRAME_RATE,
    }
    if seed is not None:
        payload['seed'] = seed
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt

    return call_with_retry('POST', create_endpoint, api_key, json=payload)


def create_keyframes(prompt, image_urls, duration=10, aspect_ratio='16:9', resolution='720p',
                     seed=None, negative_prompt=None):
    """
    关键帧动画：extra_body.image + extra_body.mode = keyframes
    image_urls: list of URL（推荐 2-4 张关键帧）
    Returns: task dict
    """
    if not isinstance(image_urls, list) or len(image_urls) < 2:
        print(f"[错误] 关键帧模式需要至少 2 张图片", file=sys.stderr)
        sys.exit(1)

    api_key, create_endpoint, _, model = get_api_config()
    width, height = resolve_size(aspect_ratio, resolution)
    num_frames = resolve_frames(duration)

    payload = {
        'model': model,
        'prompt': prompt,
        'extra_body': {
            'image': image_urls,
            'mode': 'keyframes'
        },
        'width': width,
        'height': height,
        'num_frames': num_frames,
        'frame_rate': DEFAULT_FRAME_RATE,
    }
    if seed is not None:
        payload['seed'] = seed
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt

    return call_with_retry('POST', create_endpoint, api_key, json=payload)


# ============ 结果轮询 ============
def poll_video_result(video_id, poll_interval=POLL_INTERVAL, poll_timeout=POLL_TIMEOUT):
    """
    轮询直到视频生成完成或失败
    Returns: 最终响应 dict（含 status / progress / remixed_from_video_id）
    """
    api_key, _, result_endpoint, _ = get_api_config()

    url = f"{result_endpoint}?video_id={video_id}"
    start_time = time.time()
    last_progress = -1

    while True:
        elapsed = time.time() - start_time
        if elapsed > poll_timeout:
            print(f"[错误] 轮询超时 ({poll_timeout}s)，任务仍未完成", file=sys.stderr)
            sys.exit(1)

        resp = call_with_retry('GET', url, api_key, max_retries=1, timeout=30)
        status = resp.get('status', 'unknown')
        progress = resp.get('progress', 0)

        if progress != last_progress:
            print(f"[轮询] status={status}, progress={progress}%, elapsed={elapsed:.0f}s", file=sys.stderr)
            last_progress = progress

        if status == 'completed':
            return resp
        elif status == 'failed':
            error = resp.get('error') or {}
            print(f"[错误] 视频生成失败: {error}", file=sys.stderr)
            sys.exit(1)
        elif status in ('queued', 'in_progress'):
            time.sleep(poll_interval)
            continue
        else:
            print(f"[警告] 未知状态: {status}，继续轮询", file=sys.stderr)
            time.sleep(poll_interval)


# ============ 视频下载 ============
def download_video(url, save_path):
    """
    从 URL 下载视频到本地
    """
    try:
        import requests
    except ImportError:
        print("[错误] requests 未安装", file=sys.stderr)
        sys.exit(1)

    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    total = 0
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192 * 16):
            if chunk:
                f.write(chunk)
                total += len(chunk)

    print(f"[下载] 已保存: {save_path} ({total / 1024:.1f} KB)", file=sys.stderr)
    return save_path


# ============ 一键式（创建 + 轮询 + 下载） ============
def generate_and_download(capability, prompt, **kwargs):
    """
    完整流程：创建任务 → 轮询 → 下载
    capability: 't2v' | 'i2v' | 'multi_i2v' | 'keyframes'
    其他 kwargs: duration, aspect_ratio, resolution, image_urls, seed, output_path

    Returns: dict {video_id, video_url, local_path, seconds, size}
    """
    output_path = kwargs.pop('output_path', None)
    duration = kwargs.pop('duration', 10)
    aspect_ratio = kwargs.pop('aspect_ratio', '16:9')
    resolution = kwargs.pop('resolution', '720p')
    seed = kwargs.pop('seed', None)
    negative_prompt = kwargs.pop('negative_prompt', None)

    # 1. 创建任务
    if capability == 't2v':
        task = create_t2v(prompt, duration, aspect_ratio, resolution, seed, negative_prompt)
    elif capability == 'i2v':
        image_url = kwargs.pop('image_url', None)
        if not image_url:
            print("[错误] I2V 需要 image_url", file=sys.stderr)
            sys.exit(1)
        task = create_i2v(prompt, image_url, duration, aspect_ratio, resolution, seed, negative_prompt)
    elif capability == 'multi_i2v':
        image_urls = kwargs.pop('image_urls', [])
        task = create_multi_image(prompt, image_urls, duration, aspect_ratio, resolution, seed, negative_prompt)
    elif capability == 'keyframes':
        image_urls = kwargs.pop('image_urls', [])
        task = create_keyframes(prompt, image_urls, duration, aspect_ratio, resolution, seed, negative_prompt)
    else:
        print(f"[错误] capability 必须是 t2v/i2v/multi_i2v/keyframes，当前: {capability}", file=sys.stderr)
        sys.exit(1)

    video_id = task.get('video_id') or task.get('task_id')
    if not video_id:
        print(f"[错误] 响应中无 video_id: {task}", file=sys.stderr)
        sys.exit(1)

    print(f"[创建] video_id={video_id}, seconds={task.get('seconds')}, size={task.get('size')}", file=sys.stderr)

    # 2. 轮询
    result = poll_video_result(video_id)
    # Agnes API 字段兼容：新版本用 'url'，旧版本用 'remixed_from_video_id'
    video_url = result.get('url') or result.get('remixed_from_video_id')
    if not video_url:
        print(f"[错误] 响应中无视频URL（url/remixed_from_video_id 都不存在）: {result}", file=sys.stderr)
        sys.exit(1)

    # 3. 下载
    if output_path:
        download_video(video_url, output_path)
    else:
        output_path = None

    return {
        'video_id': video_id,
        'video_url': video_url,
        'local_path': output_path,
        'seconds': result.get('seconds'),
        'size': result.get('size'),
        'capability': capability,
        'prompt': prompt,
        'duration': duration,
        'aspect_ratio': aspect_ratio,
        'resolution': resolution,
    }


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='Agnes Video V2.0 客户端')
    parser.add_argument('--capability', choices=['t2v', 'i2v', 'multi_i2v', 'keyframes', 'poll'],
                        default='i2v', help='生成模式')
    parser.add_argument('--prompt', help='视频描述 prompt')
    parser.add_argument('--image', help='I2V 单图 URL')
    parser.add_argument('--images', help='多图 URL，逗号分隔')
    parser.add_argument('--keyframes', help='关键帧 URL，逗号分隔')
    parser.add_argument('--duration', type=int, default=10, help='目标时长（秒），≤18')
    parser.add_argument('--aspect-ratio', default='16:9', choices=list(ASPECT_RATIO_PRESETS.keys()))
    parser.add_argument('--resolution', default='720p', choices=list(RESOLUTION_SCALE.keys()))
    parser.add_argument('--seed', type=int, help='随机种子')
    parser.add_argument('--negative-prompt', help='反向提示词')
    parser.add_argument('--video-id', help='轮询已有任务时使用')
    parser.add_argument('--output', help='视频保存路径')
    parser.add_argument('--out-json', help='保存完整结果到 JSON')

    args = parser.parse_args()

    # 模式分支
    if args.capability == 'poll':
        if not args.video_id:
            print("[错误] --capability poll 需要 --video-id", file=sys.stderr)
            sys.exit(1)
        result = poll_video_result(args.video_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.prompt:
        print("[错误] 需要 --prompt", file=sys.stderr)
        sys.exit(1)

    capability = args.capability
    kwargs = {
        'duration': args.duration,
        'aspect_ratio': args.aspect_ratio,
        'resolution': args.resolution,
        'seed': args.seed,
        'negative_prompt': args.negative_prompt,
        'output_path': args.output,
    }

    if capability == 't2v':
        pass
    elif capability == 'i2v':
        if not args.image:
            print("[错误] I2V 需要 --image", file=sys.stderr)
            sys.exit(1)
        kwargs['image_url'] = args.image
    elif capability in ('multi_i2v', 'keyframes'):
        urls_str = args.images if capability == 'multi_i2v' else args.keyframes
        if not urls_str:
            print(f"[错误] {capability} 需要 --images 或 --keyframes（逗号分隔URL）", file=sys.stderr)
            sys.exit(1)
        kwargs['image_urls'] = [u.strip() for u in urls_str.split(',') if u.strip()]
        if capability == 'keyframes':
            capability = 'keyframes'  # 保持 capability 名

    result = generate_and_download(capability, args.prompt, **kwargs)

    if args.out_json:
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[保存] {args.out_json}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()