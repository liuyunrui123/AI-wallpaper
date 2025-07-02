<template>
  <div class="settings-container">
    <!-- 左侧导航 -->
    <div class="settings-sidebar">
      <div class="sidebar-header">
        <h1>AI Wallpaper</h1>
        <p class="version">v{{ version }}</p>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="category in categories"
          :key="category.id"
          :class="['nav-item', { active: activeCategory === category.id }]"
          @click="activeCategory = category.id"
        >
          <i :class="category.icon"></i>
          <span>{{ category.name }}</span>
        </div>
      </nav>
    </div>

    <!-- 右侧内容区 -->
    <div class="settings-content">
      <div class="content-header">
        <h2>{{ getCurrentCategory().name }}</h2>
        <p class="category-description">{{ getCurrentCategory().description }}</p>
      </div>

      <div class="content-body">
        <!-- 基础设置 -->
        <div v-if="activeCategory === 'basic'" class="settings-section">
          <div class="setting-card">
            <h3>壁纸设置</h3>
            <div class="setting-item">
              <div class="setting-label">
                <label>壁纸模式</label>
                <span class="restart-required">*需重启</span>
              </div>
              <select v-model="settings.wallpaperMode">
                <option value="0">窗口模式</option>
                <option value="1">壁纸模式</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 外观设置 -->
        <div v-if="activeCategory === 'appearance'" class="settings-section">
          <div class="setting-card">
            <h3>Live2D 设置</h3>
            <div class="setting-item">
              <label>启用 Live2D</label>
              <input type="checkbox" v-model="settings.enableLive2D" />
            </div>
            <div class="setting-item" v-if="settings.enableLive2D">
              <label>Live2D 角色</label>
              <select v-model="settings.selectedModel">
                <option v-for="model in availableModels" :key="model.id" :value="model.id">
                  {{ model.name }} - {{ model.description }}
                </option>
              </select>
            </div>
            <div class="setting-item" v-if="settings.enableLive2D">
              <label>鼠标跟踪</label>
              <input type="checkbox" v-model="settings.mouseTracking" />
            </div>
            <div class="setting-item" v-if="settings.enableLive2D">
              <label>禁用自动动画</label>
              <input type="checkbox" v-model="settings.disableAutoAnimations" />
            </div>
          </div>
        </div>

        <!-- 位置设置 -->
        <div v-if="activeCategory === 'location'" class="settings-section">
          <div class="setting-card">
            <h3>地理位置设置</h3>
            <div class="setting-item">
              <div class="setting-label">
                <label>自动获取位置</label>
                <span class="setting-description">启用后将通过IP自动获取地理位置</span>
              </div>
              <input type="checkbox" v-model="settings.autoLocation" />
            </div>
            <div class="manual-location" :class="{ disabled: settings.autoLocation }">
              <label>手动设置地理位置</label>
              <div class="setting-item">
                <label>省份</label>
                <input
                  type="text"
                  v-model="settings.manualLocation.province"
                  placeholder="请输入省份，如：北京"
                  :disabled="settings.autoLocation"
                />
              </div>
              <div class="setting-item">
                <label>城市</label>
                <input
                  type="text"
                  v-model="settings.manualLocation.city"
                  placeholder="请输入城市，如：北京"
                  :disabled="settings.autoLocation"
                />
              </div>
              <div class="setting-item">
                <label>区县</label>
                <input
                  type="text"
                  v-model="settings.manualLocation.county"
                  placeholder="请输入区县，如：朝阳区"
                  :disabled="settings.autoLocation"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 网络设置 -->
        <div v-if="activeCategory === 'network'" class="settings-section">
          <div class="setting-card">
            <h3>API 设置</h3>
            <div class="setting-item">
              <div class="setting-label">
                <label>Flask API 端口</label>
                <span class="restart-required">*需重启</span>
              </div>
              <input type="number" v-model="settings.apiPort" min="1000" max="65535" />
            </div>
            <div class="setting-item">
              <div class="setting-label">
                <label>Flask API 主机</label>
                <span class="restart-required">*需重启</span>
              </div>
              <input type="text" v-model="settings.apiHost" placeholder="localhost" />
            </div>
          </div>
        </div>

        <!-- 关于 -->
        <div v-if="activeCategory === 'about'" class="settings-section">
          <div class="setting-card">
            <h3>应用信息</h3>
            <div class="about-info">
              <div class="info-item">
                <label>应用版本</label>
                <span>{{ version }}</span>
              </div>
              <div class="info-item">
                <label>构建时间</label>
                <span>{{ new Date().toLocaleDateString() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="settings-footer">
        <button @click="saveSettings" :disabled="isSaving" class="btn-primary">
          <span v-if="isSaving">保存中...</span>
          <span v-else>保存设置</span>
        </button>
        <button @click="resetSettings" class="btn-secondary">重置默认</button>
        <button @click="restartApp" class="btn-warning">重启应用</button>
        <button @click="closeWindow" class="btn-secondary">关闭</button>
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

    // 当前活动的分类
    const activeCategory = ref('basic');

    // 设置分类
    const categories = ref([
      {
        id: 'basic',
        name: '基础设置',
        description: '壁纸模式等基础配置',
        icon: 'icon-settings'
      },
      {
        id: 'appearance',
        name: '外观设置',
        description: 'Live2D角色和界面相关设置',
        icon: 'icon-palette'
      },
      {
        id: 'location',
        name: '位置设置',
        description: '地理位置获取和配置',
        icon: 'icon-location'
      },
      {
        id: 'network',
        name: '网络设置',
        description: 'API端口和网络相关配置',
        icon: 'icon-network'
      },
      {
        id: 'about',
        name: '关于',
        description: '应用信息和版本详情',
        icon: 'icon-info'
      }
    ]);

    // 获取当前分类信息
    const getCurrentCategory = () => {
      return categories.value.find(cat => cat.id === activeCategory.value) || categories.value[0];
    };

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

        const response = await axios.post(`${getApiBase()}/location-config`, locationData, {
          timeout: 5000 // 5秒超时
        });
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

    const isSaving = ref(false);

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

      // 设置保存状态，禁用保存按钮
      isSaving.value = true;

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

            // 检查地理位置相关设置是否发生变化
            const locationChanged = (
              originalConfig.value.autoLocation !== configToSave.autoLocation ||
              originalConfig.value.manualLocation?.province !== configToSave.manualLocation?.province ||
              originalConfig.value.manualLocation?.city !== configToSave.manualLocation?.city ||
              originalConfig.value.manualLocation?.county !== configToSave.manualLocation?.county
            );

            // 更新原始配置为当前保存的配置
            originalConfig.value = {
              ...configToSave
            };

            // 立即显示保存成功消息，提升用户体验
            if (needsRestart) {
              showMessage('设置已保存！壁纸模式、API端口或API主机的更改需要重启应用才能生效。', 'warning', 5000);
            } else {
              showMessage('设置已保存！', 'success');
            }
            console.log('设置保存成功:', result.message);

            // 只有地理位置设置发生变化时才通知后端
            if (locationChanged) {
              console.log('检测到地理位置设置变更，通知后端更新');
              // 异步通知后端地理位置配置变更，不阻塞用户界面
              notifyLocationConfigChange().then(locationNotified => {
                if (!locationNotified) {
                  console.warn('通知后端地理位置配置失败，但本地配置已保存');
                  // 可选：显示一个不太显眼的提示
                  // showMessage('后端同步失败，但配置已保存', 'warning', 2000);
                } else {
                  console.log('后端地理位置配置同步成功');
                }
              }).catch(error => {
                console.error('异步通知后端时发生错误:', error);
              });
            } else {
              console.log('地理位置设置未变更，跳过后端通知');
            }
          } else {
            showMessage('保存设置失败：' + result.message, 'error');
            console.error('设置保存失败:', result.message);
          }
        } catch (error: any) {
          console.error('保存设置时发生错误:', error);
          showMessage('保存设置时发生错误：' + (error.message || error), 'error');
        } finally {
          // 无论成功还是失败，都重置保存状态
          isSaving.value = false;
        }
      } else {
        showMessage('无法访问Electron API，请确保在Electron环境中运行', 'error');
        isSaving.value = false;
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
      activeCategory,
      categories,
      getCurrentCategory,
      message,
      confirmDialog,
      isSaving,
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
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 左侧导航栏 */
.settings-sidebar {
  width: 280px;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 25px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h1 {
  margin: 0 0 6px 0;
  font-size: 1.6em;
  font-weight: 600;
  color: white;
}

.sidebar-header .version {
  margin: 0;
  opacity: 0.7;
  font-size: 0.8em;
  color: rgba(255, 255, 255, 0.8);
}

.sidebar-nav {
  flex: 1;
  padding: 15px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: #4CAF50;
}

.nav-item i {
  width: 18px;
  height: 18px;
  margin-right: 10px;
  opacity: 0.8;
  font-style: normal;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.nav-item span {
  font-size: 0.85em;
  font-weight: 500;
}

/* 图标样式 */
.icon-settings::before {
  content: '⚙️';
  font-style: normal;
  font-weight: normal;
  text-rendering: optimizeLegibility;
}
.icon-palette::before {
  content: '🎨';
  font-style: normal;
  font-weight: normal;
  text-rendering: optimizeLegibility;
}
.icon-location::before {
  content: '📍';
  font-style: normal;
  font-weight: normal;
  text-rendering: optimizeLegibility;
}
.icon-network::before {
  content: '🌐';
  font-style: normal;
  font-weight: normal;
  text-rendering: optimizeLegibility;
}
.icon-info::before {
  content: 'ℹ️';
  font-style: normal;
  font-weight: normal;
  text-rendering: optimizeLegibility;
}

/* 右侧内容区 */
.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  padding: 25px 35px 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.content-header h2 {
  margin: 0 0 6px 0;
  font-size: 1.5em;
  font-weight: 600;
}

.category-description {
  margin: 0;
  opacity: 0.8;
  font-size: 0.8em;
}

.content-body {
  flex: 1;
  padding: 25px 35px;
  overflow-y: auto;
}

/* 设置卡片 */
.setting-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  margin-bottom: 20px;
}

.setting-card h3 {
  margin: 0 0 15px 0;
  font-size: 1.1em;
  font-weight: 500;
  color: white;
}

/* 设置项样式 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.setting-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.setting-label {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.setting-item label {
  font-weight: 500;
  margin-bottom: 2px;
  color: white;
  font-size: 0.9em;
}

.setting-description {
  font-size: 0.75em;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
  line-height: 1.3;
}

.restart-required {
  color: #FF9800;
  font-size: 0.7em;
  font-weight: 400;
  margin-left: 6px;
}

/* 输入框样式 */
.setting-item input,
.setting-item select {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  min-width: 150px;
  font-size: 0.85em;
  transition: all 0.3s ease;
}

.setting-item input:focus,
.setting-item select:focus {
  outline: none;
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.5);
}

.setting-item input[type="checkbox"] {
  min-width: auto;
  width: 16px;
  height: 16px;
  transform: scale(1.1);
  cursor: pointer;
}

/* 手动位置设置区域 */
.manual-location {
  margin-top: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.manual-location.disabled {
  opacity: 0.5;
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05);
}

.manual-location.disabled label {
  color: rgba(255, 255, 255, 0.4);
}

.manual-location.disabled input {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.4);
  cursor: not-allowed;
}

