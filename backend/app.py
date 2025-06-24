from flask import Flask, jsonify, request, send_from_directory
from weather.weather_qq_api import get_qq_weather
from weather.get_location import get_location_by_ip
from ai_image.ai_image_api import generate_image
import urllib.parse
import requests
import os
import sys
from flask_socketio import SocketIO, emit, disconnect
import threading
import time
import io
import logging
from ai_image.make_prompt import make_draw_prompt, get_time_mood, get_weather_key
# import gevent
# print("gevent version:", gevent.__version__)

__version__ = "0.1.3"

# 设置标准输出和错误输出的编码为UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

# 兼容源码和PyInstaller打包后的路径
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_WALLPAPER_DIR = os.path.join(BASE_DIR, 'static', 'wallpapers')
os.makedirs(STATIC_WALLPAPER_DIR, exist_ok=True)

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')
app.config['WALLPAPER_DIR'] = STATIC_WALLPAPER_DIR

DEFAULT_WALLPAPER = "default.jpg"
DEFAULT_WALLPAPER_PATH = os.path.join(app.config['WALLPAPER_DIR'], DEFAULT_WALLPAPER)

# 程序启动时只获取一次位置
ret_location = get_location_by_ip()
if 'error' in ret_location:
    logging.error(f"[location] 获取位置失败: {ret_location['error']}")
else:
    logging.info(f"[location] 获取位置成功: {ret_location}")
LOCATION_CACHE = ret_location
first_run = True  # 用于标记是否首次运行

# 全局缓存
CACHE = {
    'weather_data': None,
    'weather_key': None,
    'time_mood': None,
    'prompt': None,
    'province': '',
    'city': '',
    'county': ''
}

# def get_wallpaper_filename(time_mood: str, weather_key: str) -> str:
#     return f"{time_mood}_{weather_key}.jpg"

def get_wallpaper_filename_by_prompts(prompt: str) -> str:
    prompt_filename = prompt.strip()
    return f"{prompt_filename}.jpg"

def get_wallpaper_path(filename) -> str:
    # filename = get_wallpaper_filename(time_mood, weather_key)
    # filename = get_wallpaper_filename_by_prompts(prompt)
    return os.path.join(app.config['WALLPAPER_DIR'], filename)

def download_wallpaper(prompt, local_path, max_retries=3):
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f'https://image.pollinations.ai/prompt/{encoded_prompt}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(image_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(resp.content)
                logging.info(f"download_wallpaper [成功] 壁纸下载到: {local_path}")
                return True
            else:
                logging.error(f"download_wallpaper [失败] 状态码 {resp.status_code}, 尝试 {attempt + 1}/{max_retries}")
                time.sleep(5)  # 等待后重试
        except Exception as e:
            logging.error(f"download_wallpaper [错误] 请求异常: {e} image_url: {image_url}")
    
    logging.error("download_wallpaper [终止] 多次尝试后仍失败, image_url: {image_url}")
    return False

@app.route('/api/version', methods=['GET'])
def version():
    return jsonify({"version": __version__})

@app.route('/api/weather', methods=['GET'])
def weather():
    global LOCATION_CACHE
    loc = LOCATION_CACHE
    province = loc.get('province', '')
    city = loc.get('city', '')
    county = loc.get('county', '')
    weather_data = get_qq_weather(province, city, county)
    # 返回风力、湿度、位置
    return jsonify({
        **weather_data,
        'province': province,
        'city': city,
        'county': county
    })

@app.route('/api/generate-image', methods=['POST'])
def generate_ai_image():
    image_data = generate_image()
    return jsonify(image_data)

