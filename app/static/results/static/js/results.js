// ==========================================
// ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКИ ДИНАМИЧЕСКОГО URL
// ==========================================

// Функция парсит test_id из URL (/results/425 -> 425) или из параметров (?test_id=425)
function getTestIdFromUrl() {
    const pathSegments = window.location.pathname.split('/');
    const resultsIndex = pathSegments.indexOf('results');

    if (resultsIndex !== -1 && pathSegments[resultsIndex + 1]) {
        const testId = parseInt(pathSegments[resultsIndex + 1], 10);
        if (!isNaN(testId)) return testId;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const paramId = parseInt(urlParams.get('test_id'), 10);

    return !isNaN(paramId) ? paramId : 1; // 1 — ID по умолчанию, если ничего не найдено
}

const TEST_ID = getTestIdFromUrl();
let currentPage = 1;
let totalPages = 1;
const LIMIT = 100; // Лимит записей на бэкенде для расчета абсолютного места

// ==========================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (УТИЛИТЫ)
// ==========================================

// Переводит ISO формат даты от БД в человеческий: ГГГГ.ММ.ДД ЧЧ:ММ:СС
function formatDateTime(dateString) {
    if (!dateString) return '';
    const d = new Date(dateString);
    const pad = (num) => String(num).padStart(2, '0');
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

// Формирует буквы для круглых аватарок участников
function getInitials(name, lastname) {
    return `${name ? name[0] : ''}${lastname ? lastname[0] : ''}`.toUpperCase() || '?';
}

// Перезапускает CSS-анимацию «вырастания» подиума без багов браузера
function forceTriggerDOMReflow(element) {
    void element.offsetWidth;
}

// Салют конфетти в фирменных цветах академии (стиль Kahoot)
function runKahootConfetti() {
    confetti({
        particleCount: 140,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#0f4c81', '#17a2b8', '#e83e8c', '#ffd700']
    });
    setTimeout(() => {
        confetti({ particleCount: 40, angle: 60, spread: 55, origin: { x: 0, y: 0.8 } });
    }, 200);
    setTimeout(() => {
        confetti({ particleCount: 40, angle: 120, spread: 55, origin: { x: 1, y: 0.8 } });
    }, 400);
}

// ==========================================
// ОСНОВНАЯ ЛОГИКА ЗАГРУЗКИ И РЕНДЕРИНГА
// ==========================================

async function loadResults(page) {
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const podiumContainer = document.getElementById('podium-container');

    // Показываем лоадер, скрываем старый контент
    loader.style.display = 'block';
    resultsContainer.style.display = 'none';
    if(page === 1) podiumContainer.style.display = 'none';

    try {
        // Динамический эндпоинт: берет текущий домен, где крутится страница (window.location.origin)
        const currentOrigin = window.location.origin;
        const apiUrl = `${currentOrigin}/api/results/${TEST_ID}?page=${page}`;

        const response = await fetch(apiUrl);
        const data = await response.json();

        totalPages = data.total_pages || 1;
        document.getElementById('test-title').innerText = data.test_name || 'Результаты';

        const participants = data.results || [];
        resultsContainer.innerHTML = '';

        // Если результатов совсем нет
        if (participants.length === 0) {
            resultsContainer.innerHTML = '<div style="text-align:center; padding:20px; color:gray;">Нет результатов</div>';
            loader.style.display = 'none';
            resultsContainer.style.display = 'block';
            updatePagination();
            return;
        }

        let startIndex = 0;

        // Логика подиума Kahoot для ПЕРВОЙ страницы
        if (page === 1) {
            podiumContainer.style.display = 'flex';

            const t1 = document.getElementById('top-1');
            const t2 = document.getElementById('top-2');
            const t3 = document.getElementById('top-3');

            // Сбрасываем старые анимации для корректного перезапуска
            t1.classList.remove('animate-place-1');
            t2.classList.remove('animate-place-2');
            t3.classList.remove('animate-place-3');

            // Наполнение 3 места
            if(participants[2]) {
                t3.style.visibility = 'visible';
                document.getElementById('name-3').innerText = `${participants[2].username} ${participants[2].lastname}`;
                document.getElementById('score-3').innerText = `${participants[2].score} б.`;
                document.getElementById('avatar-3').innerText = getInitials(participants[2].username, participants[2].lastname);
                forceTriggerDOMReflow(t3);
                t3.classList.add('animate-place-3');
            } else { t3.style.visibility = 'hidden'; }

            // Наполнение 2 места
            if(participants[1]) {
                t2.style.visibility = 'visible';
                document.getElementById('name-2').innerText = `${participants[1].username} ${participants[1].lastname}`;
                document.getElementById('score-2').innerText = `${participants[1].score} б.`;
                document.getElementById('avatar-2').innerText = getInitials(participants[1].username, participants[1].lastname);
                forceTriggerDOMReflow(t2);
                t2.classList.add('animate-place-2');
            } else { t2.style.visibility = 'hidden'; }

            // Наполнение 1 места
            if(participants[0]) {
                t1.style.visibility = 'visible';
                document.getElementById('name-1').innerText = `${participants[0].username} ${participants[0].lastname}`;
                document.getElementById('score-1').innerText = `${participants[0].score} б.`;
                document.getElementById('avatar-1').innerText = getInitials(participants[0].username, participants[0].lastname);
                forceTriggerDOMReflow(t1);
                t1.classList.add('animate-place-1');

                // Праздничный взрыв запускается ровно в момент анимации 1-го места
                setTimeout(runKahootConfetti, 1300);
            } else { t1.style.visibility = 'hidden'; }

            // На 1-й странице в нижний список идут участники, начиная с 4-го места
            startIndex = 3;
        } else {
            // На 2, 3 и т.д. страницах подиум скрыт, выводим всех списком
            podiumContainer.style.display = 'none';
        }

        // Рендеринг основного списка участников
        for (let i = startIndex; i < participants.length; i++) {
            const user = participants[i];

            // Расчет абсолютного места на фронтенде с учетом текущей страницы
            const absoluteRank = ((page - 1) * LIMIT) + i + 1;

            const itemHtml = `
                <div class="result-item">
                    <div class="rank">${absoluteRank}</div>
                    <div class="user-info">
                        <div class="user-name">${user.username} ${user.lastname}</div>
                        <div class="submit-time"><i class="far fa-clock"></i> ${formatDateTime(user.created_at)}</div>
                    </div>
                    <div class="score-badge">
                        <div class="score-value">${user.score}</div>
                        <div class="score-label">баллов</div>
                    </div>
                </div>
            `;
            resultsContainer.insertAdjacentHTML('beforeend', itemHtml);
        }

        // Переключаем видимость блоков
        loader.style.display = 'none';
        resultsContainer.style.display = 'block';
        updatePagination();

    } catch (error) {
        console.error("Ошибка при работе с API:", error);
        document.getElementById('test-title').innerText = "Ошибка загрузки результатов";
        loader.style.display = 'none';
    }
}

// Переключение и блокировка кнопок пагинации
function updatePagination() {
    document.getElementById('page-info').innerText = `Стр. ${currentPage} из ${totalPages}`;
    document.getElementById('prev-btn').disabled = (currentPage === 1);
    document.getElementById('next-btn').disabled = (currentPage === totalPages || totalPages === 0);
}

// Функция смены страницы (вызывается при кликах на кнопки в HTML)
function changePage(direction) {
    const targetPage = currentPage + direction;
    if (targetPage >= 1 && targetPage <= totalPages) {
        currentPage = targetPage;
        loadResults(currentPage);
    }
}

// Автоматический старт загрузки сразу после готовности DOM дерева
document.addEventListener('DOMContentLoaded', () => loadResults(currentPage));