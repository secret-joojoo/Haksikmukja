const { MENU_TYPE_MAP: menuTypeMap, UI_TEXT } = window.CONSTANTS;
const translations = UI_TEXT.main;

let currentDateStr = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD
let savedSettings = { school: null, cafeteria: null };
let currentLang = 'ko'; // 기본 언어
let lastApiData = null; // 언어 바꿀 때 다시 그리기 위해 데이터 저장용


// 1. [추가] 화면 높이에 맞춰서 최대 높이 계산하는 함수
function setDynamicMaxHeight() {
    // window.screen.availHeight : 작업 표시줄 제외한 모니터 실제 사용 가능 높이
    // 0.8을 곱해서 화면의 80%까지만 차지하게 제한 (너무 꽉 차면 답답하니까)
    const screenLimit = window.screen.availHeight * 0.8;
    
    // 타이틀바 높이(50px)랑 패딩 대충 빼줌 (여유분)
    const contentLimit = screenLimit - 50; 

    // 계산된 값을 CSS 변수 '--max-content-height'에 넣어줌!
    document.documentElement.style.setProperty('--max-content-height', `${contentLimit}px`);
}

// 🏁 초기화
window.onload = () => {
    setDynamicMaxHeight();
    window.electronAPI.send('get-settings');
};

// 📨 설정값 수신
window.electronAPI.on('load-settings', (data) => {
    savedSettings = data;
    if (data.language) {
        currentLang = data.language;
    }
    updateStaticUI();
    
    if (data.school && data.cafeteria) {
        updateHeaderUI(data.school, data.cafeteria);
        fetchDailyMenu(); 
    } else {
        document.querySelector('.content').innerHTML = 
            `<div class="empty-state-msg">${translations.noSchool[currentLang]}</div>`;
    }
    if (data.theme) document.body.setAttribute('data-theme', data.theme);
});

// 실시간 감지 추가
window.electronAPI.on('theme-changed', (themeName) => {
    document.body.setAttribute('data-theme', themeName);
});

// 📨 언어 변경 감지 (설정 창에서 바꿨을 때)
window.electronAPI.on('language-changed', (lang) => {
    currentLang = lang;
    updateStaticUI();
    if (lastApiData) {
        renderMenu(lastApiData);
    } else if (!savedSettings.school) {
        document.querySelector('.content').innerHTML = 
            `<div class="empty-state-msg">${translations.noSchool[currentLang]}</div>`;
    }
});

// 📨 학교 정보 변경
window.electronAPI.on('update-school-info', (data) => {
    savedSettings = data;
    updateHeaderUI(data.school, data.cafeteria);
    fetchDailyMenu();
});

// 📨 날짜 변경
window.electronAPI.on('change-date', (data) => {
    currentDateStr = data.date;
    fetchDailyMenu();
});


// ----------------------------------------------------
// 🛠️ 기능 로직
// ----------------------------------------------------

// 1. 고정 UI (툴팁 등) 업데이트
function updateStaticUI() {
    // 툴팁 텍스트 교체
    document.getElementById('btnSchool').setAttribute('data-tooltip', translations.tooltipSchool[currentLang]);
    document.getElementById('btnCalendar').setAttribute('data-tooltip', translations.tooltipCalendar[currentLang]);
    document.getElementById('btnSettings').setAttribute('data-tooltip', translations.tooltipSettings[currentLang]);
}

async function fetchDailyMenu() {
    if (!savedSettings.school || !savedSettings.cafeteria) return;

    const contentDiv = document.querySelector('.content');
    // 로딩 문구도 번역
    // contentDiv.innerHTML = `<div style='text-align:center; color:#ccc; padding:20px;'>${translations.loading[currentLang]}</div>`;

    try {
        const data = await window.electronAPI.fetchDailyMenu(savedSettings.school, currentDateStr);
        lastApiData = data;
        renderMenu(data);

    } catch (error) {
        console.error(error);
        contentDiv.innerHTML = `
            <div style="padding:15px; text-align:center; color:#ff6b6b;">
                ${translations.serverError[currentLang]}<br>
                <span style="font-size:11px;">${translations.checkServer[currentLang]}</span>
            </div>`;
        sendHeight();
    }
}

// 2. 날짜 텍스트 생성 (한국어/영어 분기)
function getRelativeDateTitle(dateString) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const [year, month, day] = dateString.split('-').map(Number);
    const targetDate = new Date(year, month - 1, day);
    
    const diffTime = targetDate - today;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    
    // 날짜 포맷 (한국: 1/16, 영어: Jan 16)
    const shortDateKo = `${month}/${day}`;
    const shortDateEn = targetDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    if (currentLang === 'en') {
        // 영어 날짜 표기
        if (diffDays === 0) return `${translations.today[currentLang]} (${shortDateEn})`;
        if (diffDays === -1) return `${translations.yesterday[currentLang]} (${shortDateEn})`;
        if (diffDays === 1) return `${translations.tomorrow[currentLang]} (${shortDateEn})`;
        // "Menu for Jan 16"
        return `${translations.dayAfterTmrrw[currentLang]} ${shortDateEn}`;
    } else {
        // 한국어 날짜 표기
        if (diffDays === 0) return `${translations.today[currentLang]} (${shortDateKo})`;
        if (diffDays === -1) return `${translations.yesterday[currentLang]} (${shortDateKo})`;
        if (diffDays === 1) return `${translations.tomorrow[currentLang]} (${shortDateKo})`;
        if (diffDays === 2) return `${translations.dayAfterTmrrw[currentLang]} (${shortDateKo})`;
        return `${month}월 ${day}일${translations.menuFor[currentLang]}`;
    }
}