@app.route('/api/auto-wallpaper', methods=['GET'])
def auto_wallpaper():
    # global CACHE
    # 直接读取缓存
    weather_data = CACHE['weather_data'] or {}
    if 'error' in weather_data:
        logging.error(f"[weather] API返回天气失败: {weather_data['error']}")
        weather_data = {'weather': '未知', 'temperature': '--', 'humidity': '--', 'wind_power': '--'}
    weather = weather_data.get('weather', '晴')
    temperature = weather_data.get('temperature', '25°C')
    humidity = weather_data.get('humidity', '--')
    wind_power = weather_data.get('wind_power', '--')
    province = CACHE['province']
    city = CACHE['city']
    county = CACHE['county']
    time_mood = CACHE['time_mood'] or get_time_mood()
    # weather_key = CACHE['weather_key'] or get_weather_key(weather)
    if CACHE['prompt'] is None:
        # 如果缓存中没有prompt，则生成一个新的
        logging.info("[auto_wallpaper] CACHE中没有prompt")
        prompt = "None"
    else:
        prompt = CACHE['prompt']
        logging.info(f"[auto_wallpaper] 使用缓存中的prompt: {prompt}")

    # 文件名
    filename = get_wallpaper_filename_by_prompts(prompt)
    local_path = get_wallpaper_path(filename)


    # 优先返回本地图片，否则返回默认图片
    if os.path.exists(local_path):
        local_url = f"/static/wallpapers/{filename}"
    elif os.path.exists(DEFAULT_WALLPAPER_PATH):
        logging.info(f"[auto_wallpaper] 使用默认壁纸: {DEFAULT_WALLPAPER}")
        local_url = f"/static/wallpapers/{DEFAULT_WALLPAPER}"
    else:
        local_url = ""  # 没有任何图片

    return jsonify({
        'prompt': prompt,
        'image_url': local_url,
        'weather': weather,
        'temperature': temperature,
        'humidity': humidity,
        'wind_power': wind_power,
        'province': province,
        'city': city,
        'county': county,
        'time_mood': time_mood
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)

# 记录上一次的时间段和天气
last_time_mood = None
last_weather = None


def update_cache():
    global LOCATION_CACHE
    global CACHE
    if 'error' in LOCATION_CACHE:
        logging.error(f"[location] 获取位置为空: {LOCATION_CACHE['error']}")
        LOCATION_CACHE = get_location_by_ip()
    loc = LOCATION_CACHE
    province = loc.get('province', '')
    city = loc.get('city', '')
    county = loc.get('county', '')
    weather_data = get_qq_weather(province, city, county)
    if 'error' in weather_data:
        logging.error(f"[weather] 获取天气失败: {weather_data['error']}")
        # 保持上一次的weather_data不变，或用默认值
        weather_data = CACHE['weather_data'] or {
            'weather': '未知', 'temperature': '--', 'humidity': '--', 'wind_power': '--'
        }
    # debug 当前时间超过17:55时，设置weather_data['weather']为雨
    # now = datetime.now()
    # if now.hour > 17 or (now.hour == 17 and now.minute >= 55):
    #     weather_data['weather'] = '雨'

    weather = weather_data.get('weather', '晴')
    time_mood = get_time_mood()
    weather_key = get_weather_key(weather)
    CACHE['weather_data'] = weather_data
    CACHE['weather_key'] = weather_key
    CACHE['time_mood'] = time_mood
    CACHE['province'] = province
    CACHE['city'] = city
    CACHE['county'] = county

update_cache()

# 改为记录连接的客户端数量
connected_clients = 0
enabled_push = threading.Event()

@socketio.on('ready_for_push')
def handle_ready_for_push():
    global connected_clients
    connected_clients += 1
    enabled_push.set()
    logging.info(f"[socketio] 前端客户端 已准备好接收推送 (当前客户端数: {connected_clients})")

@socketio.on('disconnect')
def handle_disconnect():
    global connected_clients
    connected_clients = max(0, connected_clients - 1)
    if connected_clients == 0:
        enabled_push.clear()
    logging.info(f"[socketio] 客户端断开 (剩余客户端数: {connected_clients})")

def wallpaper_monitor():
    import datetime
    global CACHE, last_time_mood, last_weather
    check_interval = 60  # 检查间隔时间（秒）
    last_trigger_time = 0  # 记录上一次壁纸更新的时间戳
    try:
        while True:
            if not enabled_push.is_set():
                logging.info('[wallpaper_monitor] 等待前端ready_for_push...')
                enabled_push.wait()
            try:
                update_cache()
            except Exception as e:
                logging.error(f'[wallpaper_monitor] 更新缓存失败: {e}')
                time.sleep(10)
                continue
            logging.info("[wallpaper_monitor] 壁纸更新监控线程运行中...")
            time_mood = CACHE['time_mood']
            weather_key = CACHE['weather_key']

            now = datetime.datetime.now()
            is_on_the_hour = (now.minute == 0)
            now_ts = now.timestamp()
            # 距离上次触发超过10分钟才允许整点触发
            allow_on_the_hour = is_on_the_hour and (now_ts - last_trigger_time > 600)

            # 检测到条件变化或首次启动时生成，或整点强制触发（需10分钟间隔）
            if time_mood != last_time_mood or weather_key != last_weather or allow_on_the_hour:
                last_time_mood = time_mood
                last_weather = weather_key
                last_trigger_time = now_ts
                logging.info(f"[wallpaper_monitor] 检测到壁纸条件变化、首次生成或整点触发: {time_mood}, {weather_key}")
                prompt = make_draw_prompt(time_mood, weather_key)
                CACHE['prompt'] = prompt
                filename = get_wallpaper_filename_by_prompts(prompt)
                local_path = get_wallpaper_path(filename)
                if os.path.exists(local_path):
                    logging.info(f"[wallpaper_monitor] 已存在壁纸文件: {local_path}")
                    socketio.emit('refresh_wallpaper', {'time_mood': time_mood, 'weather': weather_key})
                    time.sleep(check_interval)
                    continue
                ret = download_wallpaper(prompt, local_path, max_retries=3)
                if ret == True:
                    socketio.emit('refresh_wallpaper', {'time_mood': time_mood, 'weather': weather_key})

            time.sleep(check_interval)  # 每分钟检测一次
    except Exception as e:
        import traceback
        logging.error("[wallpaper_monitor] 未捕获异常:", e)
        traceback.print_exc()
        # 可选：通知主线程或重启

# 启动监控线程
threading.Thread(target=wallpaper_monitor, daemon=True).start()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9000, help='端口号，默认9000')
    args = parser.parse_args()
    port = args.port
    try:
        logging.info(f"后端服务启动，版本: {__version__}，端口: {port}")
        socketio.run(app, port=port, debug=True, use_reloader=False)
    except Exception as e:
        import traceback
        logging.info("[main] 未捕获异常:", e)
        traceback.print_exc()