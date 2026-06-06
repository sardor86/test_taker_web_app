
function getTestIdFromUrl() {
    const pathSegments = window.location.pathname.split('/');
    const resultsIndex = pathSegments.indexOf('results');

    if (resultsIndex !== -1 && pathSegments[resultsIndex + 1]) {
        const testId = parseInt(pathSegments[resultsIndex + 1], 10);
        if (!isNaN(testId)) return testId;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const paramId = parseInt(urlParams.get('test_id'), 10);

    return !isNaN(paramId) ? paramId : 1;
}

const TEST_ID = getTestIdFromUrl();
let currentPage = 1;
let totalPages = 1;
const LIMIT = 100;


function formatDateTime(dateString) {
    if (!dateString) return '';

    if (!dateString.endsWith('Z') && !dateString.includes('+')) {
        dateString += 'Z';
    }

    let rawMs = Date.parse(dateString);
    if (isNaN(rawMs)) return '';

    const uzbMs = rawMs + (5 * 60 * 60 * 1000);
    const d = new Date(uzbMs);

    const pad = (num) => String(num).padStart(2, '0');

    const year = d.getUTCFullYear();
    const month = pad(d.getUTCMonth() + 1);
    const day = pad(d.getUTCDate());
    const hours = pad(d.getUTCHours());
    const minutes = pad(d.getUTCMinutes());
    const seconds = pad(d.getUTCSeconds());

    return `${year}.${month}.${day} ${hours}:${minutes}:${seconds}`;
}

function getInitials(name, lastname) {
    return `${name ? name[0] : ''}${lastname ? lastname[0] : ''}`.toUpperCase() || '?';
}

function forceTriggerDOMReflow(element) {
    void element.offsetWidth;
}

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


async function loadResults(page) {
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const podiumContainer = document.getElementById('podium-container');

    loader.style.display = 'block';
    resultsContainer.style.display = 'none';
    if(page === 1) podiumContainer.style.display = 'none';

    try {
        const currentOrigin = window.location.origin;
        const apiUrl = `${currentOrigin}/api/results/${TEST_ID}?page=${page}`;

        const response = await fetch(apiUrl);
        const data = await response.json();

        totalPages = data.total_pages || 1;
        document.getElementById('test-title').innerText = data.test_name || 'Natijalar';

        const participants = data.results || [];
        resultsContainer.innerHTML = '';

        if (participants.length === 0) {
            resultsContainer.innerHTML = '<div style="text-align:center; padding:20px; color:gray;">Natijalar topilmadi</div>';
            loader.style.display = 'none';
            resultsContainer.style.display = 'block';
            updatePagination();
            return;
        }

        let startIndex = 0;

        if (page === 1) {
            podiumContainer.style.display = 'flex';

            const t1 = document.getElementById('top-1');
            const t2 = document.getElementById('top-2');
            const t3 = document.getElementById('top-3');

            t1.classList.remove('animate-place-1');
            t2.classList.remove('animate-place-2');
            t3.classList.remove('animate-place-3');

            if(participants[2]) {
                t3.style.visibility = 'visible';
                document.getElementById('name-3').innerText = `${participants[2].username} ${participants[2].lastname}`;
                document.getElementById('score-3').innerText = `${participants[2].score} ball`;
                document.getElementById('avatar-3').innerText = getInitials(participants[2].username, participants[2].lastname);
                forceTriggerDOMReflow(t3);
                t3.classList.add('animate-place-3');
            } else { t3.style.visibility = 'hidden'; }

            if(participants[1]) {
                t2.style.visibility = 'visible';
                document.getElementById('name-2').innerText = `${participants[1].username} ${participants[1].lastname}`;
                document.getElementById('score-2').innerText = `${participants[1].score} ball`;
                document.getElementById('avatar-2').innerText = getInitials(participants[1].username, participants[1].lastname);
                forceTriggerDOMReflow(t2);
                t2.classList.add('animate-place-2');
            } else { t2.style.visibility = 'hidden'; }

            if(participants[0]) {
                t1.style.visibility = 'visible';
                document.getElementById('name-1').innerText = `${participants[0].username} ${participants[0].lastname}`;
                document.getElementById('score-1').innerText = `${participants[0].score} ball`;
                document.getElementById('avatar-1').innerText = getInitials(participants[0].username, participants[0].lastname);
                forceTriggerDOMReflow(t1);
                t1.classList.add('animate-place-1');

                setTimeout(runKahootConfetti, 1300);
            } else { t1.style.visibility = 'hidden'; }

            startIndex = 3;
        } else {
            podiumContainer.style.display = 'none';
        }

        for (let i = startIndex; i < participants.length; i++) {
            const user = participants[i];
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
                        <div class="score-label">ball</div>
                    </div>
                </div>
            `;
            resultsContainer.insertAdjacentHTML('beforeend', itemHtml);
        }

        loader.style.display = 'none';
        resultsContainer.style.display = 'block';
        updatePagination();

    } catch (error) {
        console.error("Xatolik:", error);
        document.getElementById('test-title').innerText = "Ma'lumot yuklashda xatolik";
        loader.style.display = 'none';
    }
}

function updatePagination() {
    document.getElementById('page-info').innerText = `Sahifa: ${currentPage} / ${totalPages}`;
    document.getElementById('prev-btn').disabled = (currentPage === 1);
    document.getElementById('next-btn').disabled = (currentPage === totalPages || totalPages === 0);
}

function changePage(direction) {
    const targetPage = currentPage + direction;
    if (targetPage >= 1 && targetPage <= totalPages) {
        currentPage = targetPage;
        loadResults(currentPage);
    }
}

document.addEventListener('DOMContentLoaded', () => loadResults(currentPage));