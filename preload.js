const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // 1. 렌더러 -> 메인으로 메시지 보내기 (send)
    send: (channel, data) => {
        // 보안을 위해 허용된 채널만 전송 가능하게 필터링 (선택사항이지만 추천)
        let validChannels = [
            'open-settings', 'open-school-setup', 'open-calendar', 'open-3d-viewer', 
            'quit-app', 'set-language', 'set-theme', 'set-font-size', 'set-opacity', 
            'resize-me', // 이건 위젯용
            'school-setup-complete', 'date-selected', 'get-settings',
            
            // 👇 [여기 추가!] 설정 창, 학교 설정 창, 캘린더 창 리사이즈 채널 추가
            'resize-settings-window', 
            'resize-setup-window',
            'resize-calendar-window',
            'resize-update-window',

            // 👇 [혹시 모르니 이것들도 확인]
            'save-captured-image', 'viewer-toggle-maximize' 
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        } else {
            // 디버깅용 로그 (나중에 지워도 돼)
            console.warn(`Blocked channel: ${channel}`);
        }
    },
    // 2. 메인 -> 렌더러 메시지 받기 (on)
    on: (channel, func) => {
        let validChannels = [
            'load-settings', 
            'update-school-info', 
            'change-date', 
            'language-changed', 
            'theme-changed', 
            'font-size-changed',
            // 👇 [여기 추가!] 메인에서 보내주는 날짜를 받으려면 이게 필수야!
            'set-initial-date',
            // 👇 [혹시 모르니 이것도 추가] 뷰어 창에서 이미지 받을 때 필요함
            'load-3d-image',
            'update-downloaded',
            'update-error'
        ];
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        }
    },
    // 3. [중요] API 요청을 메인에게 시키기 (axios 대체)
    fetchDailyMenu: (schoolName, date) => ipcRenderer.invoke('fetch-daily-menu', { schoolName, date }),
    // preload.js의 contextBridge 안에 추가
    fetchInquiry: (category, content) => ipcRenderer.invoke('submit-inquiry', { category, content }),
    
    // update.html이나 다른 창에서 전용 함수로 호출할 때 필요해
    onThemeChanged: (callback) => ipcRenderer.on('theme-changed', callback),
    onLanguageChanged: (callback) => ipcRenderer.on('language-changed', callback),

    // [업데이트 관련]
    onUpdateAvailableInfo: (callback) => ipcRenderer.on('update-available-info', callback),
    onUpdateProgress: (callback) => ipcRenderer.on('update-progress', callback),
    onUpdateDownloaded: (callback) => ipcRenderer.on('update-downloaded', callback),
    
    startDownloadUpdate: () => ipcRenderer.send('start-download-update'),
    quitAndInstall: () => ipcRenderer.send('quit-and-install'),
    closeUpdateWindow: () => ipcRenderer.send('close-update-window'),
});
