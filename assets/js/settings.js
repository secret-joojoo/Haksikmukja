const { UI_TEXT } = window.CONSTANTS;
const translations = UI_TEXT.settings;

function quitApp() { window.electronAPI.send('quit-app'); }

let currentLang = 'ko'; 
let currentTheme = 'dark'; 

window.onload = () => {
    window.electronAPI.send('get-settings');
    sendHeight(); 
};

window.electronAPI.on('load-settings', (data) => {
    if (data.opacity) {
        const slider = document.getElementById('opacityRange');
        const text = document.getElementById('opacityValue');
        const transparency = Math.round((1 - data.opacity) * 100);
        slider.value = transparency;
        text.innerText = transparency + "%";
    }

    if (data.language) {
        currentLang = data.language;
        applyTranslations(data.language);
        updateLangBtnActive(data.language);
    }
    if (data.zoomLevel) {
        updateFontBtnActive(data.zoomLevel);
    }
    if (data.theme) {
        currentTheme = data.theme;
        applyThemeUI(currentTheme); 
        updateThemeBtnActive(currentTheme); 
    }
    // 🔴 [추가] 자동 실행 여부 받아서 버튼 활성화
    if (data.openAtLogin !== undefined) {
        updateStartupBtnActive(data.openAtLogin);
    }
    setTimeout(sendHeight, 50);
});

function changeLanguage(lang) {
    window.electronAPI.send('set-language', lang);
    updateLangBtnActive(lang);
}

window.electronAPI.on('language-changed', (lang) => {
    currentLang = lang;
    applyTranslations(lang);
    updateLangBtnActive(lang);
    refreshSelectedText(lang);
    setTimeout(sendHeight, 50); 
});

function updateLangBtnActive(lang) {
    const btnKo = document.getElementById('btnKo');
    const btnEn = document.getElementById('btnEn');
    btnKo.removeAttribute('style');
    btnEn.removeAttribute('style');
    if (lang === 'ko') {
        btnKo.classList.add('active');
        btnEn.classList.remove('active');
    } else {
        btnKo.classList.remove('active');
        btnEn.classList.add('active');
    }
}

function applyTranslations(lang) {
    // 1. 일반 텍스트 번역
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[key] && translations[key][lang]) {
            el.innerText = translations[key][lang];
        }
    });

    // 2. 🔴 [추가] Placeholder 번역 (입력창 등)
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[key] && translations[key][lang]) {
            el.placeholder = translations[key][lang];
        }
    });
}

// 🔴 [추가] 언어 변경 시 선택된 옵션 텍스트도 같이 번역
function refreshSelectedText(lang) {
    const key = document.getElementById('contactReasonKey').value;
    const textSpan = document.getElementById('selectedText');
    
    if (key && translations[key]) {
        // 이미 선택된 항목이 있다면 그 항목의 번역 텍스트로 교체
        textSpan.innerText = translations[key][lang];
    } else {
        // 선택된 게 없으면 기본 placeholder 문구로 교체
        textSpan.innerText = translations['selectTopicPlaceholder'][lang];
    }
}

function toggleLanguagePanel() {
    const panel = document.getElementById('languagePanel');
    panel.style.display = (panel.style.display === 'none') ? 'flex' : 'none';
    setTimeout(sendHeight, 10);
}

function toggleFontSizePanel() {
    const panel = document.getElementById('fontPanel');
    panel.style.display = (panel.style.display === 'none') ? 'flex' : 'none';
    setTimeout(sendHeight, 10);
}

function setFontSize(size) {
    window.electronAPI.send('set-font-size', size);
}

window.electronAPI.on('font-size-changed', (factor) => {
    updateFontBtnActive(factor);
    setTimeout(sendHeight, 50);
});

