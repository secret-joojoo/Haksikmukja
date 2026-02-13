const { app, BrowserWindow, screen, ipcMain, dialog } = require('electron');
const fs = require('fs');
const Store = require('electron-store');
const path = require('path');
const axios = require('axios'); // 🌟 [추가] 렌더러 대신 메인이 axios를 써야 해
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');

autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';
autoUpdater.verifyUpdateCodeSignature = false;

log.info('App starting...');

const store = new Store();

// 전역 변수 관리
let widgetWin = null;
let viewerWin = null;
let settingsWin = null;
let schoolSetupWin = null;
let calendarWin = null;
let updateWin = null;

// 💾 저장된 설정 불러오기
let currentZoomLevel = Number(store.get('zoomLevel', 1.0));
let currentLang = store.get('language', 'ko');
let currentTheme = store.get('theme', 'dark'); // ✨ [추가] 테마 설정 로드

// -------------------------------------------------------------
// 🛠️ 공통: 창 로딩 끝난 뒤 배율 강제 적용 함수 (확인 사살용)
// -------------------------------------------------------------
function applyZoomIdeally(win) {
    if (!win) return;
    
    // 1. 페이지 내비게이션(로드) 완료 시점에 강제 적용
    win.webContents.on('did-finish-load', () => {
        win.webContents.setZoomFactor(currentZoomLevel);
    });
}


// 1. 메인 위젯 창 생성
function createWidgetWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  const windowWidth = 350;

  widgetWin = new BrowserWindow({
    width: windowWidth,
    height: 100,
    x: width - windowWidth,
    y: 0,
    frame: false,
    transparent: true,      // 🔴 [체크] 투명 배경 유지
    resizable: false,       // 🔴 [체크] 리사이즈 불가 유지
    skipTaskbar: true,      // 🔴 [체크] 태스크바 숨김 유지
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    opacity: store.get('opacity', 1.0),
    webPreferences: { 
        nodeIntegration: false, 
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), // 🌉 [추가] 다리 연결
        zoomFactor: currentZoomLevel 
    }
  });

  applyZoomIdeally(widgetWin);

  widgetWin.loadFile('index.html');
  // 👇 [추가 2] 창이 켜지고 나면 업데이트 체크 시작!
  widgetWin.once('ready-to-show', () => {
      autoUpdater.checkForUpdatesAndNotify();
  });
  widgetWin.on('closed', () => { widgetWin = null; });
}

// 2. 3D 뷰어 창 생성
function createViewerWindow(data) {
  if (viewerWin) {
    viewerWin.focus();
    viewerWin.webContents.send('load-3d-image', data);
    return;
  }

  viewerWin = new BrowserWindow({
    width: 800,
    height: 600,
    title: "메뉴 상세보기",
    frame: false,
    resizable: false,
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), // 🌉 [추가] 다리 연결
        webSecurity: false, // 🔴 [체크] 로컬 이미지 로드 등을 위해 필요
        zoomFactor: currentZoomLevel
    }
  });

  applyZoomIdeally(viewerWin);

  viewerWin.loadFile('viewer.html');

  viewerWin.webContents.once('did-finish-load', () => {
    viewerWin.webContents.send('load-3d-image', data);
    viewerWin.webContents.send('language-changed', currentLang);
    viewerWin.webContents.send('theme-changed', currentTheme); // ✨ [추가] 테마 적용
  });

  viewerWin.on('closed', () => { viewerWin = null; });
}

// 3. 설정 창 생성
function createSettingsWindow() {
  if (settingsWin) {
    settingsWin.focus();
    return;
  }

  settingsWin = new BrowserWindow({
    width: 400,
    height: 500,
    minWidth: 350,
    title: "설정",
    frame: false,
    resizable: false, // 🔴 [수정] true -> false (UX 복구! 사용자가 임의로 늘리면 안 됨)
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    webPreferences: { 
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), // 🌉 [추가] 다리 연결
        zoomFactor: currentZoomLevel
    }
  });

  applyZoomIdeally(settingsWin);

  settingsWin.loadFile('settings.html');
  settingsWin.on('closed', () => { settingsWin = null; });
}

