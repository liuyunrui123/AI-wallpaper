const { contextBridge, ipcRenderer, app } = require('electron');
const pkg = require('../package.json');
const path = require('path');

contextBridge.exposeInMainWorld('api', {
    getWeather: (location) => ipcRenderer.invoke('get-weather', location),
    analyzeTime: (timeData) => ipcRenderer.invoke('analyze-time', timeData),
    generateImage: (prompt) => ipcRenderer.invoke('generate-image', prompt)
});

// 同步获取配置信息
const appConfig = ipcRenderer.sendSync('get-app-config-sync');

contextBridge.exposeInMainWorld('electronAPI', {
    isWallpaperMode: appConfig?.wallpaperMode === '1',
    version: pkg.version,
    port: String(appConfig?.apiPort || 9000),
    host: String(appConfig?.apiHost || 'localhost'),
    exitWallpaper: () => ipcRenderer.send('exit-wallpaper'),
    restartApp: () => ipcRenderer.send('restart-app'),
    enableLive2D: Boolean(appConfig?.enableLive2D), // 直接同步注入
    getResourcePath: (relativePath) => {
        // 获取资源目录路径
        const resourcesPath = process.resourcesPath || path.join(__dirname, '../resources');
        return path.join(resourcesPath, relativePath).replace(/\\/g, '/');
    },
    readLive2DConfig: () => ipcRenderer.invoke('read-live2d-config'),
    closeWindow: () => ipcRenderer.send('close-current-window'),
    getAppConfig: () => ipcRenderer.invoke('get-app-config'),
    saveAppConfig: (config) => ipcRenderer.invoke('save-app-config', config)
});

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => ipcRenderer.send(channel, data),
        on: (channel, func) => ipcRenderer.on(channel, func)
    }
});