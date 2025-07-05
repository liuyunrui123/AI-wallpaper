# 壁纸挂载工具切换指南

本项目提供了两种壁纸挂载实现方式，你可以根据需要在它们之间切换。

## 当前状态

**当前使用：Python版本**
- 位置：`wallpaper_hoster/python/wallpaper_hoster.py`
- 优势：无需.NET依赖，文件体积小

## 两种实现对比

| 特性 | Python版本 | C#版本 |
|------|------------|--------|
| 依赖 | Python 3.x | .NET 9.0 |
| 文件大小 | ~10KB | ~10MB |
| 启动速度 | 中等 | 快 |
| 维护性 | 高 | 中等 |
| 部署复杂度 | 低 | 中等 |

## 如何切换到C#版本

### 1. 修改 `electron/main.js`

在 `setAsWallpaper` 函数中：

```javascript
function setAsWallpaper(win) {
    const hwnd = getNativeHWND(win);
    
    // ===== 取消注释C#版本接口 =====
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
        // ... 错误处理代码
    });
    
    // ===== 注释掉Python版本接口 =====
    // const pythonScript = path.join(process.resourcesPath, 'wallpaper_hoster', 'python', 'wallpaper_hoster.py');
    // ... Python调用代码
}
```

在 `setAsWallpaperMulti` 函数中做类似修改。

### 2. 修改 `package.json`

更新构建配置，确保C#编译产物被包含：

```json
{
  "from": "wallpaper_hoster/WallpaperHosterLively/out",
  "to": "wallpaper_hoster/WallpaperHosterLively/out",
  "filter": ["!*.pdb"]
}
```

### 3. 编译C#工具

```bash
cd wallpaper_hoster
./build.bat
```

## 如何切换回Python版本

### 1. 修改 `electron/main.js`

注释掉C#版本代码，取消注释Python版本代码（恢复当前状态）。

### 2. 确保Python脚本存在

```bash
cd wallpaper_hoster/python
python test_wallpaper_hoster.py
```

## 混合使用（高级）

你也可以通过配置文件动态选择使用哪种实现：

1. 在 `wallpaper_config.json` 中添加配置项：
```json
{
  "wallpaperHosterType": "python"  // 或 "csharp"
}
```

2. 在 `main.js` 中读取配置并选择对应实现。

## 故障排除

### Python版本问题
- 确保系统安装了Python 3.x
- 确保Python添加到系统PATH
- 运行测试：`python wallpaper_hoster/python/test_wallpaper_hoster.py`

### C#版本问题
- 确保安装了.NET 9.0 SDK
- 重新编译：`cd wallpaper_hoster && ./build.bat`
- 检查编译产物：`wallpaper_hoster/WallpaperHosterLively/out/WallpaperHosterLively.exe`

### 权限问题
- 某些情况下可能需要管理员权限运行
- 检查Windows版本兼容性

## 推荐使用

**推荐使用Python版本**，因为：
1. 无需额外的.NET依赖
2. 部署更简单
3. 代码更易维护
4. 文件体积更小

除非你有特殊的性能要求或已经有.NET环境，否则建议使用Python版本。
