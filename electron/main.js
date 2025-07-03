const { app, BrowserWindow, ipcMain, globalShortcut, Tray, Menu, protocol } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const pkg = require('../package.json');
const { logToAll } = require('./log');

// 强制切换 cwd，保证双击和命令行启动一致
process.chdir(process.resourcesPath);

// 配置管理模块
class ConfigManager {
    constructor() {
        this.configPath = path.join(process.resourcesPath, 'wallpaper_config.json');
        this.defaultConfig = {
            wallpaperMode: '0',
            enableLive2D: false,
            apiPort: 9000,
            apiHost: 'localhost',
            desktopHwnd: 0,
            selectedModel: 'Senko_Normals',
            mouseTracking: true,
            disableAutoAnimations: true,
            autoLocation: true,
            manualLocation: {
                province: '',
                city: '',
                county: ''
            }
        };
    }

    // 读取配置文件
    readConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                const configData = fs.readFileSync(this.configPath, 'utf-8');
                const config = JSON.parse(configData);
                // 合并默认配置和读取的配置
                return { ...this.defaultConfig, ...config };
            } else {
                console.log('配置文件不存在，使用默认配置');
                return { ...this.defaultConfig };
            }
        } catch (error) {
            console.error('读取配置文件失败:', error);
            return { ...this.defaultConfig };
        }
    }

    // 保存配置文件
    saveConfig(config) {
        try {
            const configData = { ...this.defaultConfig, ...config };
            fs.writeFileSync(this.configPath, JSON.stringify(configData, null, 2), 'utf-8');
            console.log('配置文件保存成功:', configData);

            // 保存Live2D相关配置
            this.saveLive2DConfig(configData);

            // 更新环境变量
            this.setEnvironmentVariables(configData);

            return { success: true, message: '配置保存成功', config: configData };
        } catch (error) {
            console.error('保存配置文件失败:', error);
            return { success: false, message: '配置保存失败: ' + error.message };
        }
    }

    // 保存Live2D配置
    saveLive2DConfig(config) {
        if (config.selectedModel || config.mouseTracking !== undefined || config.disableAutoAnimations !== undefined) {
            try {
                const live2dConfigPath = path.join(process.resourcesPath, 'static', 'live2d', 'models.json');
                if (fs.existsSync(live2dConfigPath)) {
                    const live2dConfigData = JSON.parse(fs.readFileSync(live2dConfigPath, 'utf-8'));

                    // 更新默认模型
                    if (config.selectedModel) {
                        live2dConfigData.default = config.selectedModel;
                    }

                    // 更新Live2D设置
                    if (!live2dConfigData.settings) {
                        live2dConfigData.settings = {};
                    }

                    if (config.mouseTracking !== undefined) {
                        live2dConfigData.settings.enableMouseTracking = config.mouseTracking;
                    }

                    if (config.disableAutoAnimations !== undefined) {
                        live2dConfigData.settings.disableAutoAnimations = config.disableAutoAnimations;
                    }

                    fs.writeFileSync(live2dConfigPath, JSON.stringify(live2dConfigData, null, 2), 'utf-8');
                    console.log('Live2D配置保存成功:', live2dConfigData);
                }
            } catch (live2dError) {
                console.error('保存Live2D配置失败:', live2dError);
            }
        }
    }

    // 设置环境变量
    setEnvironmentVariables(config) {
        if (config.wallpaperMode) {
            process.env.WALLPAPER_MODE = config.wallpaperMode;
        }
        if (config.apiPort) {
            process.env.FLASK_API_PORT = String(config.apiPort);
        }
        if (config.apiHost) {
            process.env.FLASK_API_HOST = String(config.apiHost);
        }
        if (config.enableLive2D !== undefined) {
            process.env.ENABLE_LIVE2D = config.enableLive2D ? '1' : '0';
        }
    }
}

// 创建配置管理器实例
const configManager = new ConfigManager();

// 读取配置并设置环境变量
const appConfig = configManager.readConfig();
configManager.setEnvironmentVariables(appConfig);

// 从配置中获取需要的变量
let desktopHwnd = Number(appConfig.desktopHwnd) || 0;
let enableLive2D = appConfig.enableLive2D || false;

let flaskProcess = null;
let mainWindow = null;
let settingsWindow = null;
let tray = null;

// 多屏壁纸窗口管理
const { screen } = require('electron');
let wallpaperWindows = {};

function stopFlaskSync(callback) {
    if (flaskProcess) {
        if (process.platform === 'win32') {
            exec(`taskkill /PID ${flaskProcess.pid} /T /F`, (err) => {
                if (err) {
                    console.error('taskkill failed:', err);
                }
                flaskProcess = null;
                if (callback) callback();
            });
        } else {
            flaskProcess.kill('SIGKILL');
            flaskProcess = null;
            if (callback) callback();
        }
    } else {
        if (callback) callback();
    }
}

