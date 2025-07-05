#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python版本的壁纸挂载工具
替代C# WallpaperHosterLively.exe的Python实现
使用ctypes调用Windows API实现将Electron窗口挂载到桌面壁纸层
"""

import sys
import ctypes
from ctypes import wintypes, byref, c_char_p, c_int, c_uint, c_void_p, POINTER
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Windows API常量
SW_SHOW = 5
SWP_NOZORDER = 0x0010
GW_HWNDNEXT = 2
SMTO_ABORTIFHUNG = 0x0002

# Windows API函数声明
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 定义RECT结构体
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", c_int),
        ("top", c_int), 
        ("right", c_int),
        ("bottom", c_int)
    ]

# 定义回调函数类型
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# Windows API函数
FindWindow = user32.FindWindowW
FindWindow.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindow.restype = wintypes.HWND

FindWindowEx = user32.FindWindowExW
FindWindowEx.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowEx.restype = wintypes.HWND

SetParent = user32.SetParent
SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
SetParent.restype = wintypes.HWND

ShowWindow = user32.ShowWindow
ShowWindow.argtypes = [wintypes.HWND, c_int]
ShowWindow.restype = wintypes.BOOL

EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
EnumWindows.restype = wintypes.BOOL

SendMessageTimeout = user32.SendMessageTimeoutW
SendMessageTimeout.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM, wintypes.UINT, wintypes.UINT, POINTER(wintypes.DWORD)]
SendMessageTimeout.restype = wintypes.LONG

GetClassName = user32.GetClassNameW
GetClassName.argtypes = [wintypes.HWND, wintypes.LPWSTR, c_int]
GetClassName.restype = c_int

GetWindow = user32.GetWindow
GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
GetWindow.restype = wintypes.HWND

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, POINTER(RECT)]
GetWindowRect.restype = wintypes.BOOL

SetWindowPos = user32.SetWindowPos
SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, c_int, c_int, c_int, c_int, wintypes.UINT]
SetWindowPos.restype = wintypes.BOOL


def create_worker_w():
    """
    创建WorkerW窗口，用于挂载壁纸
    这是核心功能，等价于C#版本的CreateWorkerW方法
    """
    # 1. 找到Progman窗口
    progman = FindWindow("Progman", None)
    if not progman:
        logger.error("未找到Progman窗口")
        return None
    
    logger.info(f"找到Progman窗口: 0x{progman:X}")
    
    # 2. 向Progman发送消息，促使系统创建新的WorkerW
    result = wintypes.DWORD()
    ret = SendMessageTimeout(progman, 0x052C, 0xD, 0x1, SMTO_ABORTIFHUNG, 1000, byref(result))
    if not ret:
        logger.error("发送消息到Progman失败")
        return None
    
    logger.info("已向Progman发送消息，开始查找WorkerW")
    
    # 3. 枚举所有窗口，找到带有SHELLDLL_DefView的WorkerW，再取其下一个WorkerW
    worker_w = None
    
    def enum_windows_callback(hwnd, lparam):
        nonlocal worker_w
        
        # 获取窗口类名
        class_name = ctypes.create_unicode_buffer(256)
        GetClassName(hwnd, class_name, 256)
        
        if class_name.value == "WorkerW":
            # 查找是否有SHELLDLL_DefView子窗口
            shell_view = FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
            if shell_view:
                logger.info(f"找到带有SHELLDLL_DefView的WorkerW: 0x{hwnd:X}")
                # 找到带有SHELLDLL_DefView的WorkerW，取其下一个WorkerW
                next_worker = GetWindow(hwnd, GW_HWNDNEXT)
                if next_worker:
                    # 验证下一个窗口也是WorkerW
                    next_class_name = ctypes.create_unicode_buffer(256)
                    GetClassName(next_worker, next_class_name, 256)
                    if next_class_name.value == "WorkerW":
                        worker_w = next_worker
                        logger.info(f"找到目标WorkerW: 0x{worker_w:X}")
                        return False  # 停止枚举
        
        return True  # 继续枚举
    
    # 执行窗口枚举
    callback = EnumWindowsProc(enum_windows_callback)
    EnumWindows(callback, 0)
    
    # 4. 兜底：如果没找到，直接用FindWindowEx查找WorkerW
    if not worker_w:
        logger.warning("通过枚举未找到WorkerW，尝试直接查找")
        worker_w = FindWindowEx(progman, None, "WorkerW", None)
        if worker_w:
            logger.info(f"通过直接查找找到WorkerW: 0x{worker_w:X}")
    
    if not worker_w:
        logger.error("未能找到WorkerW窗口")
        return None
    
    return worker_w


def set_as_wallpaper(hwnd, x=0, y=0, width=0, height=0):
    """
    将指定窗口设置为壁纸
    
    Args:
        hwnd: 窗口句柄
        x, y: 窗口位置 (可选)
        width, height: 窗口大小 (可选)
    
    Returns:
        bool: 是否成功
    """
    logger.info(f"开始挂载窗口: hwnd=0x{hwnd:X}, 位置=({x},{y}), 大小=({width}x{height})")
    
    # 1. 创建WorkerW
    worker_w = create_worker_w()
    if not worker_w:
        logger.error("创建WorkerW失败，挂载失败")
        return False
    
    # 2. 将目标窗口设置为WorkerW的子窗口
    result = SetParent(hwnd, worker_w)
    if not result:
        logger.error("SetParent失败")
        return False
    
    logger.info(f"成功将窗口挂载到WorkerW: 0x{worker_w:X}")
    
    # 3. 设置窗口位置和大小
    if width > 0 and height > 0:
        # 使用指定的位置和大小
        SetWindowPos(hwnd, None, x, y, width, height, SWP_NOZORDER)
        logger.info(f"设置窗口位置和大小: ({x},{y}) {width}x{height}")
    else:
        # 使用WorkerW的大小（全屏）
        rect = RECT()
        if GetWindowRect(worker_w, byref(rect)):
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            SetWindowPos(hwnd, None, 0, 0, w, h, SWP_NOZORDER)
            logger.info(f"设置窗口为全屏大小: {w}x{h}")
        else:
            logger.warning("获取WorkerW大小失败，使用默认设置")
    
    # 4. 显示窗口
    ShowWindow(hwnd, SW_SHOW)
    
    logger.info(f"[WallpaperHoster] hwnd:0x{hwnd:X} 挂载到WorkerW句柄: 0x{worker_w:X} 区域: x={x},y={y},w={width},h={height}")
    return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("请传入 Electron 窗口句柄（十进制）")
        print("用法: python wallpaper_hoster.py <hwnd> [x] [y] [width] [height]")
        return 1
    
    try:
        # 解析参数
        hwnd = int(sys.argv[1])
        x = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        y = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        width = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        height = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        
        # 执行壁纸挂载
        success = set_as_wallpaper(hwnd, x, y, width, height)
        
        if success:
            print(f"[WallpaperHoster] hwnd:{hwnd} 挂载到WorkerW成功 区域: x={x},y={y},w={width},h={height}")
            return 0
        else:
            print("壁纸挂载失败")
            return 1
            
    except ValueError as e:
        logger.error(f"参数解析错误: {e}")
        print("错误：窗口句柄必须是数字")
        return 1
    except Exception as e:
        logger.error(f"挂载过程中发生错误: {e}")
        print(f"挂载失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
