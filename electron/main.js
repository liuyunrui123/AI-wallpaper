const { app, BrowserWindow, ipcMain, globalShortcut, Tray, Menu } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const pkg = require('../package.json');
const { logToAll } = require('./log');

// 强制切换 cwd，保证双击和命令行启动一致
process.chdir(process.resourcesPath);

// 读取配置文件中的 DESKTOP_HWND
let desktopHwnd = 0;
// 读取wallpaper_config.json配置自动设置环境变量
const configPath = path.join(process.resourcesPath, 'wallpaper_config.json');
let enableLive2D = false;
if (fs.existsSync(configPath)) {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        if (config.WALLPAPER_MODE) {
            process.env.WALLPAPER_MODE = config.WALLPAPER_MODE;
        }
        if (config.DESKTOP_HWND && Number(config.DESKTOP_HWND) !== 0) {
            desktopHwnd = Number(config.DESKTOP_HWND);
        }
        // 允许配置 FLASK_API_PORT 和 FLASK_API_HOST
        if (config.FLASK_API_PORT) {
            process.env.FLASK_API_PORT = String(config.FLASK_API_PORT);
        }
        if (config.FLASK_API_HOST) {
            process.env.FLASK_API_HOST = String(config.FLASK_API_HOST);
        }
        if (typeof config.ENABLE_LIVE2D !== 'undefined') {
            enableLive2D = !!config.ENABLE_LIVE2D;
        }
    } catch (e) {
        console.error('读取wallpaper_config.json失败:', e);
    }
}

let flaskProcess = null;
let mainWindow = null;
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
            { label: '退出壁纸', click: () => { safeQuit(); } }
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