using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
// using System.Management;

class WallpaperHosterLively
{
    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr FindWindowEx(IntPtr parentHandle, IntPtr childAfter, string className, string windowTitle);

    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr SetParent(IntPtr hWndChild, IntPtr hWndNewParent);

    [DllImport("user32.dll")]
    static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    static extern int SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);

    [DllImport("user32.dll")]
    static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    static extern bool IsWindowVisible(IntPtr hWnd);

    // 备用win版本识别方案
    // static bool IsWindows11OrGreater()
    // {
    //     try
    //     {
    //         using (var searcher = new ManagementObjectSearcher("SELECT Version FROM Win32_OperatingSystem"))
    //         {
    //             foreach (var os in searcher.Get())
    //             {
    //                 string version = os["Version"].ToString(); // 例如 "10.0.22000"
    //                 var parts = version.Split('.');
    //                 if (parts.Length >= 3 && int.TryParse(parts[2], out int build))
    //                 {
    //                     return build >= 22000;
    //                 }
    //             }
    //         }
    //     }
    //     catch { }
    //     return false;
    // }

    static bool IsWindows11OrGreater()
    {
        // 22000是Win11的第一个正式版Build号
        return Environment.OSVersion.Version.Build >= 22000;
    }

    static void Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;

        if (args.Length < 1)
        {
            Console.WriteLine("请传入 Electron 窗口句柄（十进制）");
            return;
        }
        IntPtr hwnd = (IntPtr)Convert.ToInt32(args[0]);
        IntPtr progman = FindWindow("Progman", null);
        IntPtr result;
        // 1. 向Progman发送消息，创建新WorkerW
        // SendMessageTimeout(progman, 0x052C, IntPtr.Zero, IntPtr.Zero, 0, 1000, out result);

        IntPtr wallpaperWorkerW = IntPtr.Zero;
        if (args.Length > 1)
        {
            wallpaperWorkerW = (IntPtr)Convert.ToInt32(args[1]);
            SetParent(hwnd, wallpaperWorkerW);
            Console.WriteLine($"[WallpaperHosterLively] hwnd:{hwnd} 直接-挂载到WorkerW句柄: 0x{wallpaperWorkerW.ToInt64():X}");
            ShowWindow(hwnd, 5); // SW_SHOW
            return;
        }
        // Console.WriteLine("[WallpaperHosterLively] 枚举所有WorkerW窗口:");
        if (IsWindows11OrGreater())
        {   
            Console.WriteLine("[WallpaperHosterLively] 检测到 Windows 11 或更高版本");
            // Win11策略：查找Progman下的第一个WorkerW
            wallpaperWorkerW = FindWindowEx(progman, IntPtr.Zero, "WorkerW", null);
            if (wallpaperWorkerW == IntPtr.Zero)
            {
                Console.WriteLine("[WallpaperHosterLively] Win11: 未找到Progman下的WorkerW，兜底用Progman");
                wallpaperWorkerW = progman;
            }
            else
            {
                Console.WriteLine($"[WallpaperHosterLively] Win11: 挂载到Progman下的WorkerW句柄: 0x{wallpaperWorkerW.ToInt64():X}");
            }
        }
        else
        {
            Console.WriteLine("[WallpaperHosterLively] 检测到 Windows 10");
            // Win10及以下策略
            EnumWindows((hWnd, lParam) =>
            {
                var className = new StringBuilder(256);
                GetClassName(hWnd, className, className.Capacity);
                if (className.ToString() == "WorkerW")
                {
                    IntPtr shellView = FindWindowEx(hWnd, IntPtr.Zero, "SHELLDLL_DefView", null);
                    bool isVisible = IsWindowVisible(hWnd);
                    Console.WriteLine($"  WorkerW句柄: 0x{hWnd.ToInt64():X}, SHELLDLL_DefView: {(shellView != IntPtr.Zero ? "有" : "无")}, 可见: {(isVisible ? "是" : "否")}");
                    if (shellView == IntPtr.Zero && isVisible)
                    {
                        wallpaperWorkerW = hWnd; // 只记录最后一个可见的无SHELLDLL_DefView的WorkerW
                    }
                }
                return true;
            }, IntPtr.Zero);
            if (wallpaperWorkerW == IntPtr.Zero)
            {
                Console.WriteLine("[WallpaperHosterLively] 未找到可见且无SHELLDLL_DefView的WorkerW，用Progman下的WorkerW作为兜底");
                // 向Progman发送消息，创建新WorkerW
                SendMessageTimeout(progman, 0x052C, IntPtr.Zero, IntPtr.Zero, 0, 1000, out result);
                wallpaperWorkerW = FindWindowEx(progman, IntPtr.Zero, "WorkerW", null);
                if (wallpaperWorkerW == IntPtr.Zero)
                {
                    Console.WriteLine("[WallpaperHosterLively] 未找到新创建的WorkerW，使用Progman作为兜底");
                    wallpaperWorkerW = progman;
                }
                else
                {
                    Console.WriteLine($"[WallpaperHosterLively] 挂载到新创建的WorkerW句柄: 0x{wallpaperWorkerW.ToInt64():X}");
                }
            }
            else
            {
                Console.WriteLine($"[WallpaperHosterLively] 挂载到WorkerW句柄: 0x{wallpaperWorkerW.ToInt64():X}");
            }
        }
        // 手动赋一个整数给 wallpaperWorkerW
        // wallpaperWorkerW = new IntPtr(0x1044e); // 这里需要替换为实际的WorkerW句柄

        SetParent(hwnd, wallpaperWorkerW);
        Console.WriteLine($"[WallpaperHosterLively] hwnd:{hwnd} 挂载到WorkerW句柄: 0x{wallpaperWorkerW.ToInt64():X}");
        ShowWindow(hwnd, 5); // SW_SHOW
    }
}
