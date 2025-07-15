<template>
  <div class="home">
    <WallpaperDisplay
      v-if="wallpaperUrl"
      :wallpaperUrl="wallpaperUrl"
      :title="''"
      :description="''"
    />
    <TimeDisplay v-if="wallpaperUrl" />
    <WeatherDisplay
      v-if="wallpaperUrl"
      :weather="weather"
      :temperature="temperature"
      :humidity="humidity"
      :windPower="windPower"
      :province="province"
      :city="city"
      :county="county"
    />
    <div v-if="wallpaperUrl" class="prompt-panel">
      <div class="prompt-desc">Prompt：{{ prompt }}</div>
      <div class="scene-desc">场景：{{ timeMood }} {{ weather }} </div>
    </div>
    <div class="app-version" style="position:fixed;left:20px;bottom:16px;color:#aaa;font-size:14px;z-index:99;">ver:{{ coreVersion }}(bv:{{ backend_version }})</div>
    <div v-if="backendError" class="loading">{{ backendError }}</div>
    <div v-else-if="!wallpaperUrl" class="loading">正在加载壁纸...</div>
    <div v-if="!isWallpaperMode" class="exit-btn" @click="exitWallpaper">退出壁纸</div>
    <div v-if="enableLive2D" id="live2d-container"></div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import WallpaperDisplay from '../components/WallpaperDisplay.vue';
import TimeDisplay from '../components/TimeDisplay.vue';
import WeatherDisplay from '../components/WeatherDisplay.vue';
import { io } from 'socket.io-client';
import { createLive2DManager, Live2DManager } from '../utils/live2d-manager';

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

let enableLive2D = ref(true);
if (typeof window !== 'undefined' && window.electronAPI) {
  if(!window.electronAPI.enableLive2D)
    enableLive2D.value = false;
}