function safeQuit() {
    stopFlaskSync(() => {
        app.quit();
    });
}

function restartApp() {
    console.log('重启应用程序...');
    logToAll('用户请求重启应用程序', 'INFO', 'electron');

    stopFlaskSync(() => {
        // 重启应用
        app.relaunch();
        app.exit(0);
    });
}

function refreshWallpaper() {
    // 通知所有窗口刷新壁纸
    BrowserWindow.getAllWindows().forEach(window => {
        window.webContents.send('refresh-wallpaper');
    });
    console.log('已发送刷新壁纸请求到所有窗口');
    logToAll('用户请求刷新壁纸', 'INFO', 'electron');
}

function openSettingsWindow() {
    // 如果设置窗口已经存在，则聚焦到该窗口
    if (settingsWindow) {
        settingsWindow.focus();
        return;
    }

    // 创建设置窗口
    settingsWindow = new BrowserWindow({
        width: 900,
        height: 700,
        title: 'AI Wallpaper 设置',
        icon: path.join(__dirname, '../public/icon.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        // 设置窗口的菜单栏
        autoHideMenuBar: true,
        resizable: true,
        minimizable: true,
        maximizable: true,
        closable: true
    });

    // 加载设置页面
    if (process.env.NODE_ENV === 'development') {
        settingsWindow.loadURL('http://localhost:8080/#/settings');
    } else {
        settingsWindow.loadFile(path.join(__dirname, '../dist/index.html'), {
            hash: 'settings'
        });
    }

    // 窗口关闭时清理引用
    settingsWindow.on('closed', () => {
        settingsWindow = null;
    });

    console.log('设置窗口已打开');
    logToAll('用户打开设置窗口', 'INFO', 'electron');
}

function startFlask() {
    const backendExe = path.join(process.resourcesPath, 'backend', 'app.exe');
    if (!fs.existsSync(backendExe)) {
        logToAll('backend flask exe not found: ' + backendExe, 'ERROR', 'electron');
        console.error('backend flask exe not found:', backendExe);
        return;
    }
    // 端口号优先级：环境变量 > 默认9000
    const port = process.env.FLASK_API_PORT || 9000;
    logToAll('start flask exe: ' + backendExe + ' --port ' + port, 'INFO', 'electron');
    // 合并并补全关键环境变量
    const env = Object.assign({}, process.env, {
        SystemRoot: process.env.SystemRoot || 'C:\\Windows',
        Path: process.env.Path || process.env.PATH || '',
        TEMP: process.env.TEMP || process.env.TMP || 'C:\\Windows\\Temp',
    });
    flaskProcess = spawn(backendExe, ['--port', String(port)], {
        cwd: path.join(process.resourcesPath, 'backend'),
        stdio: ['ignore', 'pipe', 'pipe'],
        env
    });
    flaskProcess.stdout.on('data', data => {
        const out = Buffer.from(data).toString('utf8');
        logToAll(out.trim(), 'INFO', 'backend');
        console.log('[flask]', out);
    });
    flaskProcess.stderr.on('data', data => {
        const out = Buffer.from(data).toString('utf8');
        logToAll(out.trim(), 'ERROR', 'backend');
        console.error('[flask-err]', out);
    });
    flaskProcess.on('error', (err) => {
        logToAll('Failed to start Flask backend: ' + err, 'ERROR', 'electron');
        console.error('Failed to start Flask backend:', err);
    });
    flaskProcess.on('exit', (code, signal) => {
        logToAll(`Flask backend exited: ${code} ${signal}`, 'ERROR', 'backend');
        console.error('Flask backend exited:', code, signal);
    });
}

function getNativeHWND(win) {
    // Electron 15+ 可用 win.getNativeWindowHandle()
    const buf = win.getNativeWindowHandle();
    if (process.arch === 'x64') {
        return buf.readBigInt64LE(0).toString();
    } else {
        return buf.readInt32LE(0).toString();
    }
}

function setAsWallpaper(win) {
    const hwnd = getNativeHWND(win);
    const exePath = path.join(process.resourcesPath, 'wallpaper_hoster', 'WallpaperHosterLively', 'out', 'WallpaperHosterLively.exe');
    logToAll(`setAsWallpaper: hwnd=${hwnd}, exePath=${exePath}`, 'INFO', 'electron');
    console.log('set window as wallpaper, hwnd:', hwnd, 'hwnd_hex:', '0x' + hwnd.toString(16), 'exe:', exePath);
    if (!fs.existsSync(exePath)) {
        logToAll('wallpaper host lively not found: ' + exePath, 'ERROR', 'electron');
        console.error('wallpaper host lively not fount:', exePath);
        if (mainWindow && mainWindow.webContents) {
            mainWindow.webContents.send('show-error', '壁纸挂载失败：未找到挂载工具！');
        }
        return;
    }
    const { execFile } = require('child_process');
    execFile(exePath, [hwnd], { encoding: 'utf8' }, (err, stdout, stderr) => {
        if (err) {
            logToAll('壁纸挂载失败: ' + err, 'ERROR', 'electron');
            console.error('壁纸挂载失败:', err);
            if (mainWindow && mainWindow.webContents) {
                mainWindow.webContents.send('show-error', '壁纸挂载失败: ' + err.message);
            }
        }
        if (stdout) {
            logToAll('WallpaperHosterLively 输出: ' + stdout, 'INFO', 'electron');
            console.log('WallpaperHosterLively 输出:', stdout);
        }
        if (stderr) {
            logToAll('WallpaperHosterLively 错误: ' + stderr, 'ERROR', 'electron');
            console.error('WallpaperHosterLively 错误:', stderr);
        }
    });
}

// 多屏壁纸窗口管理
function setAsWallpaperMulti(win, display) {
    const hwnd = getNativeHWND(win);
    const exePath = path.join(process.resourcesPath, 'wallpaper_hoster', 'WallpaperHosterLively', 'out', 'WallpaperHosterLively.exe');
    if (!fs.existsSync(exePath)) {
        logToAll('wallpaper host lively not found: ' + exePath, 'ERROR', 'electron');
        return;
    }
    const { x, y, width, height } = display.bounds;
    spawn(exePath, [hwnd, x, y, width, height], { detached: true, stdio: 'ignore' });
}

function createWallpaperWindow(display) {
    const win = new BrowserWindow({
        x: display.bounds.x,
        y: display.bounds.y,
        width: display.bounds.width,
        height: display.bounds.height,
        frame: false,
        transparent: true,
        skipTaskbar: true,
        show: false,
        resizable: false,
        movable: false,
        focusable: false,
        alwaysOnTop: false,
        hasShadow: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            enableRemoteModule: false,
        }
    });
    if (process.env.NODE_ENV === 'development') {
        win.loadURL('http://localhost:8080');
    } else {
        win.loadFile('dist/index.html').catch(err => {
            console.error('load index.html faild:', err);
        });
    }
    win.once('ready-to-show', () => {
        win.showInactive();
        setTimeout(() => {
            setAsWallpaperMulti(win, display);
            win.maximize();
            win.setIgnoreMouseEvents(true, { forward: true });
            win.setAlwaysOnTop(false);
            win.setFocusable(false);
        }, 50);
    });
    win.on('closed', () => {
        Object.keys(wallpaperWindows).forEach(id => {
            if (wallpaperWindows[id] === win) delete wallpaperWindows[id];
        });
    });
    return win;
}

