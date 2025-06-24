<template>
  <div class="home">
    <WallpaperDisplay
      v-if="wallpaperUrl"
      :wallpaperUrl="wallpaperUrl"
      :title="''"
      :description="''"
    />
    <div v-if="wallpaperUrl" class="info-panel">
      <div class="info-card">
        <div class="info-row"><span class="info-label">🌤️ 天气：</span>{{ weather }}</div>
        <div class="info-row"><span class="info-label">🌡️ 温度：</span>{{ temperature }}</div>
        <div class="info-row"><span class="info-label">💧 湿度：</span>{{ humidity }}</div>
        <div class="info-row"><span class="info-label">💨 风力：</span>{{ windPower }}</div>
        <div class="info-row"><span class="info-label">📍 位置：</span>{{ province }}{{ city }}{{ county }}</div>
      </div>
    </div>
    <div v-if="wallpaperUrl" class="prompt-panel">
      <div class="prompt-desc">Prompt：{{ prompt }}</div>
      <div class="scene-desc">场景：{{ timeMood }} {{ weather }} </div>
    </div>
    <div class="app-version" style="position:fixed;left:20px;bottom:16px;color:#aaa;font-size:14px;z-index:99;">ver:{{ coreVersion }}(bv:{{ backend_version }})</div>
    <div v-if="backendError" class="loading">{{ backendError }}</div>
    <div v-else-if="!wallpaperUrl" class="loading">正在加载壁纸...</div>
    <div v-if="!isWallpaperMode" class="exit-btn" @click="exitWallpaper">退出壁纸</div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import WallpaperDisplay from '../components/WallpaperDisplay.vue';
import { io } from 'socket.io-client';

// 优先运行时获取端口和host，打包后可随时改 config.json
let API_PORT = '9000';
let API_HOST = 'localhost';
if (typeof window !== 'undefined' && window.electronAPI) {
  if (window.electronAPI.port) API_PORT = window.electronAPI.port;
  if (window.electronAPI.host) API_HOST = window.electronAPI.host;
} else {
  if (process.env.FLASK_API_PORT) API_PORT = process.env.FLASK_API_PORT;
  if (process.env.FLASK_API_HOST) API_HOST = process.env.FLASK_API_HOST;
}
const API_BASE = process.env.NODE_ENV === 'development'
  ? '/api'
  : `http://${API_HOST}:${API_PORT}/api`;
const STATIC_BASE = process.env.NODE_ENV === 'development'
  ? '/static'
  : `http://${API_HOST}:${API_PORT}/static`;
const SOCKET_BASE = process.env.NODE_ENV === 'development'
  ? ''
  : `http://${API_HOST}:${API_PORT}`;

let isWallpaperMode = false;
if (typeof window !== 'undefined' && window.electronAPI && window.electronAPI.isWallpaperMode) {
  isWallpaperMode = true;
}

