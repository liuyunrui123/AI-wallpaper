# Python版本壁纸挂载工具

这是一个Python实现的壁纸挂载工具，用于替代C#版本的`WallpaperHosterLively.exe`。

## 功能特点

- **无需.NET依赖**：使用Python ctypes库调用Windows API，无需安装.NET Framework
- **功能完整**：实现与C#版本相同的壁纸挂载功能
- **跨平台潜力**：虽然当前只支持Windows，但为未来扩展留下空间
- **易于维护**：Python代码更易读和维护

## 技术实现

### 核心原理
1. 通过Windows API找到桌面的`Progman`窗口
2. 向`Progman`发送特殊消息创建新的`WorkerW`窗口
3. 将Electron窗口设置为`WorkerW`的子窗口
4. 调整窗口位置和大小以覆盖整个桌面

### 主要API调用
- `FindWindow` - 查找窗口
- `SendMessageTimeout` - 发送消息创建WorkerW
- `EnumWindows` - 枚举窗口查找目标WorkerW
- `SetParent` - 设置父子窗口关系
- `SetWindowPos` - 调整窗口位置和大小

## 使用方法

### 命令行使用
```bash
python wallpaper_hoster.py <hwnd> [x] [y] [width] [height]
```

参数说明：
- `hwnd`: Electron窗口句柄（十进制）
- `x, y`: 窗口位置（可选，默认0,0）
- `width, height`: 窗口大小（可选，默认全屏）

### 示例
```bash
# 基本用法（全屏壁纸）
python wallpaper_hoster.py 123456

# 指定位置和大小
python wallpaper_hoster.py 123456 100 200 800 600
```

## 构建和测试

### 运行测试
```bash
python test_wallpaper_hoster.py
```

### 一键构建测试
```bash
build.bat
```

## 与C#版本的对比

| 特性 | C#版本 | Python版本 |
|------|--------|------------|
| 依赖 | .NET 9.0 | Python 3.x |
| 文件大小 | ~10MB | ~10KB |
| 启动速度 | 快 | 中等 |
| 维护性 | 中等 | 高 |
| 跨平台 | Windows only | 潜在支持 |

## 集成到Electron

要在Electron项目中使用Python版本，需要修改`main.js`中的调用逻辑：

```javascript
// 替换原来的C#调用
const pythonScript = path.join(process.resourcesPath, 'wallpaper_hoster', 'python', 'wallpaper_hoster.py');
execFile('python', [pythonScript, hwnd], callback);
```

## 注意事项

1. **Python环境**：需要系统安装Python 3.x并添加到PATH
2. **权限要求**：某些情况下可能需要管理员权限
3. **兼容性**：仅支持Windows系统
4. **性能**：首次启动可能比C#版本稍慢

## 故障排除

### 常见问题

1. **找不到Python**
   - 确保Python已安装并添加到系统PATH
   - 尝试使用完整路径调用Python

2. **WorkerW创建失败**
   - 尝试以管理员权限运行
   - 检查Windows版本兼容性

3. **SetParent失败**
   - 确认窗口句柄有效
   - 检查目标窗口是否存在

### 调试模式
脚本包含详细的日志输出，可以帮助诊断问题：
```bash
python wallpaper_hoster.py 123456 2>&1 | findstr "INFO ERROR"
```