function setupAllWallpapers() {
    Object.values(wallpaperWindows).forEach(win => {
        if (!win.isDestroyed()) win.close();
    });
    wallpaperWindows = {};
    screen.getAllDisplays().forEach(display => {
        wallpaperWindows[display.id] = createWallpaperWindow(display);
    });
}

function createWindow() {
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show();
        return mainWindow;
    }
    const { screen } = require('electron');
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;
    const isWallpaperMode = process.env.WALLPAPER_MODE === '1';
    console.log('windows size:', width, 'x', height, 'wallpaper_mode:', isWallpaperMode);
    mainWindow = new BrowserWindow({
        width,
        height,
        frame: !isWallpaperMode,
        transparent: isWallpaperMode,
        skipTaskbar: isWallpaperMode,
        show: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            enableRemoteModule: false,
        },
    });
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:8080');
    } else {
        mainWindow.loadFile('dist/index.html').catch(err => {
            console.error('load index.html faild:', err);
        });
    }
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        // if (process.env.NODE_ENV === 'development') {
        //     //最小化窗口
        //     mainWindow.minimize();
        // }
        if (isWallpaperMode) {
            setTimeout(() => {
                setAsWallpaper(mainWindow);
                // 挂载后设置为点击穿透、不可聚焦、非置顶
                mainWindow.maximize();
                mainWindow.setIgnoreMouseEvents(true, { forward: true });
                mainWindow.setAlwaysOnTop(false);
                mainWindow.setFocusable(false);
            }, 50); // 延迟确保窗口已显示
        }
    });
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
    return mainWindow;
}

