// static/app.js — логика Telegram Mini App

const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

let currentBlockId = null;
let questions = [];
let currentQuestionIndex = 0;
let isPaidBlock = false;

// Применение дизайна из БД
async function applyDesign() {
    try {
        const res = await fetch('/api/design');
        const design = await res.json();

        if (design.background_color) {
            document.body.style.backgroundColor = design.background_color;
        }
        if (design.text_color) {
            document.body.style.color = design.text_color;
        }
        if (design.font_family) {
            document.body.style.fontFamily = design.font_family;
        }
    } catch (e) {
        console.error('Ошибка загрузки дизайна:', e);
    }
}

// Загрузка списка блоков
async function loadBlocks() {
    try {
        const res = await fetch('/api/blocks');
        const blocks = await res.json();

        const container = document.getElementById('blocks-list');
        if (!container) return;

        container.innerHTML = '';

        blocks.forEach(block => {
            const card = document.createElement('div');
            card.className = 'block-card';
            card.innerHTML = `
                <h3>${block.name}</h3>
                ${block.is_paid ? `<span class="paid-badge">Платный · ${block.price} ₽</span>` : '<span class="free-badge">Бесплатно</span>'}
            `;
            card.onclick = () => openBlock(block.id, block.is_paid, block.price);
            container.appendChild(card);
        });
    } catch (e) {
        console.error('Ошибка загрузки блоков:', e);
    }
}

// Открытие блока (проверка покупки + загрузка вопросов)
async function openBlock(blockId, isPaid, price) {
    const user = tg.initDataUnsafe.user;
    if (!user || !user.id) {
        tg.showAlert('Не удалось определить пользователя');
        return;
    }

    currentBlockId = blockId;
    isPaidBlock = isPaid;

    if (isPaid) {
        try {
            const res = await fetch(`/api/check_purchase/${user.id}/${blockId}`);
            const data = await res.json();

            if (!data.purchased) {
                const confirmed = confirm(`Купить блок за ${price} ₽?`);
                if (!confirmed) return;

                // Здесь в будущем будет интеграция с ЮKassa / Telegram Payments
                // Пока просто условная покупка
                await fetch('/api/purchase', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: user.id, block_id: blockId })
                });
            }
        } catch (e) {
            tg.showAlert('Ошибка проверки покупки');
            return;
        }
    }

    // Загружаем вопросы
    try {
        const res = await fetch(`/api/questions/${blockId}`);
        questions = await res.json();

        if (questions.length === 0) {
            tg.showAlert('В этом блоке пока нет вопросов');
            return;
        }

        currentQuestionIndex = 0;
        showCurrentQuestion();
        document.getElementById('blocks-screen').style.display = 'none';
        document.getElementById('question-screen').style.display = 'block';
    } catch (e) {
        tg.showAlert('Ошибка загрузки вопросов');
    }
}

// Показ текущего вопроса
function showCurrentQuestion() {
    if (!questions[currentQuestionIndex]) return;

    const qText = document.getElementById('question-text');
    const progress = document.getElementById('progress');

    qText.textContent = questions[currentQuestionIndex].text;
    progress.textContent = `${currentQuestionIndex + 1} / ${questions.length}`;

    // Логируем просмотр
    fetch('/api/view', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: tg.initDataUnsafe.user.id,
            question_id: questions[currentQuestionIndex].id
        })
    }).catch(console.error);
}

// Навигация
function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        showCurrentQuestion();
    }
}

function prevQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showCurrentQuestion();
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    applyDesign();
    loadBlocks();

    // Кнопки навигации
    document.getElementById('btn-next')?.addEventListener('click', nextQuestion);
    document.getElementById('btn-prev')?.addEventListener('click', prevQuestion);

    // Поддержка свайпов (если подключен Hammer.js)
    if (typeof Hammer !== 'undefined') {
        const hammer = new Hammer(document.getElementById('question-screen'));
        hammer.get('swipe').set({ direction: Hammer.DIRECTION_HORIZONTAL });

        hammer.on('swipeleft', nextQuestion);
        hammer.on('swiperight', prevQuestion);
    }

    // Кнопка "Купить все блоки" (если есть)
    document.getElementById('buy-all')?.addEventListener('click', async () => {
        const userId = tg.initDataUnsafe.user.id;
        await fetch('/api/purchase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })  // block_id = null → все блоки
        });
        tg.showAlert('Все блоки разблокированы (условная покупка)');
    });
});