function updateFontBtnActive(factor) {
    document.querySelectorAll('.font-btn').forEach(btn => {
        btn.removeAttribute('style');
        const val = parseFloat(btn.getAttribute('data-val'));
        if (Math.abs(val - factor) < 0.01) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function toggleOpacity() {
    const panel = document.getElementById('opacityPanel');
    panel.style.display = (panel.style.display === 'none') ? 'flex' : 'none';
    setTimeout(sendHeight, 10);
}

const opRange = document.getElementById('opacityRange');
opRange.addEventListener('input', function() {
    const userValue = Number(this.value); 
    document.getElementById('opacityValue').innerText = userValue + "%";
    const opacityToSend = (100 - userValue) / 100;
    window.electronAPI.send('set-opacity', opacityToSend);
});

function setTheme(themeName) {
    window.electronAPI.send('set-theme', themeName);
}

window.electronAPI.on('theme-changed', (themeName) => {
    currentTheme = themeName;
    applyThemeUI(themeName);
    updateThemeBtnActive(themeName);
});

function applyThemeUI(themeName) {
    document.body.setAttribute('data-theme', themeName);
}

function updateThemeBtnActive(themeName) {
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.removeAttribute('style'); 
        const val = btn.getAttribute('data-val');
        if (val === themeName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function toggleThemePanel() {
    const panel = document.getElementById('themePanel');
    panel.style.display = (panel.style.display === 'none') ? 'flex' : 'none';
    setTimeout(sendHeight, 10); 
}

function toggleContactPanel() {
    const panel = document.getElementById('contactPanel');
    const isHidden = panel.style.display === 'none';
    panel.style.display = isHidden ? 'flex' : 'none';
    setTimeout(sendHeight, 10);
}

// 🔴 [커스텀 셀렉트 로직 수정]
function toggleCustomSelect() {
    const options = document.getElementById('customOptions');
    const isClosed = options.style.display === 'none';
    options.style.display = isClosed ? 'block' : 'none';
    
    const arrow = document.querySelector('.custom-select .arrow');
    arrow.style.transform = isClosed ? 'rotate(180deg)' : 'rotate(0deg)';

    if (isClosed) setTimeout(() => sendHeight(), 10);
}

// 🔴 [옵션 선택 로직 수정] 텍스트 대신 '번역 키(translationKey)'를 받음
function selectOption(value, translationKey) {
    const textSpan = document.getElementById('selectedText');
    
    // 1. 현재 언어에 맞는 텍스트 가져오기
    const translatedText = translations[translationKey][currentLang];
    textSpan.innerText = translatedText;
    
    // 2. 값 저장 (value는 서버 전송용, key는 번역용)
    document.getElementById('contactReason').value = value;
    document.getElementById('contactReasonKey').value = translationKey; 
    
    // 3. 스타일 변경
    textSpan.style.color = 'var(--text-main)';
    
    toggleCustomSelect();
}

// 외부 클릭 시 닫기
window.addEventListener('click', function(e) {
    const wrapper = document.querySelector('.custom-select-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
        document.getElementById('customOptions').style.display = 'none';
        const arrow = document.querySelector('.custom-select .arrow');
        if(arrow) arrow.style.transform = 'rotate(0deg)';
        sendHeight(); 
    }
});

function showModal(message) {
    const modal = document.getElementById('customModal');
    const msgBox = document.getElementById('modalMessage');
    msgBox.innerText = message; 
    modal.style.display = 'flex'; 
}

function closeModal() {
    const modal = document.getElementById('customModal');
    modal.style.display = 'none'; 
}

// 🔴 [문의 전송 로직 수정] 메시지 다국어 처리
async function submitInquiry() {
    const category = document.getElementById('contactReason').value;
    const content = document.getElementById('contactContent').value;

    if (!category) {
        showModal(translations['msgSelectTopic'][currentLang]);
        return;
    }

    if (!content.trim()) {
        showModal(translations['msgEnterContent'][currentLang]);
        return;
    }

    const submitBtn = document.querySelector('#contactPanel button');
    submitBtn.disabled = true;
    const originalBtnText = submitBtn.innerText;
    submitBtn.innerText = translations['msgSending'][currentLang];

    try {
        // ✅ [수정] 결과를 response 변수에 할당해야 합니다!
        // fetchInquiry는 메인 프로세스에서 반환한 상태 코드(status)를 리턴합니다.
        const status = await window.electronAPI.fetchInquiry(category, content);

        // 메인 프로세스에서 200 OK 등을 반환하면 성공으로 간주
        if (status >= 200 && status < 300) {
            showModal(translations['msgSuccess'][currentLang]); 
            document.getElementById('contactContent').value = ""; 
            // document.getElementById('contactReason').value = ""; // 필요시 초기화
            // refreshSelectedText(currentLang); // 필요시 텍스트 초기화
            toggleContactPanel(); 
        } else {
            // 400, 500 등의 에러 코드인 경우
            showModal(translations['msgFail'][currentLang]);
        }
    } catch (error) {
        console.error(error);
        showModal(translations['msgNetworkError'][currentLang]);
    } finally {
        submitBtn.disabled = false;
        // 버튼 텍스트 복구 시에도 현재 언어 반영
        submitBtn.innerText = translations['submitInquiryBtn'][currentLang];
    }
}

function sendHeight() {
    const titleBar = document.querySelector('.title-bar');
    const menuList = document.querySelector('.menu-list');
    const contentWrapper = document.querySelector('.content-wrapper');

    if (titleBar && menuList) {
        const contentHeight = menuList.offsetHeight;
        const headerHeight = titleBar.offsetHeight;
        let padding = 0;
        if (contentWrapper) {
            const style = window.getComputedStyle(contentWrapper);
            padding = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
        }
        const totalHeight = headerHeight + contentHeight + padding + 2; 
        window.electronAPI.send('resize-settings-window', totalHeight);
    }
}

// 🔴 [추가] 패널 토글 함수
function toggleStartupPanel() {
    const panel = document.getElementById('startupPanel');
    panel.style.display = (panel.style.display === 'none') ? 'flex' : 'none';
    setTimeout(sendHeight, 10);
}

function setStartup(enable) {
    window.electronAPI.send('set-startup', enable);
    updateStartupBtnActive(enable);
}

// 🔴 [추가] 버튼 스타일 업데이트 (활성화 된 쪽에 active 클래스 부여)
function updateStartupBtnActive(isEnabled) {
    const btnOn = document.getElementById('btnStartupOn');
    const btnOff = document.getElementById('btnStartupOff');
    
    // 일단 스타일 초기화
    btnOn.classList.remove('active');
    btnOff.classList.remove('active');
    
    // 상태에 따라 active 클래스 추가 (settings.css에 이미 정의되어 있음)
    if (isEnabled) {
        btnOn.classList.add('active');
    } else {
        btnOff.classList.add('active');
    }
}

const menuList = document.querySelector('.menu-list');
let resizeTimer; // 타이머 변수 추가

if (menuList) {
    const observer = new ResizeObserver(() => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            sendHeight(); // 0.1초 뒤에 한 번만 실행
        }, 50);
    });
    observer.observe(menuList);
}

window.changeLanguage = changeLanguage;
window.setFontSize = setFontSize;
window.setTheme = setTheme;
window.setStartup = setStartup;
window.quitApp = quitApp;
window.submitInquiry = submitInquiry;