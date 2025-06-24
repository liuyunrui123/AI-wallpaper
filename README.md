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
- [ ] 开机自启功能
- [ ] 独立的菜单窗口
- [ ] 手动刷新壁纸按钮
- [ ] 基于LLM分析当前信息自动生成绘图提示词
- [ ] 动态特效
- [ ] Live2D虚拟角色


## 项目结构
```
AI_Wallpaper
├── electron
│   ├── main.js              # Electron主进程入口，负责窗口、托盘、后端进程管理等
│   ├── preload.js           # 渲染进程预加载脚本，暴露API给前端
│   ├── log.js               # 日志
│   ├── wallpaper_config.json# 运行时配置（端口、模式等）
│   └── wallpaper_hoster/    # C#壁纸挂载工具源码及编译产物
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
├── package.json             # 前端依赖与构建配置
├── tsconfig.json            # TypeScript配置
└── README.md                # 项目说明
```

## 安装与运行
运行需要的依赖：
安装 .NET 9.0: [Download the .NET runtime](https://aka.ms/dotnet-core-applaunch?missing_runtime=true&arch=x64&rid=win-x64&os=win10&apphost_version=9.0.6)

从发布页面下载[release](https://github.com/liuyunrui123/AI_Wallpaper/releases)版本, 启动后会在托盘栏显示一个图标，右键可以退出。

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

5. 编译C#工具
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

### 动态壁纸桌面挂载工具（C#）
本项目支持将 Electron 窗口嵌入到 Windows 桌面壁纸层，实现动态壁纸效果。实现方式为：Electron 主进程调用 C# 小工具，将窗口句柄挂载到桌面 WorkerW 层。
挂载工具源码位置: `wallpaper_hoster/WallpaperHosterLively/WallpaperHosterLively.cs`
- 编译方法（.NET 9.0） 
   安装 .NET 9.0 SDK（如未安装）。
   打开命令行，执行以下命令：
   ```
   cd wallpaper_hoster
   ./build.bat
   ```
   编译完成后，WallpaperHosterLively.exe 位于 `WallpaperHosterLively/out/` 目录下。


- Electron主进程集成说明  
   生产模式下，Electron 主进程会自动调用该 exe，将窗口嵌入桌面。
   开发模式下为普通窗口，无需挂载。
   切换方式：设置环境变量 WALLPAPER_MODE=1 即可启用壁纸模式。


## 贡献
欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证
本项目遵循MIT许可证。