// 4. 학교 설정 창
function createSchoolSetupWindow() {
  if (schoolSetupWin) {
    schoolSetupWin.focus();
    return;
  }
  schoolSetupWin = new BrowserWindow({
    width: 400,
    height: 300,
    title: "학교 설정",
    frame: false,
    resizable: false, // 🔴 [체크] 고정 크기
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    webPreferences: { 
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), // 🌉 [추가] 다리 연결
        zoomFactor: currentZoomLevel
    }
  });

  applyZoomIdeally(schoolSetupWin);

  schoolSetupWin.loadFile('school-setup.html');
  schoolSetupWin.on('closed', () => { schoolSetupWin = null; });
}

// 5. 캘린더 창
function createCalendarWindow() {
  if (calendarWin) {
    calendarWin.focus();
    return;
  }
  calendarWin = new BrowserWindow({
    width: 300,
    height: 290,
    title: "캘린더",
    frame: false,
    resizable: false, // 🔴 [체크] 고정 크기
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    webPreferences: { 
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), // 🌉 [추가] 다리 연결
        zoomFactor: currentZoomLevel
    }
  });

  applyZoomIdeally(calendarWin);

  calendarWin.loadFile('calendar.html');
  calendarWin.on('closed', () => { calendarWin = null; });
}

// 🌟 [추가] 업데이트 알림 창 생성 함수
function createUpdateWindow(updateInfo) {
  if (updateWin) {
    updateWin.focus();
    return;
  }

  updateWin = new BrowserWindow({
    width: 500,
    height: 700, // 내용(패치내역)이 들어갈 공간 확보
    title: "업데이트 알림",
    frame: false,
    resizable: false,
    icon: path.join(__dirname, 'assets/icons/ic_logo.png'),
    webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'), 
        zoomFactor: currentZoomLevel
    }
  });

  applyZoomIdeally(updateWin);
  updateWin.loadFile('update.html');

  updateWin.webContents.once('did-finish-load', () => {
    // 1. 테마 적용
    updateWin.webContents.send('theme-changed', currentTheme);
    // 2. 언어 적용
    updateWin.webContents.send('language-changed', currentLang);
    // 3. 업데이트 정보(버전, 패치내역) 전송
    updateWin.webContents.send('update-available-info', updateInfo);
  });

  updateWin.on('closed', () => { updateWin = null; });
}

