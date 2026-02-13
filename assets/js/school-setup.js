const { SCHOOL_DB: schoolDB, UI_TEXT } = window.CONSTANTS; // ✅ window.CONSTANTS 사용
const translations = UI_TEXT.setup;

const input = document.getElementById('schoolInput');
const suggestions = document.getElementById('suggestions');
const cafSection = document.getElementById('cafeteriaSection');
const cafList = document.getElementById('cafeteriaList');

let selectedSchool = null;
let currentLang = 'ko';

let resizeTimer;

const observer = new ResizeObserver(() => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        const height = document.body.scrollHeight;
        window.electronAPI.send('resize-setup-window', height);
    }, 50);
});
observer.observe(document.body);


// 🏁 초기화 및 설정 로드
window.onload = () => {
    window.electronAPI.send('get-settings'); // ✅ 변경
};

// 📨 설정값 수신
window.electronAPI.on('load-settings', (data) => {
    // 1. 언어 설정 (기존 코드)
    if (data.language) {
        currentLang = data.language;
        applyTranslations(currentLang);
    }
    if (data.theme) {
        document.body.setAttribute('data-theme', data.theme);
    }

    // 2. ✨ [추가된 부분] 저장된 학교가 있다면 자동으로 선택 상태 만들기 ✨
    if (data.school) {
        // schoolDB에서 이름이 일치하는 학교 객체를 찾는다.
        const targetSchool = schoolDB.find(s => s.name === data.school);
        
        if (targetSchool) {
            // 마치 사용자가 클릭한 것처럼 selectSchool 함수를 호출해!
            selectSchool(targetSchool);

            // (선택 사항) 기왕이면 현재 설정된 식당까지 선택된 상태로 보여주면 더 완벽하겠지?
            if (data.cafeteria) {
                const chips = document.querySelectorAll('.chip');
                chips.forEach(chip => {
                    if (chip.innerText === data.cafeteria) {
                        chip.classList.add('selected');
                    }
                });
            }
        }
    } else {
        // 🔴 2. 학교가 설정 안 된 경우 -> 'initial-mode' 클래스 추가!
        // 이렇게 하면 min-height: 340px이 적용돼서 창이 큼지막하게 뜸
        document.body.classList.add('initial-mode');
        
        // 💡 팁: 검색창에 바로 포커스 주면 더 편하겠지?
        setTimeout(() => document.getElementById('schoolInput').focus(), 100);
    }
});

// 2. ✨ 실시간 테마 변경 감지 (추가)
window.electronAPI.on('theme-changed', (themeName) => {
    document.body.setAttribute('data-theme', themeName);
});

// 📨 실시간 언어 변경 감지
window.electronAPI.on('language-changed', (lang) => {
    currentLang = lang;
    applyTranslations(lang);
});

// 🛠️ 번역 적용
function applyTranslations(lang) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[key] && translations[key][lang]) {
            el.innerText = translations[key][lang];
        }
    });
    if (input) input.placeholder = translations.placeholder[lang];
}

// 검색 로직
input.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    if (!val) {
    suggestions.style.display = 'none';
    // 예전엔 여기서 updateWindowHeight() 불렀지만 이젠 필요 없음!
    return;
    }
    const matches = schoolDB.filter(s => s.name.toLowerCase().includes(val.toLowerCase()));
    renderSuggestions(matches);
});

function renderSuggestions(list) {
    suggestions.innerHTML = '';
    if (list.length === 0) {
    suggestions.style.display = 'none';
    } else {
    suggestions.style.display = 'block'; // 여기서 block 되는 순간 observer가 감지함
    list.forEach(school => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.innerText = school.name;
        div.onclick = () => selectSchool(school);
        suggestions.appendChild(div);
    });
    }
}

function selectSchool(school) {
    selectedSchool = school;
    input.value = school.name;
    suggestions.style.display = 'none'; // 여기서 사라질 때도 감지함
    
    renderCafeterias(school.cafeterias);
    cafSection.style.display = 'flex'; // 여기서 생길 때도 감지함
}

function renderCafeterias(list) {
    cafList.innerHTML = '';
    list.forEach(caf => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.innerText = caf;
    
    // 클릭 이벤트 핸들러 변경
    chip.onclick = function() {
        // 1. 시각적 효과 (선택됨 표시)
        // 사실 창이 바로 닫혀서 잘 안 보일 수도 있지만, 찰나의 피드백을 위해 남겨둬도 좋아.
        const currentSelected = document.querySelectorAll('.chip.selected');
        currentSelected.forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');

        // 2. 🚀 바로 저장하고 닫기! (원래 saveAndClose에 있던 로직)
        if (selectedSchool) {
            window.electronAPI.send('school-setup-complete', { // ✅ 변경
                school: selectedSchool.name,
                cafeteria: caf 
            });
        }
    };
    cafList.appendChild(chip);
    });
}