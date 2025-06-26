export {};

declare global {
  interface ElectronIpcRenderer {
    send: (channel: string, data: any) => void;
    on: (channel: string, listener: (event: any, ...args: any[]) => void) => void;
  }
  interface ElectronAPI {
    ipcRenderer: ElectronIpcRenderer;
  }
  interface ElectronAPI2 {
    isWallpaperMode: boolean;
    exitWallpaper: () => void;
    version?: string;
    port?: string;
    host?: string;
    enableLive2D?: boolean;
  }
  interface Window {
    electron: ElectronAPI;
    electronAPI?: ElectronAPI2;
  }
}
