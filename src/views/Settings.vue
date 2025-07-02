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
          <label>Live2D 角色</label>
          <select v-model="settings.selectedModel" :disabled="!settings.enableLive2D">
            <option v-for="model in availableModels" :key="model.id" :value="model.id">
              {{ model.name }} - {{ model.description }}
            </option>
          </select>
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
          <label>壁纸模式 <span class="restart-required">*需重启</span></label>
          <select v-model="settings.wallpaperMode">
            <option value="0">窗口模式</option>
            <option value="1">壁纸模式</option>
          </select>
        </div>
      </div>

      <div class="settings-section">
        <h2>地理位置设置</h2>
        <div class="setting-item">
          <label>自动获取位置</label>
          <input type="checkbox" v-model="settings.autoLocation" />
          <span class="setting-description">启用后将通过IP自动获取地理位置</span>
        </div>
        <div class="setting-item" v-if="!settings.autoLocation">
          <label>省份</label>
          <input type="text" v-model="settings.manualLocation.province" placeholder="请输入省份，如：北京" />
        </div>
        <div class="setting-item" v-if="!settings.autoLocation">
          <label>城市</label>
          <input type="text" v-model="settings.manualLocation.city" placeholder="请输入城市，如：北京" />
        </div>
        <div class="setting-item" v-if="!settings.autoLocation">
          <label>区县</label>
          <input type="text" v-model="settings.manualLocation.county" placeholder="请输入区县，如：朝阳区" />
        </div>
      </div>

      <div class="settings-section">
        <h2>API 设置</h2>
        <div class="setting-item">
          <label>Flask API 端口 <span class="restart-required">*需重启</span></label>
          <input type="number" v-model="settings.apiPort" min="1000" max="65535" />
        </div>
        <div class="setting-item">
          <label>Flask API 主机 <span class="restart-required">*需重启</span></label>
          <input type="text" v-model="settings.apiHost" placeholder="localhost" />
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div v-if="message.show" :class="['message-toast', message.type]">
      {{ message.text }}
    </div>

    <!-- 自定义确认对话框 -->
    <div v-if="confirmDialog.show" class="confirm-overlay">
      <div class="confirm-dialog">
        <div class="confirm-header">
          <h3>{{ confirmDialog.title }}</h3>
        </div>
        <div class="confirm-content">
          <p>{{ confirmDialog.message }}</p>
        </div>
        <div class="confirm-footer">
          <button @click="handleConfirmCancel" class="btn-secondary">取消</button>
          <button @click="handleConfirmOk" class="btn-primary">确定</button>
        </div>
      </div>
    </div>

    <div class="settings-footer">
      <button @click="saveSettings" class="btn-primary">保存设置</button>
      <button @click="resetSettings" class="btn-secondary">重置默认</button>
      <button @click="restartApp" class="btn-warning">重启应用</button>
      <button @click="closeWindow" class="btn-secondary">关闭</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import axios from 'axios';

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
      apiHost: 'localhost',
      selectedModel: 'Senko_Normals',
      autoLocation: true,
      manualLocation: {
        province: '',
        city: '',
        county: ''
      }
    });

    // 可用的Live2D模型列表
    const availableModels = ref<Array<{
      id: string;
      name: string;
      path: string;
      version: string;
      description: string;
    }>>([]);

    // API基础URL
    const getApiBase = () => {
      if (process.env.NODE_ENV === 'development') {
        return '/api';
      } else {
        return `http://${settings.value.apiHost}:${settings.value.apiPort}/api`;
      }
    };

    // 创建可序列化的配置对象
    const createSerializableConfig = () => {
      // 使用JSON.parse(JSON.stringify())来确保对象完全可序列化
      const rawConfig = {
        wallpaperMode: String(settings.value.wallpaperMode),
        enableLive2D: Boolean(settings.value.enableLive2D),
        apiPort: Number(settings.value.apiPort),
        apiHost: String(settings.value.apiHost),
        selectedModel: String(settings.value.selectedModel),
        mouseTracking: Boolean(settings.value.mouseTracking),
        disableAutoAnimations: Boolean(settings.value.disableAutoAnimations),
        autoLocation: Boolean(settings.value.autoLocation),
        manualLocation: {
          province: String(settings.value.manualLocation?.province || ''),
          city: String(settings.value.manualLocation?.city || ''),
          county: String(settings.value.manualLocation?.county || '')
        }
      };

      // 确保返回的是普通对象，没有Vue响应式代理
      return JSON.parse(JSON.stringify(rawConfig));
    };

    // 通知后端地理位置配置变更
    const notifyLocationConfigChange = async () => {
      try {
        const locationData = {
          auto_location: Boolean(settings.value.autoLocation),
          manual_location: {
            province: String(settings.value.manualLocation?.province || ''),
            city: String(settings.value.manualLocation?.city || ''),
            county: String(settings.value.manualLocation?.county || '')
          }
        };

        const response = await axios.post(`${getApiBase()}/location-config`, locationData);
        if (response.data.success) {
          console.log('后端地理位置配置已更新');
          return true;
        } else {
          console.error('通知后端地理位置配置失败:', response.data.error);
          return false;
        }
      } catch (error) {
        console.error('通知后端地理位置配置时发生错误:', error);
        return false;
      }
    };



    // 存储原始配置用于比较
    const originalConfig = ref({
      wallpaperMode: '0',
      enableLive2D: false,
      apiPort: 9000,
      apiHost: 'localhost',
      selectedModel: 'Senko_Normals',
      mouseTracking: true,
      disableAutoAnimations: true,
      autoLocation: true,
      manualLocation: {
        province: '',
        city: '',
        county: ''
      }
    });

    const message = ref({
      show: false,
      text: '',
      type: 'success' // 'success', 'warning', 'error'
    });

    // 自定义确认对话框状态
    const confirmDialog = ref({
      show: false,
      title: '',
      message: '',
      onConfirm: null as (() => void) | null,
      onCancel: null as (() => void) | null
    });

    // 显示自定义确认对话框
    const showConfirm = (title: string, message: string, onConfirm?: () => void, onCancel?: () => void) => {
      confirmDialog.value = {
        show: true,
        title,
        message,
        onConfirm: onConfirm || null,
        onCancel: onCancel || null
      };
    };

    // 处理确认对话框的确定按钮
    const handleConfirmOk = () => {
      confirmDialog.value.show = false;
      if (confirmDialog.value.onConfirm) {
        confirmDialog.value.onConfirm();
      }
    };

    // 处理确认对话框的取消按钮
    const handleConfirmCancel = () => {
      confirmDialog.value.show = false;
      if (confirmDialog.value.onCancel) {
        confirmDialog.value.onCancel();
      }
    };

    // 显示消息提示
    const showMessage = (text: string, type: 'success' | 'warning' | 'error' = 'success', duration: number = 3000) => {
      message.value = {
        show: true,
        text,
        type
      };

      // 自动隐藏消息
      setTimeout(() => {
        message.value.show = false;
      }, duration);
    };

    const loadSettings = async () => {
      // 从 electronAPI 获取当前设置
      if ((window as any).electronAPI) {
        version.value = (window as any).electronAPI.version || '0.1.3';

        try {
          // 从配置文件加载设置
          const config = await (window as any).electronAPI.getAppConfig();
          if (config) {
            settings.value.enableLive2D = config.enableLive2D;
            settings.value.wallpaperMode = config.wallpaperMode;
            settings.value.apiPort = Number(config.apiPort);
            settings.value.apiHost = String(config.apiHost);
            settings.value.autoLocation = config.autoLocation !== false;
            settings.value.manualLocation = config.manualLocation || {
              province: '',
              city: '',
              county: ''
            };

            // 同时更新原始配置用于后续比较
            originalConfig.value = {
              wallpaperMode: config.wallpaperMode,
              enableLive2D: config.enableLive2D,
              apiPort: Number(config.apiPort),
              apiHost: String(config.apiHost),
              selectedModel: settings.value.selectedModel,
              mouseTracking: settings.value.mouseTracking,
              disableAutoAnimations: settings.value.disableAutoAnimations,
              autoLocation: Boolean(settings.value.autoLocation),
              manualLocation: {
                province: String(settings.value.manualLocation?.province || ''),
                city: String(settings.value.manualLocation?.city || ''),
                county: String(settings.value.manualLocation?.county || '')
              }
            };

            console.log('设置已加载:', config);
          }

          // 加载Live2D相关设置
          const live2dConfig = await (window as any).electronAPI.readLive2DConfig();
          if (live2dConfig) {
            // 加载可用模型列表
            availableModels.value = live2dConfig.models || [];

            // 设置当前选中的模型
            settings.value.selectedModel = live2dConfig.default || 'Senko_Normals';

            // 加载其他Live2D设置
            if (live2dConfig.settings) {
              settings.value.mouseTracking = live2dConfig.settings.enableMouseTracking !== false;
              settings.value.disableAutoAnimations = live2dConfig.settings.disableAutoAnimations !== false;
            }

            // 更新原始配置中的Live2D部分
            originalConfig.value.selectedModel = settings.value.selectedModel;
            originalConfig.value.mouseTracking = settings.value.mouseTracking;
            originalConfig.value.disableAutoAnimations = settings.value.disableAutoAnimations;
          }
        } catch (error) {
          console.error('加载设置失败:', error);
        }
      }
    };

    const saveSettings = async () => {
      console.log('保存设置:', settings.value);

      if ((window as any).electronAPI) {
        try {
          // 保存应用配置
          const configToSave = createSerializableConfig();

          const result = await (window as any).electronAPI.saveAppConfig(configToSave);

          if (result.success) {
            // 检查是否有需要重启的配置项发生了变化（使用存储的原始配置）
            const needsRestart = (
              originalConfig.value.wallpaperMode !== configToSave.wallpaperMode ||
              originalConfig.value.apiPort !== configToSave.apiPort ||
              originalConfig.value.apiHost !== configToSave.apiHost
            );

            // 更新原始配置为当前保存的配置
            originalConfig.value = {
              ...configToSave
            };

            // 通知后端地理位置配置变更
            const locationNotified = await notifyLocationConfigChange();
            if (!locationNotified) {
              console.warn('通知后端地理位置配置失败，但本地配置已保存');
            }

            if (needsRestart) {
              showMessage('设置已保存！壁纸模式、API端口或API主机的更改需要重启应用才能生效。', 'warning', 5000);
            } else {
              showMessage('设置已保存！', 'success');
            }
            console.log('设置保存成功:', result.message);
          } else {
            showMessage('保存设置失败：' + result.message, 'error');
            console.error('设置保存失败:', result.message);
          }
        } catch (error: any) {
          console.error('保存设置时发生错误:', error);
          showMessage('保存设置时发生错误：' + (error.message || error), 'error');
        }
      } else {
        showMessage('无法访问Electron API，请确保在Electron环境中运行', 'error');
      }
    };

    const resetSettings = () => {
      showConfirm(
        '重置设置',
        '确定要重置所有设置为默认值吗？',
        () => {
          // 确认重置
          settings.value = {
            enableLive2D: false,
            mouseTracking: true,
            disableAutoAnimations: true,
            wallpaperMode: '0',
            apiPort: 9000,
            apiHost: 'localhost',
            selectedModel: 'Senko_Normals',
            autoLocation: true,
            manualLocation: {
              province: '',
              city: '',
              county: ''
            }
          };
          console.log('设置已重置为默认值');
        }
      );
    };

    const restartApp = () => {
      showConfirm(
        '重启应用',
        '确定要重启应用吗？未保存的更改将会丢失。',
        () => {
          // 确认重启
          if ((window as any).electronAPI && (window as any).electronAPI.restartApp) {
            (window as any).electronAPI.restartApp();
          } else {
            showMessage('无法重启应用，请手动重启', 'error');
          }
        }
      );
    };

    const closeWindow = () => {
      if ((window as any).electronAPI && (window as any).electronAPI.closeWindow) {
        (window as any).electronAPI.closeWindow();
      } else {
        window.close();
      }
    };

    onMounted(async () => {
      await loadSettings();
    });

    return {
      version,
      settings,
      availableModels,
      message,
      confirmDialog,
      saveSettings,
      resetSettings,
      restartApp,
      closeWindow,
      handleConfirmOk,
      handleConfirmCancel
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

.restart-required {
  color: #FF9800;
  font-size: 0.8em;
  font-weight: 400;
  opacity: 0.9;
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

.setting-description {
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 10px;
  font-style: italic;
}

.settings-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.btn-primary,
.btn-secondary,
.btn-warning {
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

.btn-warning {
  background: #FF9800;
  color: white;
}

.btn-warning:hover {
  background: #F57C00;
  transform: translateY(-2px);
}

/* 消息提示样式 */
.message-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 9999;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
}

.message-toast.success {
  background: #4CAF50;
}

.message-toast.warning {
  background: #FF9800;
}

.message-toast.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 自定义确认对话框样式 */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  animation: fadeIn 0.3s ease-out;
}

.confirm-dialog {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
  overflow: hidden;
  animation: scaleIn 0.3s ease-out;
}

.confirm-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
}

.confirm-header h3 {
  margin: 0;
  font-size: 1.2em;
  font-weight: 500;
}

.confirm-content {
  padding: 30px 20px;
  text-align: center;
  color: #333;
}

.confirm-content p {
  margin: 0;
  font-size: 1em;
  line-height: 1.5;
}

.confirm-footer {
  padding: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  background: #f8f9fa;
}

.confirm-footer .btn-primary,
.confirm-footer .btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.confirm-footer .btn-primary {
  background: #4CAF50;
  color: white;
}

.confirm-footer .btn-primary:hover {
  background: #45a049;
}

.confirm-footer .btn-secondary {
  background: #6c757d;
  color: white;
}

.confirm-footer .btn-secondary:hover {
  background: #5a6268;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
