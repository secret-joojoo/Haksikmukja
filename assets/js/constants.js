// 📦 assets/js/constants.js
// require(Node.js) 방식이 아니라 브라우저 전역 변수 방식으로 선언!

window.CONSTANTS = {
    // 1. 공통 데이터
    MENU_TYPE_MAP: {
        "BREAKFAST": { ko: "조식", en: "Breakfast" },
        "BREAKFAST_1000": { ko: "천원의 아침밥", en: "₩1000 Breakfast" },
        "BREAKFAST_C": { ko: "조식 C코너", en: "Breakfast C" },
        "LUNCH": { ko: "중식", en: "Lunch" },
        "LUNCH_SPECIAL": { ko: "중식 일품", en: "Lunch Special" },
        "LUNCH_A": { ko: "중식 A코너", en: "Lunch A" },
        "LUNCH_B": { ko: "중식 B코너", en: "Lunch B" },
        "LUNCH_C": { ko: "중식 C코너", en: "Lunch C" },
        "LUNCH_D": { ko: "중식 D코너", en: "Lunch D" },
        "LUNCH_SELF": { ko: "중식 셀프", en: "Lunch Self" },
        "LUNCH_ORDER": { ko: "중식 주문", en: "Lunch Order" },
        "LUNCH_BUFFET": { ko: "중식 뷔페", en: "Lunch Buffet" },
        "LUNCH_FACULTY": { ko: "중식 (교직원)", en: "Lunch (Faculty)" },
        "LUNCH_TAKEOUT": { ko: "중식 Take-out", en: "Lunch Take-out" },
        "LUNCH_1F": { ko: "중식 1층", en: "Lunch 1F" },
        "LUNCH_2F": { ko: "중식 2층", en: "Lunch 2F" },
        "LUNCH_PLUS": { ko: "중식 플러스 메뉴", en: "LUNCH PLUS"},
        "DINNER": { ko: "석식", en: "Dinner" },
        "DINNER_SPECIAL": {ko: "석식 일품", en: "Dinner Special"},
        "DINNER_C": { ko: "석식 C코너", en: "Dinner C" },
        "DINNER_D": { ko: "석식 D코너", en: "Dinner D" },
        "DINNER_SELF": { ko: "석식 셀프", en: "Dinner Self" },
        "DINNER_ORDER": { ko: "석식 주문", en: "Dinner Order" },
        "DINNER_BUFFET": { ko: "석식 뷔페", en: "Dinner Buffet" },
        "DINNER_FACULTY": { ko: "석식 (교직원)", en: "Dinner (Faculty)" },
        "DINNER_TAKEOUT": { ko: "석식 Take-out", en: "Dinner Take-out" },
        "DINNER_PLUS": { ko: "석식 플러스 메뉴", en: "DINNER PLUS"},
        "PREMIUM_A": { ko: "고급식 A", en: "Premium A" },
        "PREMIUM_B": { ko: "고급식 B", en: "Premium B" },
    },

    // 2. 학교 데이터
    SCHOOL_DB: [
        { name: "KAIST", cafeterias: ["카이마루", "서맛골", "교수회관", "문지캠퍼스", "화암 기숙사식당"] },
        { name: "서울대학교", cafeterias: ["학생회관식당", "자하연식당 3층", "자하연식당 2층", "예술계식당", "두레미담", "동원관식당", "기숙사식당", "3식당", "302동식당", "301동식당"] },
        { name: "이화여자대학교", cafeterias: ["I-House 학생식당", "진·선·미관 식당", "공대식당", "한우리집 식당", "E-House 식당(201동)"]},
        { name: "충남대학교", cafeterias: ["제1학생회관", "제2학생회관", "제3학생회관", "제4학생회관", "생활과학대학"]},
        { name: "서울시립대학교", cafeterias: ["학생회관 1층", "이룸라운지", "양식당", "자연과학관"] }
    ],

    // 3. 번역 데이터
    UI_TEXT: {
        main: {
            loading: { ko: "불러오는 중...", en: "Loading..." },
            serverError: { ko: "서버 연결 실패", en: "Server Error" },
            checkServer: { ko: "백엔드가 켜져 있나요?", en: "Is the backend server running?" },
            noSchool: { ko: "학교를 설정해주세요!", en: "Please set your school!" },
            noMenu: { ko: "메뉴가 없습니다.", en: "No menu available." },
            tooltipSchool: { ko: "학교 설정", en: "School Setup" },
            tooltipCalendar: { ko: "캘린더", en: "Calendar" },
            tooltipSettings: { ko: "설정", en: "Settings" },
            today: { ko: "오늘의 학식", en: "Today's Menu" },
            yesterday: { ko: "어제의 학식", en: "Yesterday's Menu" },
            tomorrow: { ko: "내일의 학식", en: "Tomorrow's Menu" },
            dayAfterTmrrw: { ko: "모레의 학식", en: "Menu for" },
            menuFor: { ko: "의 학식", en: "'s Menu" }
        },
        settings: {
            settingsTitle: { ko: "설정", en: "Settings" },
            langSetting: { ko: "언어 설정 (Language)", en: "Language" },
            fontSize: { ko: "글자 크기 설정", en: "Font Size" }, 
            fontSmall: { ko: "소", en: "S" },
            fontMedium: { ko: "중", en: "M" },
            fontLarge: { ko: "대", en: "L" },
            opacity: { ko: "투명도 조절", en: "Transparency" }, 
            opacityLabel: { ko: "투명도", en: "Transparency" },
            theme: { ko: "테마 설정", en: "Theme" },
            themeDark: { ko: "다크", en: "Dark" },
            themeLight: { ko: "라이트", en: "Light" },
            themeNavy: { ko: "네이비", en: "Navy" },
            themePink: { ko: "핑크", en: "Pink" },
            startupSetting: { ko: "윈도우 시작 시 자동 실행", en: "Run on Startup" },
            contact: { ko: "고객 문의", en: "Contact / Report" },
            quit: { ko: "종료하기", en: "Quit App" },
            selectTopicPlaceholder: { ko: "주제를 선택해주세요", en: "Select a topic" },
            topicFeature: { ko: "기능 추가 제안", en: "Feature Request" },
            topicBug: { ko: "앱 버그 제보", en: "App Bug Report" },
            topicError: { ko: "메뉴/가격 오류 제보", en: "Menu/Price Error" },
            topicSchool: { ko: "학교/식당 추가 요청", en: "Add School/Cafeteria" },
            topicTypo: { ko: "번역/오타 제보", en: "Translation/Typo Fix" },
            topicEtc: { ko: "기타", en: "Others" },
            contactContentPlaceholder: { ko: "내용을 입력해주세요.", en: "Please enter details." },
            submitInquiryBtn: { ko: "문의하기", en: "Submit" },
            alertTitle: { ko: "알림", en: "Notice" },
            confirmBtn: { ko: "확인", en: "OK" },
            msgSelectTopic: { ko: "문의 주제를 먼저 선택해주세요!", en: "Please select a topic first!" },
            msgEnterContent: { ko: "내용을 입력해주세요!", en: "Please enter the content!" },
            msgSending: { ko: "전송 중...", en: "Sending..." },
            msgSuccess: { ko: "소중한 의견 감사합니다!\n개발자에게 전달되었습니다.", en: "Thank you!\nYour inquiry has been sent." },
            msgFail: { ko: "전송 실패.\n서버 상태를 확인해주세요.", en: "Failed to send.\nPlease check server status." },
            msgNetworkError: { ko: "서버와 통신할 수 없습니다.", en: "Network Error." }
        },
        viewer: {
            loading: { ko: "메뉴 로딩 중..", en: "Loading menu.." },
            guide: { ko: "좌클릭 드래그: 이동  /  휠: 확대·축소  /  더블클릭: 초기화", en: "Drag: Pan  /  Wheel: Zoom  /  Double-click: Reset" },
            btnSave: { ko: "JPG 저장", en: "Save as JPG" },
            msgLoading: { ko: "이미지 불러오는 중..", en: "Loading image.." },
            msgFail: { ko: "이미지를 불러올 수 없습니다.", en: "Failed to load image." }
        },
        setup: {
            windowTitle: { ko: "학교 및 식당 설정", en: "School & Cafeteria Setup" },
            labelSearch: { ko: "학교 검색", en: "Search School" },
            labelCafeteria: { ko: "식당 선택", en: "Select Cafeteria" },
            placeholder: { ko: "학교 이름을 입력하세요 (예: KAIST)", en: "Enter school name (e.g. KAIST)" }
        },
        calendar: {
            windowTitle: { ko: "날짜 선택", en: "Select Date" },
            yesterday: { ko: "어제", en: "Yesterday" },
            today: { ko: "오늘", en: "Today" },
            tomorrow: { ko: "내일", en: "Tomorrow" },
            dayAfter: { ko: "모레", en: "Day after Tmr" },
            days: {
                ko: ['일', '월', '화', '수', '목', '금', '토'],
                en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            }
        },
        update: {
            updateTitle: { ko: "학식묵자 업데이트", en: "Update Available" },
            updateHeader: { ko: "새로운 버전이 출시되었습니다!", en: "New version is available!" },
            releaseNotesLabel: { ko: "패치 내역", en: "Release Notes" },
            btnLater: { ko: "나중에", en: "Later" },
            btnUpdate: { ko: "업데이트", en: "Update" },
            btnRestart: { ko: "재시작 및 설치", en: "Restart & Install" },
            msgNoNotes: { ko: "세부 패치 내역이 없습니다.<br>- 버그 수정 및 성능 향상", en: "No release notes available.<br>- Bug fixes and performance improvements" },
            msgDownloading: { ko: "다운로드 중...", en: "Downloading..." },
            msgDownloadComplete: { ko: "다운로드 완료! 재시작해주세요.", en: "Download complete! Please restart." },
            msgInstallReady: { ko: "설치 준비 완료!", en: "Ready to install!" }
        }
    }
};