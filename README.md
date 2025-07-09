# Wallpaper App

## 项目简介
这是一个基于Electron和Vue.js的壁纸软件项目，集成了Python后端的天气API和时间分析功能，同时提供AI生图服务。

## 技术栈
- **前端**: Vue.js, Electron
- **后端**: Python, Flask
- **AI服务**: 在线生图API


## 功能
- [x] 显示壁纸
- [x] 显示实时天气信息
- [x] 根据时间天气信息生成并刷新对应的壁纸
- [x] Live2D虚拟角色
- [x] 独立的设置菜单窗口
- [x] 手动刷新壁纸按钮
- [X] 显示时间
- [ ] 开机自启功能
- [ ] 基于LLM分析当前信息自动生成绘图提示词
- [ ] 动态特效
- [ ] 被其他应用全屏覆盖时暂停壁纸高负载活动


## 项目结构
```
AI_Wallpaper
├── electron
│   ├── main.js              # Electron主进程入口，负责窗口、托盘、后端进程管理等
│   ├── preload.js           # 渲染进程预加载脚本，暴露API给前端
│   ├── log.js               # 日志
│   └──wallpaper_config.json# 运行时配置（端口、模式等）
├── src
│   ├── App.vue              # Vue根组件
│   ├── main.ts              # Vue入口
│   ├── components/
│   │   └── WallpaperDisplay.vue
│   ├── views/
│   │   └── Home.vue         # 主页面，壁纸展示与交互
│   ├── assets/              # 前端静态资源
│   └── global.d.ts          # 前端全局类型声明
├── backend
│   ├── app.py               # Python后端主入口
│   ├── build_backend_exe.bat# 后端一键打包脚本
│   ├── requirements.txt     # Python依赖
│   ├── static/
│   │   └── wallpapers/      # 壁纸图片缓存
│   ├── ai_image/            # 壁纸生成
│   └── weather/             # 天气API
├── wallpaper_hoster/        # 壁纸挂载工具（C#和Python两种实现）
├── package.json             # 前端依赖与构建配置
├── tsconfig.json            # TypeScript配置
└── README.md                # 项目说明
```

## 安装与运行
~~运行需要的依赖：~~
~~安装 .NET 9.0: [Download the .NET runtime](https://aka.ms/dotnet-core-applaunch?missing_runtime=true&arch=x64&rid=win-x64&os=win10&apphost_version=9.0.6)~~

从发布页面下载[release](https://github.com/liuyunrui123/AI_Wallpaper/releases)版本, 启动后会在托盘栏显示一个图标，右键可以退出。

## 配置
- 主配置文件位于`resources\wallpaper_config.json`
- live2d的模型配置位于`resources\static\live2d\models.json`

## 从源码编译
1. 克隆项目到本地:
   ```
   git clone <repository-url>
   cd AI_Wallpaper
   ```

2. 安装前端依赖:
   ```
   npm install --legacy-peer-deps
   ```

3. 安装后端依赖:
   ```shell
   cd backend/
   # 创建虚拟环境
   uv venv --python 3.10
   # 激活虚拟环境
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

4. 一键打包后端为可执行文件（Windows）:
   ```
   cd backend
   build_backend_exe.bat
   ```
   > 运行后会在 backend 目录下生成 app.exe，无需本地 Python 环境即可被 Electron 自动启动。

5. 准备壁纸挂载工具

   **方式一：使用Python版本（推荐，无需.NET依赖）**
   ```
   cd wallpaper_hoster/python
   ./build.bat
   ```

   **方式二：使用C#版本（需要.NET 9.0）**
   ```
   cd wallpaper_hoster
   ./build.bat
   ```

6. 启动后端服务（开发调试用）:
   ```
   python backend/app.py
   ```

7. 启动前端应用:
   ```
   npm run serve
   ```

8. 调试模式
   ```
   npm run build
   npm run electron:serve
   ```

9. 编译打包electron主程序
   ```
   npm run electron:build
   ```
   注意：`npm run electron:build`需要管理员身份运行，否则报错。

### 动态壁纸桌面挂载工具
本项目支持将 Electron 窗口嵌入到 Windows 桌面壁纸层，实现动态壁纸效果。项目提供了两种实现方式：

#### Python版本（推荐）
- **优势**：无需.NET依赖，文件体积小，易于维护
- **位置**：`wallpaper_hoster/python/wallpaper_hoster.py`
- **技术**：使用Python ctypes库调用Windows API
- **创建虚拟环境**
   ```
   uv venv --python 3.7
   # 激活虚拟环境
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```
- **构建**：
  ```bash
  cd wallpaper_hoster/python
  ./build.bat
  ```

#### C#版本（传统）
- **优势**：启动速度快，性能优秀
- **位置**：`wallpaper_hoster/WallpaperHosterLively/WallpaperHosterLively.cs`
- **技术**：使用.NET 9.0和P/Invoke调用Windows API
- **构建**：需要安装.NET 9.0 SDK
  ```bash
  cd wallpaper_hoster
  ./build.bat
  ```

#### Electron主进程集成
- **当前使用**：Python版本（默认）
- **切换方式**：修改`electron/main.js`中的注释即可切换实现
- **运行模式**：
  - 生产模式：自动调用挂载工具，将窗口嵌入桌面
  - 开发模式：普通窗口，无需挂载


## 贡献
欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证
本项目遵循MIT许可证。
