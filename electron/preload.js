const { contextBridge, ipcRenderer } = require('electron');
const pkg = require('../package.json');

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
    enableLive2D: undefined
});

// 获取 enableLive2D 配置
ipcRenderer.invoke('get-enable-live2d').then(val => {
    window.electronAPI.enableLive2D = val;
});

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => ipcRenderer.send(channel, data),
        on: (channel, func) => ipcRenderer.on(channel, func)
    }
});