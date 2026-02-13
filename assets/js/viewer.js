const { MENU_TYPE_MAP: menuTypeMap, UI_TEXT } = window.CONSTANTS;
const translations = UI_TEXT.viewer;

let currentLang = 'ko';
let currentMealType = null;
let currentCafeteria = null;

window.onload = () => {
    window.electronAPI.send('get-settings');
};

window.electronAPI.on('load-settings', (data) => {
    if (data.language) {
        currentLang = data.language;
        applyTranslations(currentLang);
        updateTitle();
    }
    if (data.theme) document.body.setAttribute('data-theme', data.theme);
});

window.electronAPI.on('theme-changed', (themeName) => {
    document.body.setAttribute('data-theme', themeName);
});

window.electronAPI.on('language-changed', (lang) => {
    currentLang = lang;
    applyTranslations(lang);
    updateTitle();
});

function applyTranslations(lang) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (el.id === 'menuName' && currentMealType) return;
        if (translations[key] && translations[key][lang]) {
            el.innerText = translations[key][lang];
        }
    });
}

function updateTitle() {
    if (!currentMealType || !currentCafeteria) return;
    const typeInfo = menuTypeMap[currentMealType];
    const displayType = typeInfo ? typeInfo[currentLang] : currentMealType;
    document.getElementById('menuName').innerText = `[${displayType}] ${currentCafeteria}`;
    document.getElementById('menuName').removeAttribute('data-i18n');
}

// ... (위쪽 번역 코드 등은 동일) ...

// --- 2D 뷰어 로직 ---
const img = document.getElementById('targetImage');
const container = document.getElementById('canvas-container');
const loader = document.getElementById('loading-indicator');

let state = {
    scale: 1, panning: false,
    pointX: 0, pointY: 0,
    startX: 0, startY: 0
};

window.electronAPI.on('load-3d-image', (data) => {
    currentMealType = data.mealType;
    currentCafeteria = data.cafeteriaName;
    updateTitle();

    img.style.display = 'none';
    loader.style.display = 'block';
    loader.innerText = translations['msgLoading'][currentLang];

    img.src = data.imageUrl;

    img.onload = () => {
        loader.style.display = 'none';
        img.style.display = 'block';
        
        // 🔴 [추가] 이미지 원본 비율 유지하면서 초기 크기 설정
        // 컨테이너의 90% 크기로 맞춤
        const containerRatio = container.clientWidth / container.clientHeight;
        const imgRatio = img.naturalWidth / img.naturalHeight;
        
        if (containerRatio > imgRatio) {
            img.style.height = (container.clientHeight * 0.9) + 'px';
            img.style.width = 'auto';
        } else {
            img.style.width = (container.clientWidth * 0.9) + 'px';
            img.style.height = 'auto';
        }

        resetView(); // 중앙 정렬 실행
    };

    img.onerror = () => {
        loader.innerText = translations['msgFail'][currentLang];
        loader.style.color = "var(--danger-color)";
    };
});

function setTransform() {
    img.style.transform = `translate(${state.pointX}px, ${state.pointY}px) scale(${state.scale})`;
}

// 🔴 [핵심 수정] 스마트 줌 (마우스 커서 위치 기준 확대)
container.onwheel = function (e) {
    e.preventDefault();
    if(img.style.display === 'none') return;

    // 1. 현재 마우스 위치 (컨테이너 기준)
    const rect = container.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    // 2. 휠 방향에 따른 스케일 변화량 계산
    const delta = -e.deltaY;
    const oldScale = state.scale;
    let newScale = oldScale * (delta > 0 ? 1.1 : 0.9);

    // 3. 줌 제한 (0.1배 ~ 10배)
    newScale = Math.min(Math.max(0.1, newScale), 10);

    // 4. ✨ 위치 보정 공식 ✨
    // (마우스위치 - 기존위치) * (확대비율) 만큼을 빼줘야 마우스가 그 자리에 고정됨
    state.pointX = mx - (mx - state.pointX) * (newScale / oldScale);
    state.pointY = my - (my - state.pointY) * (newScale / oldScale);
    
    state.scale = newScale;
    setTransform();
};

container.onmousedown = function (e) {
    if(img.style.display === 'none') return;
    e.preventDefault();
    state.startX = e.clientX - state.pointX;
    state.startY = e.clientY - state.pointY;
    state.panning = true;
    container.style.cursor = "grabbing"; // 커서 변경
};

container.onmouseup = function (e) { 
    e.preventDefault(); 
    state.panning = false; 
    container.style.cursor = "grab"; 
};

container.onmouseleave = function (e) { 
    state.panning = false; 
    container.style.cursor = "grab"; 
};

container.onmousemove = function (e) {
    e.preventDefault();
    if (!state.panning) return;
    state.pointX = e.clientX - state.startX;
    state.pointY = e.clientY - state.startY;
    setTransform();
};

// 🔴 [수정] 초기화: 화면 정중앙에 배치
function resetView() {
    state.scale = 1;
    
    // 이미지를 컨테이너 정중앙에 놓는 좌표 계산
    // (컨테이너너비 - 이미지너비) / 2
    state.pointX = (container.clientWidth - img.offsetWidth) / 2;
    state.pointY = (container.clientHeight - img.offsetHeight) / 2;
    
    setTransform();
}

function toggleMaximize() { window.electronAPI.send('viewer-toggle-maximize'); }

function saveAsJpg() {
    if(img.style.display === 'none') return;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // 저장할 땐 현재 보이는 크기대로
    canvas.width = img.offsetWidth * state.scale; 
    canvas.height = img.offsetHeight * state.scale;
    
    const bgColor = getComputedStyle(document.body).getPropertyValue('--bg-color') || '#222';
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 현재 위치 그대로 그리기 (잘린 부분은 저장 안 됨 - 화면 캡처 방식)
    // 만약 원본 전체를 저장하고 싶으면 로직을 바꿔야 함 (현재는 화면 보이는 대로 저장)
    ctx.drawImage(img, state.pointX, state.pointY, img.offsetWidth * state.scale, img.offsetHeight * state.scale);
    
    const dataURL = canvas.toDataURL("image/jpeg", 0.9);
    window.electronAPI.send('save-captured-image', dataURL);
}

window.toggleMaximize = toggleMaximize;
window.saveAsJpg = saveAsJpg;
window.resetView = resetView;