function createTray() {
    if (tray) return;
    const isDev = process.env.NODE_ENV === 'development' || process.defaultApp || /node_modules[\\/]electron[\\/]/.test(process.execPath);
    let iconPath;
    if (isDev) {
        iconPath = path.join(__dirname, '../src/assets/icon.ico');
    } else {
        iconPath = path.join(process.resourcesPath, 'icon.ico');
    }
    try {
        tray = new Tray(iconPath);
        const contextMenu = Menu.buildFromTemplate([
            { label: '🔄 刷新壁纸', click: () => { refreshWallpaper(); } },
            { type: 'separator' },
            { label: '⚙️ 设置', click: () => { openSettingsWindow(); } },
            { type: 'separator' },
            { label: '🔄 重启程序', click: () => { restartApp(); } },
            { type: 'separator' },
            { label: '❌ 退出壁纸', click: () => { safeQuit(); } }
        ]);
        tray.setToolTip('AI Wallpaper');
        tray.setContextMenu(contextMenu);
    } catch (e) {
        console.error('托盘图标加载失败:', iconPath, e);
    }
}

// 只允许主实例运行，防止多开
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    safeQuit();
} else {
    app.whenReady().then(() => {
        // 注册自定义协议来处理资源文件
        protocol.registerFileProtocol('app-resource', (request, callback) => {
            const url = request.url.replace('app-resource://', '');
            const filePath = path.join(process.resourcesPath, url);
            callback({ path: filePath });
        });

        startFlask();
        if (process.env.WALLPAPER_MODE === '1') {
            setupAllWallpapers();
            screen.on('display-added', setupAllWallpapers);
            screen.on('display-removed', setupAllWallpapers);
            screen.on('display-metrics-changed', setupAllWallpapers);
            globalShortcut.register('Esc', () => {
                safeQuit();
            });
        } else {
            createWindow();
        }
        createTray();
        // 注入 enableLive2D 到渲染进程
        ipcMain.handle('get-enable-live2d', () => enableLive2D);

        // 读取Live2D配置文件
        ipcMain.handle('read-live2d-config', () => {
            try {
                const configPath = path.join(process.resourcesPath, 'static', 'live2d', 'models.json');
                if (fs.existsSync(configPath)) {
                    const configData = fs.readFileSync(configPath, 'utf-8');
                    return JSON.parse(configData);
                } else {
                    console.error('Live2D config file not found:', configPath);
                    return null;
                }
            } catch (error) {
                console.error('Failed to read Live2D config:', error);
                return null;
            }
        });

        // 读取应用配置文件
        ipcMain.handle('get-app-config', () => {
            try {
                return configManager.readConfig();
            } catch (error) {
                console.error('Failed to read app config:', error);
                return null;
            }
        });

        // 保存应用配置文件
        ipcMain.handle('save-app-config', (event, config) => {
            try {
                const result = configManager.saveConfig(config);

                if (result.success) {
                    logToAll('应用配置已保存', 'INFO', 'electron');

                    // 通知所有窗口配置已更新
                    BrowserWindow.getAllWindows().forEach(window => {
                        window.webContents.send('config-updated', result.config);
                    });
                }

                return result;
            } catch (error) {
                console.error('Failed to save app config:', error);
                logToAll('保存应用配置失败: ' + error.message, 'ERROR', 'electron');
                return { success: false, message: '配置保存失败: ' + error.message };
            }
        });
    });
    app.on('will-quit', () => {
        globalShortcut.unregisterAll();
    });
    app.on('window-all-closed', () => {
        safeQuit();
        // 如果是macOS可以保留app.quit()，但safeQuit已包含app.quit()
    });
    app.on('before-quit', () => {
        stopFlaskSync();
    });
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
}

// 支持前端通过IPC退出
ipcMain.on('exit-wallpaper', () => {
    safeQuit();
});

// 支持前端通过IPC重启
ipcMain.on('restart-app', () => {
    restartApp();
});

// 支持前端通过IPC关闭当前窗口
ipcMain.on('close-current-window', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender);
    if (window) {
        window.close();
    }
});

// 前端日志聚合（前端通过IPC发送日志）
ipcMain.on('frontend-log', (event, { level = 'INFO', msg = '' }) => {
    logToAll(msg, level, 'frontend');
});

// 主进程自身日志聚合示例
console.log('AI Wallpaper App 主进程启动, Version:', pkg.version);
logToAll(`AI Wallpaper App 主进程启动, Version: ${pkg.version}`, 'INFO', 'electron');

process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
    // 可选：写入日志文件
    logToAll(`Uncaught Exception: ${err.message}`, 'ERROR', 'electron');
});
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection:', reason);
    // 可选：写入日志文件
    logToAll(`Unhandled Rejection: ${reason}`, 'ERROR', 'electron');
});