// 🛠️ 메뉴 아이템 하나(카드)를 만드는 함수
// menu: API에서 받은 메뉴 객체 1개
// cafeteria: 식당 이름 (저장된 설정값)
// lang: 현재 언어 ('ko' or 'en')
function createMenuCard(menu, cafeteria, lang) {
    // 1. 메뉴 타입 텍스트 변환 (ex: LUNCH -> 중식)
    const typeInfo = menuTypeMap[menu.meal_type];
    const displayType = typeInfo ? typeInfo[lang] : menu.meal_type;

    // 2. 메뉴 텍스트 줄바꿈 처리 (\n -> <br>)
    // map을 써서 각 줄 앞에 '- '를 붙여주는 센스!
    const formattedText = menu.menu_text
        .split('\n')
        .map(line => `- ${line}`)
        .join('<br>');

    // 3. 이미지 URL 안전 처리
    const safeImageUrl = menu.image_url_3d || "";

    // 4. HTML 조립 (Template Literal 사용)
    // onclick에서 문자열 넘길 때 따옴표('') 조심해야 해!
    return `
        <div class="menu-item" onclick="window.openViewer('${safeImageUrl}', '${menu.meal_type}', '${cafeteria}')">
            <div class="menu-title">[${displayType}] ${cafeteria}</div>
            <div class="menu-desc">${formattedText}</div>
        </div>
    `;
}

function renderMenu(apiData) {
    const contentDiv = document.querySelector('.content');
    
    // 1. 날짜 타이틀 가져오기
    const titleText = getRelativeDateTitle(currentDateStr);
    
    // 2. 현재 설정된 식당 찾기
    const myCafeteria = apiData.cafeterias.find(c => c.name === savedSettings.cafeteria);

    // 3. 메뉴 리스트 HTML 생성 (여기가 핵심!)
    let menuHtml = '';

    if (!myCafeteria || !myCafeteria.menus || myCafeteria.menus.length === 0) {
        // 메뉴 없을 때
        menuHtml = `<div class="menu-item"><div class="empty-msg">${translations.noMenu[currentLang]}</div></div>`;
    } else {
        // 메뉴 있을 때: map으로 변환 후 join으로 합치기
        menuHtml = myCafeteria.menus
            .map(menu => createMenuCard(menu, savedSettings.cafeteria, currentLang))
            .join('');
    }

    // 4. 최종 렌더링
    contentDiv.innerHTML = `<h2 id="menuTitle">${titleText}</h2>` + menuHtml;
    
    // 5. 높이 조절
    setTimeout(sendHeight, 50);
}

function updateHeaderUI(schoolName, cafeteriaName) {
    const titleElement = document.querySelector('.app-title');
    if (titleElement) {
        // 학교/식당 이름은 API 데이터라 번역이 어렵지만, 
        // 필요하면 여기서도 분기 처리 가능 (일단은 그대로 둠)
        titleElement.innerText = `${schoolName} (${cafeteriaName})`;
    }
}

function sendHeight() {
    const container = document.querySelector('.widget-container');
    if(container) {
        const height = container.offsetHeight; 
        window.electronAPI.send('resize-me', height + 10);
    }
}

function openSettings() { window.electronAPI.send('open-settings'); }
function openSchoolSetup() { window.electronAPI.send('open-school-setup'); }
function openCalendar() { window.electronAPI.send('open-calendar', currentDateStr); }

// 1. openViewer 함수 수정: (타이틀 통째로 받지 말고, 타입과 식당 이름을 따로 받음)
function openViewer(imageUrl, mealType, cafeteriaName) {
    const safeImageUrl = imageUrl || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c";
    // 🔴 title 대신 mealType, cafeteriaName을 보냄
    window.electronAPI.send('open-3d-viewer', { 
        imageUrl: safeImageUrl, 
        mealType: mealType, 
        cafeteriaName: cafeteriaName 
    });
}

window.openSettings = openSettings;
window.openSchoolSetup = openSchoolSetup;
window.openCalendar = openCalendar;
window.openViewer = openViewer;

// ⚡ 디바운싱 적용
let resizeTimer;

const resizeObserver = new ResizeObserver(() => {
    // 1. 변화가 감지되면 기존 타이머 취소 (아직 보내지 마!)
    clearTimeout(resizeTimer);

    // 2. 0.1초(50ms) 뒤에 실행 예약
    resizeTimer = setTimeout(() => {
        sendHeight(); // 예약된 시간이 지나면 비로소 실행
    }, 50);
});

const widget = document.querySelector('.widget-container');
if (widget) resizeObserver.observe(widget);