using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

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
    static extern IntPtr GetWindow(IntPtr hWnd, uint uCmd);

    [DllImport("user32.dll")]
    static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left, Top, Right, Bottom;
    }

    static IntPtr CreateWorkerW()
    {
        IntPtr progman = FindWindow("Progman", null);
        IntPtr result;
        // 1. 向Progman发送消息，促使系统创建新的WorkerW
        SendMessageTimeout(progman, 0x052C, new IntPtr(0xD), new IntPtr(0x1), 0, 1000, out result);

        IntPtr workerw = IntPtr.Zero;

        // 2. 枚举所有窗口，找到带有 SHELLDLL_DefView 的 WorkerW，再取其下一个 WorkerW
        EnumWindows((tophandle, topparamhandle) =>
        {
            StringBuilder sb = new StringBuilder(256);
            GetClassName(tophandle, sb, sb.Capacity);
            if (sb.ToString() == "WorkerW")
            {
                IntPtr shellView = FindWindowEx(tophandle, IntPtr.Zero, "SHELLDLL_DefView", null);
                if (shellView != IntPtr.Zero)
                {
                    // 找到带有 SHELLDLL_DefView 的 WorkerW，取其下一个 WorkerW
                    workerw = GetWindow(tophandle, 2); // GW_HWNDNEXT = 2
                }
            }
            return true;
        }, IntPtr.Zero);

        // 3. 兜底：找不到就用 FindWindowEx
        if (workerw == IntPtr.Zero)
        {
            workerw = FindWindowEx(progman, IntPtr.Zero, "WorkerW", null);
        }
        return workerw;
    }

    static void Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        if (args.Length < 1)
        {
            Console.WriteLine("请传入 Electron 窗口句柄（十进制）");
            return;
        }
        IntPtr hwnd = (IntPtr)Convert.ToInt32(args[0]);
        IntPtr workerw = CreateWorkerW();
        if (workerw == IntPtr.Zero)
        {
            Console.WriteLine("未能找到 WorkerW，挂载失败。");
            return;
        }

        SetParent(hwnd, workerw);

        // 可选：调整壁纸窗口大小为 WorkerW 区域
        if (GetWindowRect(workerw, out RECT rect))
        {
            SetWindowPos(hwnd, IntPtr.Zero, 0, 0, rect.Right - rect.Left, rect.Bottom - rect.Top, 0x0010); // SWP_NOZORDER
        }

        ShowWindow(hwnd, 5); // SW_SHOW
        Console.WriteLine($"[WallpaperHosterLively] hwnd:{hwnd} 挂载到WorkerW句柄: 0x{workerw.ToInt64():X}");
    }
}
