import { ref, Ref } from 'vue';

// Live2D版本类型
export type Live2DVersion = 'v2' | 'v3';

// Live2D位置配置
export interface Live2DPosition {
  x: number; // 0.0-1.0，相对于屏幕宽度的位置
  y: number; // 0.0-1.0，相对于屏幕高度的位置
}

// Live2D模型接口
export interface Live2DModel {
  id: string;
  name: string;
  path: string;
  version: Live2DVersion; // 可选字段
  description?: string; // 可选字段
  model_scale: number; // 可选字段
  model_position?: Live2DPosition; // 可选字段
}

// Live2D设置接口
export interface Live2DSettings {
  enableMouseTracking?: boolean;
  disableAutoAnimations?: boolean;
  scale?: number;
  position?: Live2DPosition;
}

// Live2D配置接口（使用Live2DModel接口）
export interface Live2DConfig {
  models: Live2DModel[];
  default: string;
  settings?: Live2DSettings;
}

export class Live2DModelManager {
  private models: Live2DModel[] = [];
  private settings: Live2DSettings = {};
  private defaultModel: string = "Senko_Normals";

  async loadConfig(): Promise<Live2DConfig | null> {
    try {
      let config: any;

      // 检查是否在Electron环境中
      if (!(process.env.NODE_ENV === 'development') && (window as any).electronAPI) {
        // 打包后的Electron环境，使用IPC读取文件
        config = await (window as any).electronAPI.readLive2DConfig();
      } else {
        // 开发环境，使用fetch
        const configPath = './static/live2d/models.json';
        const response = await fetch(configPath);
        config = await response.json();
      }

      if (config) {
        this.models = config.models || [];
        this.settings = config.settings || {};
        this.defaultModel = config.default || 'Senko_Normals';
        console.log('Live2D models config loaded:', this.models);
        return config as Live2DConfig;
      }
    } catch (error) {
      console.error('Failed to load Live2D models config:', error);
    }

    return null;
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
  private modelConfig: any = null; // 存储当前模型的配置

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
      const baseWidth = 240;
      let baseHeight = 400;
      // 提前获取模型的高与宽的比例
      const selectedModel = this.modelManager.getDefaultModel();
      if (selectedModel) {
        const modelPath = this.modelManager.getModelPath('./' + selectedModel.path);
        await this.loadModelConfig(modelPath);
        this.model = await Live2DModel.from(modelPath);
        const modelRatio = this.model.height / this.model.width;
        // 根据缩放动态调整canvas大小
        baseHeight = baseWidth * modelRatio;
      }
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
      // 给canvas增加可见的边框
      //canvas.style.border = '1px solid red';

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

      canvas.style.pointerEvents = 'auto'; // 允许交互
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

  // 加载模型配置文件
  private async loadModelConfig(modelPath: string): Promise<void> {
    try {
      console.log('加载模型配置:', modelPath);

      // 发送请求获取模型配置
      const response = await fetch(modelPath);
      if (response.ok) {
        this.modelConfig = await response.json();
        console.log('模型配置加载成功:', this.modelConfig);

        // 检查版本并记录可用动作
        if (this.modelConfig.Version === 3) {
          console.log('检测到Live2D v3模型');
          if (this.modelConfig.FileReferences && this.modelConfig.FileReferences.Motions) {
            console.log('可用动作:', Object.keys(this.modelConfig.FileReferences.Motions));
          }
        } else {
          console.log('检测到Live2D v2模型');
          if (this.modelConfig.motions) {
            console.log('可用动作:', Object.keys(this.modelConfig.motions));
          }
        }
      }
    } catch (error) {
      console.warn('加载模型配置失败:', error);
      this.modelConfig = null;
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

        // 加载模型配置以获取动作信息
        await this.loadModelConfig(modelPath);

        // 如果存在model_position，使用model_position设置模型锚点
        if (selectedModel.model_position) {
          this.model.anchor.set(selectedModel.model_position.x, selectedModel.model_position.y);
        } else {
          this.model.anchor.set(0.5, 1.0);
        }

        this.model.x = this.app.screen.width * 0.5;
        this.model.y = this.app.screen.height * 1.0;

        let modelScale = 1.0;
        if (selectedModel.model_scale) {
          modelScale = selectedModel.model_scale;
        }
        // console.log('this.app.screen.width:', this.app.screen.width);
        // console.log('this.app.screen.height:', this.app.screen.height);
        // console.log('this.model.width:', this.model.width);
        // console.log('this.model.height:', this.model.height);
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

        // 添加触摸交互功能
        this.setupTouchInteraction();

        console.log('Live2D v3 model loaded successfully with touch interaction');
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

  async reload(): Promise<void> {
    if (this.enableLive2D.value && this.isInitialized) {
      console.log('重新加载Live2D模型...');
      this.destroy();
      // 等待一小段时间确保销毁完成
      await new Promise(resolve => setTimeout(resolve, 100));
      await this.init();
    }
  }

  // 设置触摸交互功能
  private setupTouchInteraction(): void {
    if (!this.model || !this.app) return;

    console.log('设置Live2D触摸交互...');

    // 使模型可交互
    this.model.interactive = true;
    this.model.buttonMode = true;

    // 允许canvas接收事件
    const canvas = this.app.view;
    canvas.style.pointerEvents = 'auto';

    // 添加点击事件监听器
    this.model.on('pointerdown', (event: any) => {
      this.handleTouch(event);
    });

    // 添加触摸事件监听器（移动设备）
    this.model.on('touchstart', (event: any) => {
      this.handleTouch(event);
    });

    console.log('Live2D触摸交互设置完成');
  }

  // 处理触摸事件
  private handleTouch(event: any): void {
    if (!this.model) return;

    try {
      console.log('Live2D模型被触摸');

      // 获取触摸位置
      const localPoint = event.data.getLocalPosition(this.model);
      const hitArea = this.getHitArea(localPoint);

      console.log('触摸位置:', localPoint);
      console.log('命中区域:', hitArea);

      // 播放相应的触摸动作
      this.playTouchMotion(hitArea);

    } catch (error) {
      console.error('处理触摸事件失败:', error);
    }
  }

  // 获取命中区域
  private getHitArea(point: any): string {
    if (!this.model) return this.getDefaultMotionKey();

    try {
      const modelHeight = this.model.height;

      // 简单的区域划分
      if (point.y < modelHeight * 0.3) {
        console.log('头部区域');
        return this.getHeadMotionKey(); // 头部区域
      } else if (point.y < modelHeight * 0.7) {
        console.log('身体区域');
        return this.getBodyMotionKey(); // 身体区域
      } else {
        console.log('下半身区域');
        return this.getBodyMotionKey(); // 下半身也算身体
      }

    } catch (error) {
      console.warn('获取命中区域失败:', error);
      return this.getDefaultMotionKey();
    }
  }

  // 获取头部动作键名（根据模型配置）
  private getHeadMotionKey(): string {
    if (this.modelConfig) {
      if (this.modelConfig.Version === 3) {
        // V3版本：检查可用的头部动作
        const motions = this.modelConfig.FileReferences?.Motions || {};
        if (motions.TapHead) return 'TapHead';
        if (motions.Taphead) return 'Taphead';
        if (motions.taphead) return 'taphead';
        if (motions.head) return 'head';
        return 'Tap'; // 默认使用Tap
      } else {
        // V2版本：检查可用的头部动作
        const motions = this.modelConfig.motions || {};
        if (motions.flick_head) return 'flick_head';
        if (motions.tap_head) return 'tap_head';
        if (motions.head) return 'head';
        return 'tap_body'; // 默认使用tap_body
      }
    }

    // 如果没有配置，使用版本推测
    const selectedModel = this.modelManager.getDefaultModel();
    if (selectedModel && selectedModel.version === 'v3') {
      return 'TapHead';
    } else {
      return 'flick_head';
    }
  }

  // 获取身体动作键名（根据模型配置）
  private getBodyMotionKey(): string {
    if (this.modelConfig) {
      if (this.modelConfig.Version === 3) {
        // V3版本：检查可用的身体动作
        const motions = this.modelConfig.FileReferences?.Motions || {};
        if (motions.TapBody) return 'TapBody';
        if (motions.Tapbody) return 'Tapbody';
        if (motions.Tap) return 'Tap';
        if (motions.tap) return 'tap';
        return 'Tap'; // 默认使用Tap
      } else {
        // V2版本：检查可用的身体动作
        const motions = this.modelConfig.motions || {};
        if (motions.tap_body) return 'tap_body';
        if (motions.tap) return 'tap';
        if (motions.body) return 'body';
        return 'tap_body'; // 默认使用tap_body
      }
    }

    // 如果没有配置，使用版本推测
    const selectedModel = this.modelManager.getDefaultModel();
    if (selectedModel && selectedModel.version === 'v3') {
      return 'Tap';
    } else {
      return 'tap_body';
    }
  }

  // 获取默认动作键名（根据模型配置）
  private getDefaultMotionKey(): string {
    return this.getBodyMotionKey(); // 默认使用身体动作
  }

  // 播放触摸动作
  private playTouchMotion(motionGroup: string): void {
    if (!this.model || !this.model.internalModel) return;

    try {
      console.log('播放触摸动作:', motionGroup);

      // 获取动作管理器
      const motionManager = this.model.internalModel.motionManager;
      if (motionManager) {
        // 随机选择该组中的一个动作索引
        const motionIndex = Math.floor(Math.random() * 3); // 假设每组最多有3个动作

        // 播放动作
        motionManager.startMotion(motionGroup, motionIndex);
        console.log(`播放动作: ${motionGroup}[${motionIndex}]`);
      }

      // 播放音效（如果有）
      this.playTouchSound(motionGroup);

    } catch (error) {
      console.warn('播放触摸动作失败:', error);
      // 如果播放失败，尝试播放默认动作
      this.playDefaultMotion();
    }
  }

  // 播放默认动作
  private playDefaultMotion(): void {
    try {
      if (this.model && this.model.internalModel && this.model.internalModel.motionManager) {
        this.model.internalModel.motionManager.startMotion('tap_body', 0);
        console.log('播放默认触摸动作');
      }
    } catch (error) {
      console.warn('播放默认动作失败:', error);
    }
  }

  // 播放触摸音效
  private playTouchSound(motionGroup: string): void {
    try {
      // 这里可以根据动作类型播放相应的音效
      // 暂时只记录日志
      console.log('触摸音效:', motionGroup);

      // 未来可以扩展音效播放功能
      // 例如：播放模型目录下的sounds文件夹中的音频文件
    } catch (error) {
      console.warn('播放触摸音效失败:', error);
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
