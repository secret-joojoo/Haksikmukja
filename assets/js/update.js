const titleText = document.getElementById('title-text');
const versionText = document.getElementById('version-text');
const notesArea = document.getElementById('notes-area');
const progressCont = document.getElementById('progress-cont');
const progBar = document.getElementById('prog-bar');
const progressStatus = document.getElementById('progress-status');
const btnUpdate = document.getElementById('btn-update');
const btnCancel = document.getElementById('btn-cancel');
const btnClose = document.getElementById('btn-close');

// 현재 언어 상태 (기본값 ko)
let currentLang = 'ko';

// update.js

// update.js - applyTranslations 함수 부분

function applyTranslations(lang) {
    currentLang = lang;
    const uiText = window.CONSTANTS?.UI_TEXT?.update || {};

    // 1. 일반적인 텍스트들 일괄 교체
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        // progress-status는 아래에서 별도로 숫자와 함께 처리할 거니까 
        // 굳이 여기서 덮어씌워서 0%를 날려먹을 필요는 없지만, 
        // 어차피 숨겨져 있는 상태라 덮어씌워져도 상관은 없어.
        if (uiText[key]) {
            el.innerHTML = uiText[key][lang] || uiText[key]['ko'];
        }
    });

    // 2. [보완] 진행바 상태일 때 텍스트 강제 업데이트 (숫자 포함)
    if (progressCont.style.display !== 'none') {
        const percent = progBar.style.width || '0%';
        const txtDownloading = uiText.msgDownloading ? uiText.msgDownloading[lang] : "다운로드 중...";
        
        // 다운로드 완료(100%)가 아닐 때만 퍼센트 표시
        if (percent !== '100%') {
            // 여기서 "Downloading... 45%" 처럼 숫자까지 붙여서 다시 넣어줌
            progressStatus.innerText = `${txtDownloading} ${Math.round(parseFloat(percent))}%`;
        }
    }
}

// 🛠️ 창 크기 자동 조절 요청 함수
function adjustWindowHeight() {
    // 약간의 시간차를 둬서 DOM 렌더링이 끝난 뒤 계산 (안정성 확보)
    setTimeout(() => {
        // body의 전체 높이 + 여유분(시스템 테두리 등 고려해서 20~30px 정도)
        const height = document.body.scrollHeight + 15; 
        window.electronAPI.send('resize-update-window', height);
    }, 50); // 0.05초 뒤 실행
}

// 1. 테마 적용
window.electronAPI.onThemeChanged((event, theme) => {
    document.body.setAttribute('data-theme', theme);
});

// 2. 언어 변경 감지
window.electronAPI.onLanguageChanged((event, lang) => {
    applyTranslations(lang);
});

// 3. 업데이트 정보 수신
window.electronAPI.onUpdateAvailableInfo((event, info) => {
    versionText.innerText = `v${info.version}`;
    
    if (info.releaseNotes) {
        // 실제 패치 내역이 있으면 속성 제거하고 내용 표시
        notesArea.removeAttribute('data-i18n');
        notesArea.innerHTML = info.releaseNotes;
    } else {
        // 내역이 없으면 data-i18n 속성을 달아서 applyTranslations가 처리하게 위임!
        notesArea.setAttribute('data-i18n', 'msgNoNotes');
    }
    
    // 이제 번역 적용 (위에서 세팅한 속성 덕분에 msgNoNotes도 번역됨)
    applyTranslations(currentLang); 

    adjustWindowHeight();
});

// 창 닫기
const closeWindow = () => window.electronAPI.closeUpdateWindow();
btnCancel.addEventListener('click', closeWindow);
btnClose.addEventListener('click', closeWindow);

// 4. 업데이트 시작
btnUpdate.addEventListener('click', () => {
    window.electronAPI.startDownloadUpdate();
    
    const uiText = window.CONSTANTS.UI_TEXT.update;
    const msgDownloading = uiText.msgDownloading[currentLang];

    // UI 변경
    titleText.innerText = msgDownloading;
    progressCont.style.display = 'flex';
    btnUpdate.style.display = 'none';
    btnCancel.style.display = 'none';
    btnClose.style.display = 'none';

    adjustWindowHeight();
});

// 5. 진행률 업데이트
window.electronAPI.onUpdateProgress((event, percent) => {
    const p = Math.round(percent);
    progBar.style.width = p + '%';
    
    const uiText = window.CONSTANTS.UI_TEXT.update;
    const msgDownloading = uiText.msgDownloading[currentLang];
    
    progressStatus.innerText = `${msgDownloading} ${p}%`;
});

// 6. 다운로드 완료
window.electronAPI.onUpdateDownloaded((event) => {
    const uiText = window.CONSTANTS.UI_TEXT.update;
    
    // 1. 헤더와 상태 메시지 키 변경 (나중에 언어 바뀌어도 유지되게)
    titleText.setAttribute('data-i18n', 'msgInstallReady');
    progressStatus.setAttribute('data-i18n', 'msgDownloadComplete');
    progressStatus.innerText = uiText.msgDownloadComplete[currentLang]; // 이건 단순 텍스트라 그냥 둠
    progBar.style.width = '100%';
    
    // 2. 버튼 다시 보이기 및 속성 변경 🌟
    btnUpdate.style.display = 'block';
    btnUpdate.setAttribute('data-i18n', 'btnRestart'); // 키를 'btnUpdate' -> 'btnRestart'로 변경
    
    // 3. 현재 언어로 즉시 텍스트 갱신
    titleText.innerText = uiText.msgInstallReady[currentLang];
    btnUpdate.innerText = uiText.btnRestart[currentLang];
    
    // 4. 버튼 기능 변경 (이벤트 리스너 교체)
    // 주의: cloneNode하면 DOM 참조가 끊기니까 다시 찾아야 함
    const newBtn = btnUpdate.cloneNode(true);
    btnUpdate.replaceWith(newBtn);
    
    newBtn.addEventListener('click', () => {
            window.electronAPI.quitAndInstall();
    });

    adjustWindowHeight();
});

// 7. 글자 크기(배율) 변경 감지
// 설정 창에서 글자 크기를 바꾸면 이 이벤트가 날아와. 그때 높이를 다시 계산하는 거야.
window.electronAPI.on('font-size-changed', (factor) => {
    // 글자 크기가 바뀌면 줄바꿈이 달라질 수 있으니까 높이 재조정 필수!
    adjustWindowHeight();
});

window.electronAPI.on('language-changed', (factor) => {
    adjustWindowHeight();
});

// update.js 맨 아래에 추가

// 8. 업데이트 실패 (에러) 처리
window.electronAPI.on('update-error', (msg) => {
    // 1. 진행 바 숨기기
    progressCont.style.display = 'none';
    
    // 2. 버튼 다시 보이기 (혹은 그냥 창 닫기)
    btnUpdate.style.display = 'block';
    btnUpdate.innerText = "업데이트"; // 텍스트 원상복구
    btnCancel.style.display = 'block';
    
    // 3. 사용자에게 알림
    alert(`업데이트 다운로드 실패\n사유: ${msg}`);
    
    // 4. 창 닫기 (선택사항)
    // closeWindow();
});