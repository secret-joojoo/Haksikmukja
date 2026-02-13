const { UI_TEXT } = window.CONSTANTS;
const translations = UI_TEXT.calendar;

let currentLang = 'ko'; 
let selectedDate = null;

let resizeTimer;

const observer = new ResizeObserver(() => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        const height = document.body.scrollHeight;
        window.electronAPI.send('resize-calendar-window', height);
    }, 50);
});
observer.observe(document.body);


// 🏁 초기화 및 설정 로드
window.onload = () => {
    window.electronAPI.send('get-settings');
};

window.electronAPI.on('load-settings', (data) => {
    if (data.language) {
        currentLang = data.language;
        updateStaticText();
    }
    if (selectedDate) renderCalendar(selectedDate);
    if (data.theme) document.body.setAttribute('data-theme', data.theme);
});

window.electronAPI.on('set-initial-date', (dateStr) => {
    selectedDate = dateStr;
    renderCalendar(dateStr);
});

// ✨ 실시간 변경 감지
window.electronAPI.on('theme-changed', (themeName) => {
    document.body.setAttribute('data-theme', themeName);
});

window.electronAPI.on('language-changed', (lang) => {
    currentLang = lang;
    updateStaticText();
    if (selectedDate) renderCalendar(selectedDate);
});

function updateStaticText() {
    const titleEl = document.querySelector('[data-i18n="windowTitle"]');
    if (titleEl) titleEl.innerText = translations.windowTitle[currentLang];
}

function renderCalendar(selectedDateStr) {
    const dateList = document.getElementById('dateList');
    if (!dateList) return;

    dateList.innerHTML = '';
    const today = new Date();
    const daysArray = translations.days[currentLang];

    for (let i = -1; i <= 2; i++) {
        const targetDate = new Date(today);
        targetDate.setDate(today.getDate() + i);

        const y = targetDate.getFullYear();
        const m = String(targetDate.getMonth() + 1).padStart(2, '0');
        const d = String(targetDate.getDate()).padStart(2, '0');
        const targetDateStr = `${y}-${m}-${d}`;

        const btn = document.createElement('div');
        
        let classes = 'date-btn';
        if (i === 0) classes += ' today';
        if (targetDateStr === selectedDateStr) classes += ' selected';
        btn.className = classes;

        let label = '';
        if (i === -1) label = translations.yesterday[currentLang];
        else if (i === 0) label = translations.today[currentLang];
        else if (i === 1) label = translations.tomorrow[currentLang];
        else if (i === 2) label = translations.dayAfter[currentLang];
        else label = daysArray[targetDate.getDay()] + (currentLang === 'ko' ? '요일' : '');

        let dateText = '';
        if (currentLang === 'en') {
            const monthName = targetDate.toLocaleString('en-US', { month: 'short' });
            const dateNum = targetDate.getDate();
            const dayName = daysArray[targetDate.getDay()];
            dateText = `${monthName} ${dateNum} (${dayName})`;
        } else {
            const month = targetDate.getMonth() + 1;
            const dateNum = targetDate.getDate();
            const dayName = daysArray[targetDate.getDay()];
            dateText = `${month}. ${dateNum} (${dayName})`;
        }

        btn.innerHTML = `
            <span class="date-text">${dateText}</span>
            <span class="day-label">${label}</span>
        `;

        btn.onclick = () => {
            let displayStr = '';
            if(currentLang === 'en') {
                displayStr = targetDate.toLocaleString('en-US', { month: 'short', day: 'numeric' });
            } else {
                displayStr = `${targetDate.getMonth() + 1}월 ${targetDate.getDate()}일`;
            }
            window.electronAPI.send('date-selected', { date: targetDateStr, display: displayStr });
        };

        dateList.appendChild(btn);
    }
}