<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1>AI Wallpaper 设置</h1>
      <p class="version">版本: {{ version }}</p>
    </div>

    <div class="settings-content">
      <div class="settings-section">
        <h2>Live2D 设置</h2>
        <div class="setting-item">
          <label>启用 Live2D</label>
          <input type="checkbox" v-model="settings.enableLive2D" />
        </div>
        <div class="setting-item">
          <label>鼠标跟踪</label>
          <input type="checkbox" v-model="settings.mouseTracking" />
        </div>
        <div class="setting-item">
          <label>禁用自动动画</label>
          <input type="checkbox" v-model="settings.disableAutoAnimations" />
        </div>
      </div>

      <div class="settings-section">
        <h2>壁纸设置</h2>
        <div class="setting-item">
          <label>壁纸模式</label>
          <select v-model="settings.wallpaperMode">
            <option value="0">窗口模式</option>
            <option value="1">壁纸模式</option>
          </select>
        </div>
      </div>

      <div class="settings-section">
        <h2>API 设置</h2>
        <div class="setting-item">
          <label>Flask API 端口</label>
          <input type="number" v-model="settings.apiPort" min="1000" max="65535" />
        </div>
        <div class="setting-item">
          <label>Flask API 主机</label>
          <input type="text" v-model="settings.apiHost" placeholder="localhost" />
        </div>
      </div>
    </div>

    <div class="settings-footer">
      <button @click="saveSettings" class="btn-primary">保存设置</button>
      <button @click="resetSettings" class="btn-secondary">重置默认</button>
      <button @click="closeWindow" class="btn-secondary">关闭</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';

export default defineComponent({
  name: 'Settings',
  setup() {
    const version = ref('');
    const settings = ref({
      enableLive2D: true,
      mouseTracking: true,
      disableAutoAnimations: true,
      wallpaperMode: '0',
      apiPort: 9000,
      apiHost: 'localhost'
    });

    const loadSettings = () => {
      // 从 electronAPI 获取当前设置
      if ((window as any).electronAPI) {
        version.value = (window as any).electronAPI.version || '0.1.3';
        settings.value.enableLive2D = (window as any).electronAPI.enableLive2D || false;
        settings.value.apiPort = parseInt((window as any).electronAPI.port) || 9000;
        settings.value.apiHost = (window as any).electronAPI.host || 'localhost';
        settings.value.wallpaperMode = (window as any).electronAPI.isWallpaperMode ? '1' : '0';
      }
    };

    const saveSettings = () => {
      console.log('保存设置:', settings.value);
      // TODO: 实现保存设置到配置文件的逻辑
      alert('设置已保存！（功能待实现）');
    };

    const resetSettings = () => {
      settings.value = {
        enableLive2D: true,
        mouseTracking: true,
        disableAutoAnimations: true,
        wallpaperMode: '0',
        apiPort: 9000,
        apiHost: 'localhost'
      };
      console.log('设置已重置为默认值');
    };

    const closeWindow = () => {
      if ((window as any).electronAPI && (window as any).electronAPI.closeWindow) {
        (window as any).electronAPI.closeWindow();
      } else {
        window.close();
      }
    };

    onMounted(() => {
      loadSettings();
    });

    return {
      version,
      settings,
      saveSettings,
      resetSettings,
      closeWindow
    };
  }
});
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: white;
}

.settings-header {
  text-align: center;
  margin-bottom: 30px;
}

.settings-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
  font-weight: 300;
}

.version {
  margin: 0;
  opacity: 0.8;
  font-size: 0.9em;
}

.settings-content {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 30px;
  backdrop-filter: blur(10px);
  margin-bottom: 30px;
}

.settings-section {
  margin-bottom: 30px;
}

.settings-section:last-child {
  margin-bottom: 0;
}

.settings-section h2 {
  margin: 0 0 20px 0;
  font-size: 1.5em;
  font-weight: 400;
  border-bottom: 2px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 10px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px 0;
}

.setting-item label {
  font-weight: 500;
  flex: 1;
}

.setting-item input,
.setting-item select {
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  min-width: 150px;
}

.setting-item input[type="checkbox"] {
  min-width: auto;
  transform: scale(1.2);
}

.settings-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover {
  background: #45a049;
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}
</style>