export default defineComponent({
  name: 'Home',
  components: {
    WallpaperDisplay
  },
  setup() {
    const wallpaperUrl = ref('');
    const prompt = ref('');
    const weather = ref('');
    const temperature = ref('');
    const humidity = ref('');
    const windPower = ref('');
    const province = ref('');
    const city = ref('');
    const county = ref('');
    const timeMood = ref('');
    const backend_version = ref('');
    let coreVersion = '';
    if (typeof window !== 'undefined' && window.electronAPI && window.electronAPI.version) {
      coreVersion = window.electronAPI.version;
    } 
    const backendReady = ref(false);
    const backendError = ref('');
    let socket: any = null;

    function frontendLog(msg: any, level: string = 'INFO') {
      if (window.electron && window.electron.ipcRenderer) {
        window.electron.ipcRenderer.send('frontend-log', { level, msg });
      } else if (window.require) {
        try {
          const { ipcRenderer } = window.require('electron');
          ipcRenderer.send('frontend-log', { level, msg });
        } catch {}
      }
    }

    const fetchWallpaper = async () => {
      try {
        const res = await axios.get(`${API_BASE}/auto-wallpaper`);
        console.log('壁纸API返回数据:', res.data);
        frontendLog('壁纸API返回数据: ' + JSON.stringify(res.data));
        // 直接更新壁纸，无需判断 time_mood/weather
        let imgUrl = res.data.image_url;
        if (process.env.NODE_ENV !== 'development' && imgUrl.startsWith('/static/')) {
          imgUrl = STATIC_BASE + imgUrl.replace('/static', '');
        }
        wallpaperUrl.value = imgUrl;
        prompt.value = res.data.prompt;
        weather.value = res.data.weather;
        temperature.value = res.data.temperature;
        humidity.value = res.data.humidity;
        windPower.value = res.data.wind_power;
        province.value = res.data.province;
        city.value = res.data.city;
        county.value = res.data.county;
        timeMood.value = res.data.time_mood;
      } catch (e) {
        console.error('壁纸API请求失败:', e);
        frontendLog('壁纸API请求失败: ' + e, 'ERROR');
        wallpaperUrl.value = '';
        prompt.value = '壁纸加载失败';
      }
    };

    const exitWallpaper = () => {
      frontendLog('退出壁纸按钮被点击');
      // 通过Electron IPC退出
      if (window && (window as any).electronAPI) {
        (window as any).electronAPI.exitWallpaper && (window as any).electronAPI.exitWallpaper();
      } else if (window && (window as any).require) {
        // 兼容老版Electron
        const { ipcRenderer } = (window as any).require('electron');
        ipcRenderer.send('exit-wallpaper');
      }
    };

    async function waitForBackendReady(retry = 20, delay = 1000) {
      for (let i = 0; i < retry; i++) {
        try {
          const res = await axios.get(`${API_BASE}/version`);
          if (res.data && res.data.version) {
            backend_version.value = res.data.version;
            backendReady.value = true;
            backendError.value = '';
            return true;
          }
        } catch (e) {
          backendError.value = '后端服务未就绪，正在重试...';
        }
        await new Promise(res => setTimeout(res, delay));
      }
      backendError.value = '后端服务连接失败，请检查后端是否启动。';
      return false;
    }

    onMounted(async () => {
      // 监听主进程show-error事件
      if (window.electron && window.electron.ipcRenderer) {
        window.electron.ipcRenderer.on('show-error', (event: any, msg: any) => {
          alert(msg); // 可替换为UI库的弹窗
        });
      }
      // 检查后端是否就绪
      const ready = await waitForBackendReady();
      frontendLog('后端服务就绪: ' + ready);
      if (!ready) return;
      fetchWallpaper();
      // 连接socket.io
      socket = io(SOCKET_BASE);
      socket.on('refresh_wallpaper', (data: any) => {
        frontendLog('收到后端刷新壁纸事件: ' + JSON.stringify(data));
        fetchWallpaper();
      });
      socket.on('connect', () => {
        frontendLog('socket.io已连接');
        // 通知后端前端已准备好接收推送
        socket.emit('ready_for_push');
      });
    });
    onUnmounted(() => {
      frontendLog('onUnmounted 触发');
      if (socket) {
        socket.close();
        frontendLog('socket.io已断开连接');
      }
    });

    return { wallpaperUrl, prompt, weather, temperature, humidity, windPower, province, city, county, timeMood, isWallpaperMode, backend_version, coreVersion, backendError, exitWallpaper};
  }
});
</script>

<style scoped>
.home {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.info-panel {
  position: absolute;
  right: 40px;
  top: 40px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  z-index: 10;
}
.info-card {
  background: rgba(0,0,0,0.45);
  color: #fff;
  padding: 18px 32px;
  border-radius: 14px;
  font-size: 18px;
  min-width: 220px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  user-select: text;
  text-align: left;
}
.info-row {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
.info-label {
  font-weight: bold;
  margin-right: 8px;
  margin-left: 0;
}
.prompt-panel {
  position: absolute;
  right: 40px;
  bottom: 40px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  z-index: 10;
}
.prompt-desc {
  color: #fff;
  background: rgba(0,0,0,0.35);
  padding: 8px 22px;
  border-radius: 10px;
  font-size: 16px;
  margin-bottom: 10px;
  text-align: right;
  min-width: 120px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  word-break: break-all;
  max-width: 480px;
}
.scene-desc {
  color: #fff;
  background: rgba(0,0,0,0.35);
  padding: 8px 22px;
  border-radius: 10px;
  font-size: 18px;
  text-align: right;
  min-width: 120px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
}
.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 24px;
  background: rgba(0,0,0,0.4);
  padding: 20px 40px;
  border-radius: 8px;
}
.exit-btn {
  position: absolute;
  right: 48px;
  bottom: 48px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 18px;
  padding: 10px 28px;
  border-radius: 10px;
  cursor: pointer;
  z-index: 100;
  transition: background 0.2s;
  user-select: none;
}
.exit-btn:hover {
  background: #e74c3c;
}
</style>