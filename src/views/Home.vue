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
    <div v-if="enableLive2D" id="live2d-container"></div>
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

let enableLive2D = ref(false);
if (typeof window !== 'undefined' && window.electronAPI && window.electronAPI.enableLive2D) {
  enableLive2D.value = true;
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

    // Live2D初始化函数
    const initLive2D = async () => {
      if (!enableLive2D.value || document.getElementById('live2d-canvas')) {
        return;
      }
      console.log('Live2D初始化开始...');
      // TODO: 实现完整的Live2D初始化逻辑
      // 先加载必要的脚本
      const loadScript = (src: string): Promise<void> => {
        return new Promise((resolve, reject) => {
          const script = document.createElement('script');
          script.src = src;
          script.onload = () => resolve();
          script.onerror = reject;
          document.head.appendChild(script);
        });
      };

      try {
        // 使用本地文件，避免CDN问题
        await loadScript('./live2d.min.js');
        await loadScript('./live2dcubismcore.min.js');

        const container = document.getElementById('live2d-container');
        if (container) {
          // 检查Live2D运行时是否加载
          if (!(window as any).Live2D || !(window as any).Live2DCubismCore) {
            console.error('Live2D runtime not loaded');
            return;
          }

          // 使用项目中的PIXI和Live2D
          const PIXI = (window as any).PIXI || require('pixi.js');
          const { Live2DModel } = require('pixi-live2d-display');

          // Live2D模型管理器
          class Live2DModelManager {
            private models: any[] = [];
            private settings: any = {};
            private defaultModel: string = "haru";

            async loadConfig() {
              try {
                // 检查是否在Electron环境中
                if (!(process.env.NODE_ENV === 'development') && (window as any).electronAPI) {
                  // 打包后的Electron环境，使用IPC读取文件
                  const config = await (window as any).electronAPI.readLive2DConfig();
                  if (config) {
                    this.models = config.models || [];
                    this.settings = config.settings || {};
                    this.defaultModel = config.default || 'haru';
                    console.log('Live2D models config loaded via IPC:', this.models);
                    return config;
                  }
                } else {
                  // 开发环境，使用fetch
                  const configPath = './static/live2d/models.json';
                  const response = await fetch(configPath);
                  const config = await response.json();
                  this.models = config.models || [];
                  this.settings = config.settings || {};
                  this.defaultModel = config.default || 'haru';
                  console.log('Live2D models config loaded via fetch:', this.models);
                  return config;
                }
              } catch (error) {
                console.error('Failed to load Live2D models config:', error);
                return null;
              }
            }

            getModelPath(modelPath: string) {
              // 检查是否在Electron环境中
              if (!(process.env.NODE_ENV === 'development')) {
                // 使用自定义协议
                const resourcePath = modelPath.replace('./', '');
                const customProtocolPath = `app-resource://${resourcePath}`;
                return customProtocolPath;
              }
              // 开发环境或Web环境，使用相对路径
              return modelPath;
            }

            getModelById(id: string) {
              return this.models.find(model => model.id === id);
            }

            getDefaultModel() {
              const config = this.models.find(model => model.id === this.defaultModel) || this.models[0];
              return config;
            }

            getSettings() {
              return this.settings;
            }
          }

          // 注册Ticker
          Live2DModel.registerTicker(PIXI.Ticker);

          // 创建模型管理器并加载配置
          const modelManager = new Live2DModelManager();
          const config = await modelManager.loadConfig();
          if (!config) {
            console.error('Failed to load Live2D models config');
            return;
          }

          const settings = modelManager.getSettings();
          const configScale = settings.scale || 0.8;

          // 根据缩放动态调整canvas大小
          const baseWidth = 240;
          const baseHeight = 400;
          const canvasWidth = Math.max(baseWidth, baseWidth * configScale);
          const canvasHeight = Math.max(baseHeight, baseHeight * configScale);

          // 创建PIXI应用
          const app = new PIXI.Application({
            width: canvasWidth,
            height: canvasHeight,
            transparent: true,
            antialias: true
          });
          // 使用配置文件中的position设置canvas位置
          const position = settings.position || { x: 1.0, y: 1.0 };
          console.log('Canvas position from config:', position);
          const canvas = app.view;
          canvas.id = 'live2d-canvas';
          canvas.style.position =  'fixed'; //'absolute';
          // canvas.style.right = '0';
          // canvas.style.bottom = '0';
          let transformX = '';
          let transformY = '';

          // 设置水平位置
          if (position.x === 0.5) {
            // 水平居中
            canvas.style.left = '50%';
            transformX = 'translateX(-50%)';
          } else if (position.x < 0.5) {
            // 左侧
            const leftPercent = position.x * 100;
            canvas.style.left = `${leftPercent}%`;
          } else {
            // 右侧
            const rightPercent = (1 - position.x) * 100;
            canvas.style.right = `${rightPercent}%`;
          }
        
          // 设置垂直位置
          if (position.y === 0.5) {
            // 垂直居中
            canvas.style.top = '50%';
            transformY = 'translateY(-50%)';
          } else if (position.y < 0.5) {
            // 上方
            const topPercent = position.y * 100;
            canvas.style.top = `${topPercent}%`;
          } else {
            // 下方
            const bottomPercent = (1 - position.y) * 100;
            canvas.style.bottom = `${bottomPercent}%`;
          }
          canvas.style.pointerEvents = 'none';
          container.appendChild(canvas);

          try {
              // 获取默认模型或指定模型
              const selectedModel = modelManager.getDefaultModel();
              if (selectedModel) {
                console.log('Loading model:', selectedModel.name);
                const modelPath = modelManager.getModelPath('./' + selectedModel.path);

                Live2DModel.from(modelPath)
            .then((model: any) => {
              console.log('Live2D v3 model loaded:', model); 
              // console.log('Live2D v3 model internal:', model.internalModel);

              // 禁用所有自动动画（Live2D v3方式）
              // if (model.internalModel) {
              //   const internal = model.internalModel;

              //   // 禁用眨眼 - v3方式
              //   try {
              //     if (internal.eyeBlink) {
              //       // 尝试不同的禁用方法
              //       if (typeof internal.eyeBlink.setEnable === 'function') {
              //         internal.eyeBlink.setEnable(false);
              //       } else {
              //         // v3可能使用不同的方法
              //         internal.eyeBlink = null;
              //       }
              //       console.log('Eye blink disabled');
              //     }
              //   } catch (e) {
              //     console.log('Could not disable eye blink:', e);
              //   }

              //   // 禁用呼吸 - v3方式
              //   try {
              //     if (internal.breath) {
              //       if (typeof internal.breath.setEnable === 'function') {
              //         internal.breath.setEnable(false);
              //       } else {
              //         internal.breath = null;
              //       }
              //       console.log('Breath disabled');
              //     }
              //   } catch (e) {
              //     console.log('Could not disable breath:', e);
              //   }

              //   // 停止所有动画
              //   try {
              //     if (internal.motionManager) {
              //       internal.motionManager.stopAllMotions();
              //       console.log('All motions stopped');
              //     }
              //   } catch (e) {
              //     console.log('Could not stop motions:', e);
              //   }
              // }

              // 使用已加载的配置文件设置

              // 设置模型锚点和位置
              if(selectedModel.version === "v2") {
                model.anchor.set(0.5, 1.1);
              } else {
                model.anchor.set(0.5, 1.0);
              }
              model.x = app.screen.width * 0.5;
              model.y = app.screen.height * 1.0;
              const modelScale = 0.95;
              const scale = Math.min(
                app.screen.width / model.width * modelScale,
                app.screen.height / model.height * modelScale
              );
              model.scale.set(scale);

              console.log('model scale:', {
                scale: modelScale,
                finalScale: scale
              });

              app.stage.addChild(model);
              console.log('Live2D v3 model loaded successfully with mouse tracking');
            })
            .catch((error: any) => {
              console.error('Failed to load Live2D v3 model:', error);
            });
              } else {
                console.error('No model found to load');
              }
          } catch (error) {
            console.error('Failed to initialize Live2D:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load Live2D scripts:', error);
      }
    
    };

    // 销毁Live2D
    const destroyLive2D = () => {
      const canvas = document.getElementById('live2d-canvas');
      if (canvas) {
        canvas.remove();
        console.log('Live2D destroyed');
      }
    };

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
            initLive2D();
          } else if (!config.enableLive2D && wasEnabled) {
            // Live2D被禁用，销毁
            console.log('Live2D被禁用，正在销毁...');
            destroyLive2D();
          }
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

      // 初始化Live2D（如果启用）
      if (enableLive2D.value) {
        await initLive2D();
      }
      // 原来的Live2D初始化代码位置

    });
    onUnmounted(() => {
      frontendLog('onUnmounted 触发');
      if (socket) {
        socket.close();
        frontendLog('socket.io已断开连接');
      }
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