export default defineComponent({
  name: 'Home',
  components: {
    WallpaperDisplay,
    TimeDisplay,
    WeatherDisplay
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

    const refreshWallpaper = async () => {
      try {
        frontendLog('开始强制刷新壁纸...');
        const res = await axios.post(`${API_BASE}/refresh-wallpaper`, {}, {
          timeout: 60000 // 增加超时时间到60秒，因为AI图片生成可能需要较长时间
        });
        console.log('强制刷新壁纸API返回:', res.data);
        // 只有res.data中存在'success'key为true才是成功
        if (!res.data.success) {
          console.error('强制刷新壁纸失败:', res.data.error);
          frontendLog('强制刷新壁纸失败: ' + res.data.error, 'WARN');
          return;
        }
        // 刷新成功后，重新获取壁纸数据
        await fetchWallpaper();
        frontendLog('强制刷新壁纸成功: ' + JSON.stringify(res.data));
      } catch (error: any) {
        console.error('强制刷新壁纸失败:', error);

        // 区分不同类型的错误
        let errorMsg = '未知错误';
        if (error.response) {
          // 服务器返回了错误状态码
          errorMsg = `服务器错误 ${error.response.status}: ${error.response.data?.error || error.response.statusText}`;
        } else if (error.request) {
          // 请求发出但没有收到响应
          errorMsg = '网络请求超时或无响应';
        } else {
          // 其他错误
          errorMsg = error.message || '请求配置错误';
        }

        frontendLog(`强制刷新壁纸失败: ${errorMsg}`, 'ERROR');

        // 不要因为壁纸刷新失败就断开socket连接
        // socket连接应该保持稳定，独立于API请求的成功与否
      }
    };

    // 同步地理位置配置到后端
    const syncLocationConfigToBackend = async () => {
      try {
        // 检查是否在Electron环境中
        if ((window as any).electronAPI) {
          frontendLog('开始同步地理位置配置到后端...');

          // 从配置文件读取地理位置设置
          const config = await (window as any).electronAPI.getAppConfig();
          if (config) {
            const locationData = {
              auto_location: Boolean(config.autoLocation),
              manual_location: {
                province: String(config.manualLocation?.province || ''),
                city: String(config.manualLocation?.city || ''),
                county: String(config.manualLocation?.county || '')
              }
            };

            const response = await axios.post(`${API_BASE}/location-config`, locationData, {
              timeout: 5000 // 5秒超时
            });

            if (response.data.success) {
              frontendLog('地理位置配置同步成功');
              console.log('地理位置配置同步成功:', locationData);
            } else {
              console.error('地理位置配置同步失败:', response.data.error);
              frontendLog('地理位置配置同步失败: ' + response.data.error);
            }
          } else {
            frontendLog('无法读取应用配置，跳过地理位置配置同步');
          }
        } else {
          console.log('非Electron环境，跳过地理位置配置同步');
        }
      } catch (error) {
        console.error('同步地理位置配置时发生错误:', error);
        frontendLog('同步地理位置配置时发生错误: ' + error);
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

    // 创建Live2D管理器
    const live2dManager = createLive2DManager(enableLive2D);

    onMounted(async () => {
      // 监听主进程show-error事件
      if (window.electron && window.electron.ipcRenderer) {
        window.electron.ipcRenderer.on('show-error', (event: any, msg: any) => {
          alert(msg); // 可替换为UI库的弹窗
        });

        // 监听配置更新事件
        window.electron.ipcRenderer.on('config-updated', (event: any, config: any) => {
          console.log('配置已更新:', config);
          const wasEnabled = enableLive2D.value;
          enableLive2D.value = config.enableLive2D;

          if (config.enableLive2D && !wasEnabled) {
            // Live2D被启用，初始化
            console.log('Live2D被启用，正在初始化...');
            live2dManager.init();
          } else if (!config.enableLive2D && wasEnabled) {
            // Live2D被禁用，销毁
            console.log('Live2D被禁用，正在销毁...');
            live2dManager.destroy();
          } else if (config.enableLive2D && wasEnabled) {
            // Live2D已启用，检查是否需要重新加载（角色更换等）
            if (config.selectedModel || config.mouseTracking !== undefined || config.disableAutoAnimations !== undefined) {
              console.log('Live2D配置已更新，正在重新加载...');
              live2dManager.reload();
            }
          }
        });

        // 监听刷新壁纸事件
        window.electron.ipcRenderer.on('refresh-wallpaper', () => {
          console.log('收到刷新壁纸请求');
          frontendLog('收到刷新壁纸请求');
          refreshWallpaper();
        });
      }
      // 检查后端是否就绪
      const ready = await waitForBackendReady();
      frontendLog('后端服务就绪: ' + ready);
      if (!ready) return;

      // 同步地理位置配置到后端
      await syncLocationConfigToBackend();

      fetchWallpaper();
      // 连接socket.io
      socket = io(SOCKET_BASE, {
        autoConnect: true,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
        timeout: 20000
      });

      socket.on('refresh_wallpaper', (data: any) => {
        frontendLog('收到后端刷新壁纸事件: ' + JSON.stringify(data));
        fetchWallpaper();
      });

      socket.on('connect', () => {
        frontendLog('socket.io已连接');
        // 通知后端前端已准备好接收推送
        socket.emit('ready_for_push');
      });

      socket.on('disconnect', (reason: string) => {
        frontendLog(`socket.io断开连接: ${reason}`, 'WARN');
      });

      socket.on('connect_error', (error: any) => {
        frontendLog(`socket.io连接错误: ${error.message}`, 'ERROR');
      });

      socket.on('reconnect', (attemptNumber: number) => {
        frontendLog(`socket.io重连成功 (尝试次数: ${attemptNumber})`, 'INFO');
      });

      socket.on('reconnect_error', (error: any) => {
        frontendLog(`socket.io重连失败: ${error.message}`, 'ERROR');
      });

      // 初始化Live2D（如果启用）
      if (enableLive2D.value) {
        await live2dManager.init();
      }
      // 原来的Live2D初始化代码位置

    });
    onUnmounted(() => {
      frontendLog('onUnmounted 触发');
      if (socket) {
        socket.close();
        frontendLog('socket.io已断开连接');
      }
      // 清理Live2D资源
      live2dManager.destroy();
    });

    return { wallpaperUrl, prompt, weather, temperature, humidity, windPower, province, city, county, timeMood, isWallpaperMode, backend_version, coreVersion, backendError, exitWallpaper, enableLive2D };
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
#live2d-container {
  position: fixed;
  right: 40px;
  bottom: 0;
  z-index: 20;
  pointer-events: none;
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