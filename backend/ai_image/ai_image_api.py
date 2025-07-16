from flask import Flask, request, jsonify
import urllib.parse
import logging
import requests
import os
import time
import hashlib
import re
try:
    from PIL import Image
except ImportError:
    Image = None

app = Flask(__name__)

def generate_safe_filename(prompt, max_length=100):
    """
    根据提示词生成安全的文件名

    Args:
        prompt: 原始提示词
        max_length: 文件名最大长度（不包括扩展名）

    Returns:
        安全的文件名（不包括扩展名）
    """
    # 移除或替换不安全的字符
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', prompt)
    safe_chars = re.sub(r'[,.]', '_', safe_chars)
    safe_chars = re.sub(r'\s+', '_', safe_chars)  # 多个空格替换为单个下划线
    safe_chars = re.sub(r'_+', '_', safe_chars)   # 多个下划线替换为单个下划线
    safe_chars = safe_chars.strip('_')            # 移除首尾下划线

    # 如果文件名太长，截取前部分并添加哈希值
    if len(safe_chars) > max_length:
        # 生成提示词的哈希值作为唯一标识
        hash_value = hashlib.md5(prompt.encode('utf-8')).hexdigest()[:8]
        # 截取前部分，留出空间给哈希值
        truncated = safe_chars[:max_length-9]  # 9 = 1个下划线 + 8位哈希
        safe_filename = f"{truncated}_{hash_value}"
    else:
        safe_filename = safe_chars

    # 确保文件名不为空
    if not safe_filename:
        hash_value = hashlib.md5(prompt.encode('utf-8')).hexdigest()[:12]
        safe_filename = f"wallpaper_{hash_value}"

    return safe_filename

def validate_image_file(file_path):
    """验证图片文件的完整性"""
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size < 1024:  # 小于1KB认为无效
            return False

        # 如果PIL可用，尝试打开图片验证格式
        if Image:
            try:
                with Image.open(file_path) as img:
                    # 验证图片格式
                    img.verify()
                    return True
            except Exception as e:
                logging.warning(f"validate_image_file [PIL验证失败] {file_path}: {e}")
                return False
        else:
            # 如果PIL不可用，进行基本的文件头验证
            with open(file_path, 'rb') as f:
                header = f.read(16)
                # 检查常见图片格式的文件头
                if header.startswith(b'\xff\xd8\xff'):  # JPEG
                    return True
                elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                    return True
                elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
                    return True
                elif header.startswith(b'RIFF') and b'WEBP' in header:  # WebP
                    return True
                else:
                    logging.warning(f"validate_image_file [未知格式] {file_path}")
                    return False
    except Exception as e:
        logging.error(f"validate_image_file [验证异常] {file_path}: {e}")
        return False

def download_wallpaper(prompt, local_path, max_retries=3, width=1920, height=1080, model="flux", seed=2, Enhance=False, nologo=True):
    '''
    按1920*1080请求实际得到的宽高最大到1704*960
    model: flux, kontext, turbo, gptimage
    Enhance: 启用/禁用 Pollinations AI 提示增强器，它能通过优化你的文本提示，帮助你创造更出色的图像。
    '''
    encoded_prompt = urllib.parse.quote(prompt)
    #  example: https://image.pollinations.ai/prompt/cyberpunk%20city%20at%20night?width=1920&height=1080&model=flux&seed=42&nologo=True&Enhance=True
    image_url = f'https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&seed={seed}&nologo={nologo}&Enhance={Enhance}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            resp = requests.get(image_url, headers=headers, timeout=20)
            if resp.status_code == 200:
                # 检查响应内容是否为空
                if not resp.content or len(resp.content) == 0:
                    logging.warning(f"download_wallpaper [警告] 响应内容为空, 尝试 {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue

                # 检查内容长度是否合理（至少1KB）
                if len(resp.content) < 1024:
                    logging.warning(f"download_wallpaper [警告] 文件过小 ({len(resp.content)} bytes), 可能不是有效图片, 尝试 {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue

                # 写入文件
                with open(local_path, 'wb') as f:
                    f.write(resp.content)

                # 验证文件完整性
                if not validate_image_file(local_path):
                    logging.warning(f"download_wallpaper [警告] 文件验证失败, 尝试 {attempt + 1}/{max_retries}")
                    # 删除无效文件
                    try:
                        os.remove(local_path)
                    except:
                        pass
                    time.sleep(2)
                    continue

                logging.info(f"download_wallpaper [成功] 壁纸下载到: {local_path}, 大小: {len(resp.content)} bytes")
                return True
            else:
                logging.error(f"download_wallpaper [失败] 状态码 {resp.status_code}, 尝试 {attempt + 1}/{max_retries}")
                time.sleep(5)  # 等待后重试
        except Exception as e:
            logging.error(f"download_wallpaper [错误] 请求异常: {e}, 尝试 {attempt + 1}/{max_retries}")
            time.sleep(2)

    logging.error(f"download_wallpaper [终止] 多次尝试后仍失败, image_url: {image_url}")
    return False

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # 对prompt进行URL编码
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f'https://image.pollinations.ai/prompt/{encoded_prompt}'
    return jsonify({'image_url': image_url})

if __name__ == '__main__':
    app.run(debug=True)