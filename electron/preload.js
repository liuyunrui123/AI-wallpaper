const { contextBridge, ipcRenderer, app } = require('electron');
const pkg = require('../package.json');
const path = require('path');

contextBridge.exposeInMainWorld('api', {
    getWeather: (location) => ipcRenderer.invoke('get-weather', location),
    analyzeTime: (timeData) => ipcRenderer.invoke('analyze-time', timeData),
    generateImage: (prompt) => ipcRenderer.invoke('generate-image', prompt)
});

contextBridge.exposeInMainWorld('electronAPI', {
    isWallpaperMode: process.env.WALLPAPER_MODE === '1',
    version: pkg.version,
    port: process.env.FLASK_API_PORT || '9000',
    host: process.env.FLASK_API_HOST || 'localhost',
    exitWallpaper: () => ipcRenderer.send('exit-wallpaper'),
    restartApp: () => ipcRenderer.send('restart-app'),
    enableLive2D: process.env.ENABLE_LIVE2D === '1', // 直接同步注入
    getResourcePath: (relativePath) => {
        // 获取资源目录路径
        const resourcesPath = process.resourcesPath || path.join(__dirname, '../resources');
        return path.join(resourcesPath, relativePath).replace(/\\/g, '/');
    },
    readLive2DConfig: () => ipcRenderer.invoke('read-live2d-config')
});

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => ipcRenderer.send(channel, data),
        on: (channel, func) => ipcRenderer.on(channel, func)
    }
});