app.whenReady().then(() => {
  const isFirstRun = !store.get('hasRunBefore');

  if (isFirstRun) {   
      app.setLoginItemSettings({
          openAtLogin: true,
          path: app.getPath('exe') // 현재 실행 파일 경로 등록
      });

      // 이제 "나 실행된 적 있어!"라고 도장을 쾅 찍어둬.
      // 다음에 켜질 땐 이 if문 안으로 안 들어오게 됨.
      store.set('hasRunBefore', true);
  }

  createWidgetWindow();

  // --- IPC 핸들러 ---

  // [뷰어] 열기
  ipcMain.on('open-3d-viewer', (event, data) => { createViewerWindow(data); });

  // [뷰어] 최대화 토글
  ipcMain.on('viewer-toggle-maximize', () => {
    if (viewerWin) {
      viewerWin.isMaximized() ? viewerWin.unmaximize() : viewerWin.maximize();
    }
  });

  // [뷰어] JPG 저장
  ipcMain.on('save-captured-image', async (event, base64Data) => {
    const data = base64Data.replace(/^data:image\/jpeg;base64,/, "");
    const { filePath } = await dialog.showSaveDialog(viewerWin, {
      title: '이미지 저장',
      defaultPath: 'menu_image.jpg',
      filters: [{ name: 'JPG Image', extensions: ['jpg'] }]
    });
    if (filePath) {
      fs.writeFile(filePath, data, 'base64', (err) => console.log(err || '저장 성공'));
    }
  });

  // [설정] 값 요청 (테마 포함!)
  ipcMain.on('get-settings', (event) => {
    // 🔴 [추가] 현재 앱이 로그인(부팅) 시 자동 실행되도록 설정되어 있는지 확인
    const loginSettings = app.getLoginItemSettings();

    const data = {
      opacity: store.get('opacity', 1.0),
      school: store.get('school', null),
      cafeteria: store.get('cafeteria', null),
      language: currentLang,
      zoomLevel: currentZoomLevel,
      theme: currentTheme, // ✨ [추가] 테마 정보 전송
      // 🔴 [추가] 이 값을 렌더러로 보냄
      openAtLogin: loginSettings.openAtLogin
    };
    event.sender.send('load-settings', data);
  });

  // 🔴 [추가] 윈도우 시작 시 자동 실행 설정 핸들러
  ipcMain.on('set-startup', (event, enable) => {
      // 개발 모드(!app.isPackaged)에서는 동작이 확실하지 않을 수 있어.
      // 하지만 빌드된 앱(exe)에서는 정상 작동해.
      app.setLoginItemSettings({
          openAtLogin: enable, // true면 자동실행 켜기, false면 끄기
          path: app.getPath('exe') // 확실하게 현재 실행 파일 경로 지정
      });
      console.log(`[Setting] Startup Auto-launch: ${enable}`);
  });

  // [설정] 언어 변경
  ipcMain.on('set-language', (event, lang) => {
    currentLang = lang;
    store.set('language', lang);
    BrowserWindow.getAllWindows().forEach(win => {
        win.webContents.send('language-changed', lang);
    });
  });

  // ✨ [추가] 테마 변경 핸들러
  ipcMain.on('set-theme', (event, themeName) => {
    currentTheme = themeName;
    store.set('theme', themeName); // 영구 저장
    
    // 모든 열린 창들에게 테마 변경 알림
    BrowserWindow.getAllWindows().forEach(win => {
        win.webContents.send('theme-changed', themeName);
    });
  });

  // [설정] 글자 크기(배율) 변경
  ipcMain.on('set-font-size', (event, size) => {
    let factor = 1.0;
    if (size === 'small') factor = 0.85;
    if (size === 'large') factor = 1.15;

    currentZoomLevel = factor;
    store.set('zoomLevel', factor); 

    BrowserWindow.getAllWindows().forEach(win => {
        win.webContents.setZoomFactor(factor);
        win.webContents.send('font-size-changed', factor);
    });
  });

  // [설정] 투명도
  ipcMain.on('set-opacity', (event, value) => {
    store.set('opacity', Number(value));
    if (widgetWin) widgetWin.setOpacity(Number(value));
  });

  // [설정] 창 열기/종료/최대화
  ipcMain.on('open-settings', () => createSettingsWindow());
  ipcMain.on('quit-app', () => app.quit());
  ipcMain.on('maximize-settings', () => {
    if (settingsWin) settingsWin.isMaximized() ? settingsWin.unmaximize() : settingsWin.maximize();
  });

  // [학교설정] 관련
  ipcMain.on('open-school-setup', () => createSchoolSetupWindow());
  ipcMain.on('school-setup-complete', (event, data) => {
    store.set('school', data.school);
    store.set('cafeteria', data.cafeteria);
    if (widgetWin) widgetWin.webContents.send('update-school-info', data);
    if (schoolSetupWin) schoolSetupWin.close();
  });
  
  // 리사이즈 핸들러
  ipcMain.on('resize-setup-window', (event, h) => {
      if(schoolSetupWin) schoolSetupWin.setBounds({ width: 400, height: Math.ceil(h * currentZoomLevel) });
  });
  ipcMain.on('resize-calendar-window', (event, h) => {
      if(calendarWin) calendarWin.setBounds({ width: 300, height: Math.ceil(h * currentZoomLevel) });
  });
  ipcMain.on('resize-me', (event, h) => {
      if(widgetWin) widgetWin.setSize(350, Math.ceil(h * currentZoomLevel), true);
  });
  // 🔴 [수정] setSize 대신 setBounds 사용! (이게 훨씬 말을 잘 들어)
  ipcMain.on('resize-settings-window', (event, h) => {
      if(settingsWin) {
          // 너비는 현재 너비 유지, 높이만 강력하게 변경
          const currentWidth = settingsWin.getBounds().width; 
          settingsWin.setBounds({ 
              width: currentWidth, 
              height: Math.ceil(h * currentZoomLevel) 
          });
      }
  });

  // [캘린더] 관련
  ipcMain.on('open-calendar', (event, dateStr) => {
    createCalendarWindow();
    if (calendarWin) {
       calendarWin.webContents.once('did-finish-load', () => {
         calendarWin.webContents.send('set-initial-date', dateStr);
         // 캘린더 열 때도 테마 동기화 한 번 더 (안전장치)
         calendarWin.webContents.send('theme-changed', currentTheme);
       });
    }
  });
  ipcMain.on('date-selected', (event, data) => {
    if (widgetWin) widgetWin.webContents.send('change-date', data);
    if (calendarWin) calendarWin.close();
  });

  // ipcMain 핸들러들이 모여있는 곳에 추가해
  ipcMain.handle('fetch-daily-menu', async (event, { schoolName, date }) => {
      try {
          const response = await axios.get('https://haksikmukja-server.fly.dev/api/v1/daily', {
              params: {
                  school_name: schoolName,
                  target_date: date
              }
          });
          return response.data; // 데이터를 렌더러에게 반환
      } catch (error) {
          console.error("API Error:", error);
          throw error; // 에러가 나면 렌더러에게 알림
      }
  });

  // main.js의 ipcMain 부분
  ipcMain.handle('submit-inquiry', async (event, { category, content }) => {
      // 여기서 axios로 서버에 전송 (메인 프로세스에는 axios가 require되어 있어야 함)
      // const axios = require('axios'); // 상단에 선언
      const response = await axios.post('https://haksikmukja-server.fly.dev/api/v1/inquiries/', {
          category, content
      });
      return response.status; // 성공 여부 반환
  });

  autoUpdater.autoDownload = false;

  // 👇 [추가 3] 업데이트 관련 이벤트 로그 (확인용)
  autoUpdater.on('checking-for-update', () => {
      log.info('업데이트 확인 중...');
  });

  autoUpdater.on('update-available', (info) => {
      console.log('업데이트 발견:', info);
      createUpdateWindow(info);
  });

  autoUpdater.on('update-not-available', () => {
      log.info('현재 최신 버전입니다.');
  });

  autoUpdater.on('download-progress', (progressObj) => {
      if (updateWin) {
          updateWin.webContents.send('update-progress', progressObj.percent);
      }
  });

  autoUpdater.on('update-downloaded', () => {
      if (updateWin) {
          updateWin.webContents.send('update-downloaded');
      }
  });

  autoUpdater.on('error', (err) => {
      console.error('업데이트 에러:', err);
      // 업데이트 창이 켜져 있다면 에러 사실을 알려줌
      if (updateWin) {
          updateWin.webContents.send('update-error', err.message);
      }
  });

  // 👇 [추가] 업데이트 창에서 "예(업데이트)" 눌렀을 때
  ipcMain.on('start-download-update', () => {
      autoUpdater.downloadUpdate();
  });

  // 👇 [추가] 업데이트 창에서 "재시작" 눌렀을 때
  ipcMain.on('quit-and-install', () => {
      autoUpdater.quitAndInstall();
  });
  
  // 👇 [추가] 업데이트 창 닫기 (아니오)
  ipcMain.on('close-update-window', () => {
      if (updateWin) updateWin.close();
  });

  // 🔴 [추가] 업데이트 창 리사이즈 핸들러
  ipcMain.on('resize-update-window', (event, h) => {
      if (updateWin) {
          // 너비는 고정(500), 높이만 내용에 맞춰서 변경
          // 500은 createUpdateWindow에서 설정한 width 값과 맞춰주는 게 좋아
          const currentWidth = updateWin.getBounds().width;
          updateWin.setBounds({ 
              width: currentWidth, 
              height: Math.ceil(h * currentZoomLevel) 
          });
      }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWidgetWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});