.manual-location.disabled input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

/* 关于页面信息 */
.about-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.info-item:last-child {
  border-bottom: none;
}

.info-item label {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.info-item span {
  color: white;
  font-weight: 600;
}

/* 底部按钮区域 */
.settings-footer {
  padding: 20px 35px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn-primary,
.btn-secondary,
.btn-warning {
  padding: 10px 18px;
  border: none;
  border-radius: 6px;
  font-size: 0.9em;
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

/* 禁用状态样式 */
.btn-primary:disabled {
  background: #cccccc;
  color: #666666;
  cursor: not-allowed;
  transform: none;
  opacity: 0.6;
}

.btn-primary:disabled:hover {
  background: #cccccc;
  transform: none;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    flex-direction: column;
  }

  .settings-sidebar {
    width: 100%;
    height: auto;
  }

  .sidebar-nav {
    display: flex;
    overflow-x: auto;
    padding: 10px 0;
  }

  .nav-item {
    min-width: 120px;
    justify-content: center;
    flex-direction: column;
    padding: 10px;
    text-align: center;
  }

  .nav-item i {
    margin-right: 0;
    margin-bottom: 5px;
  }

  .content-header,
  .content-body,
  .settings-footer {
    padding-left: 20px;
    padding-right: 20px;
  }

  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .setting-item input,
  .setting-item select {
    width: 100%;
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .sidebar-header {
    padding: 20px 15px;
  }

  .sidebar-header h1 {
    font-size: 1.5em;
  }

  .content-header,
  .content-body,
  .settings-footer {
    padding-left: 15px;
    padding-right: 15px;
  }

  .setting-card {
    padding: 20px;
  }

  .settings-footer {
    flex-direction: column;
    gap: 10px;
  }

  .settings-footer button {
    width: 100%;
  }
}
</style>
