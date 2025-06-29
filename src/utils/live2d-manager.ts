import { ref, Ref } from 'vue';

export interface Live2DConfig {
  models: Array<{
    id: string;
    name: string;
    path: string;
    version: string;
    description: string;
  }>;
  default: string;
  settings: {
    enableMouseTracking: boolean;
    disableAutoAnimations: boolean;
    scale: number;
    position: {
      x: number;
      y: number;
    };
  };
}

export interface Live2DModel {
  id: string;
  name: string;
  path: string;
  version: string;
  description: string;
}

export class Live2DModelManager {
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

export class Live2DManager {
  private isInitialized = false;
  private app: any = null;
  private model: any = null;
  private modelManager: Live2DModelManager;
  private enableLive2D: Ref<boolean>;

  constructor(enableLive2D: Ref<boolean>) {
    this.enableLive2D = enableLive2D;
    this.modelManager = new Live2DModelManager();
  }

  private async loadScript(src: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // 检查脚本是否已经加载
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.onload = () => resolve();
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async init(): Promise<boolean> {
    if (!this.enableLive2D.value || this.isInitialized || document.getElementById('live2d-canvas')) {
      return false;
    }

    try {
      console.log('Live2D初始化开始...');

      // 先加载必要的脚本
      await this.loadScript('./live2d.min.js');
      await this.loadScript('./live2dcubismcore.min.js');

      const container = document.getElementById('live2d-container');
      if (!container) {
        console.error('Live2D container not found');
        return false;
      }

      // 检查Live2D运行时是否加载
      if (!(window as any).Live2D || !(window as any).Live2DCubismCore) {
        console.error('Live2D runtime not loaded');
        return false;
      }

      // 使用项目中的PIXI和Live2D
      const PIXI = (window as any).PIXI || require('pixi.js');
      const { Live2DModel } = require('pixi-live2d-display');

      // 注册Ticker
      Live2DModel.registerTicker(PIXI.Ticker);

      // 创建模型管理器并加载配置
      const config = await this.modelManager.loadConfig();
      if (!config) {
        console.error('Failed to load Live2D models config');
        return false;
      }

      const settings = this.modelManager.getSettings();
      const configScale = settings.scale || 0.8;

      // 根据缩放动态调整canvas大小
      const baseWidth = 240;
      const baseHeight = 400;
      const canvasWidth = Math.max(baseWidth, baseWidth * configScale);
      const canvasHeight = Math.max(baseHeight, baseHeight * configScale);

      // 创建PIXI应用
      this.app = new PIXI.Application({
        width: canvasWidth,
        height: canvasHeight,
        transparent: true,
        antialias: true
      });

      // 使用配置文件中的position设置canvas位置
      const position = settings.position || { x: 1.0, y: 1.0 };
      console.log('Canvas position from config:', position);

      const canvas = this.app.view;
      canvas.id = 'live2d-canvas';
      canvas.style.position = 'fixed';

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

      // 加载模型
      await this.loadModel();

      this.isInitialized = true;
      console.log('Live2D初始化完成');
      return true;

    } catch (error) {
      console.error('Failed to initialize Live2D:', error);
      return false;
    }
  }

  private async loadModel(): Promise<void> {
    try {
      // 获取默认模型或指定模型
      const selectedModel = this.modelManager.getDefaultModel();
      if (selectedModel) {
        console.log('Loading model:', selectedModel.name);
        const modelPath = this.modelManager.getModelPath('./' + selectedModel.path);

        const { Live2DModel } = require('pixi-live2d-display');

        this.model = await Live2DModel.from(modelPath);
        console.log('Live2D v3 model loaded:', this.model);

        // 设置模型锚点和位置
        if (selectedModel.version === "v2") {
          this.model.anchor.set(0.5, 1.1);
        } else {
          this.model.anchor.set(0.5, 1.0);
        }

        this.model.x = this.app.screen.width * 0.5;
        this.model.y = this.app.screen.height * 1.0;

        const modelScale = 0.95;
        const scale = Math.min(
          this.app.screen.width / this.model.width * modelScale,
          this.app.screen.height / this.model.height * modelScale
        );
        this.model.scale.set(scale);

        console.log('model scale:', {
          scale: modelScale,
          finalScale: scale
        });

        this.app.stage.addChild(this.model);
        console.log('Live2D v3 model loaded successfully with mouse tracking');
      } else {
        console.error('No model found to load');
      }
    } catch (error) {
      console.error('Failed to load Live2D model:', error);
    }
  }

  destroy(): void {
    console.log('Live2D销毁开始...');

    if (this.model) {
      if (this.app && this.app.stage) {
        this.app.stage.removeChild(this.model);
      }
      this.model.destroy();
      this.model = null;
    }

    if (this.app) {
      this.app.destroy(true);
      this.app = null;
    }

    const canvas = document.getElementById('live2d-canvas');
    if (canvas) {
      canvas.remove();
    }

    this.isInitialized = false;
    console.log('Live2D销毁完成');
  }

  isActive(): boolean {
    return this.isInitialized && this.enableLive2D.value;
  }

  async toggle(): Promise<void> {
    if (this.enableLive2D.value && !this.isInitialized) {
      await this.init();
    } else if (!this.enableLive2D.value && this.isInitialized) {
      this.destroy();
    }
  }
}

// 创建全局Live2D管理器实例
let live2dManagerInstance: Live2DManager | null = null;

export function createLive2DManager(enableLive2D: Ref<boolean>): Live2DManager {
  if (live2dManagerInstance) {
    live2dManagerInstance.destroy();
  }
  live2dManagerInstance = new Live2DManager(enableLive2D);
  return live2dManagerInstance;
}

export function getLive2DManager(): Live2DManager | null {
  return live2dManagerInstance;
}
