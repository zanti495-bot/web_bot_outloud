const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

let currentBlockId = null;
let questions = [];
let currentIndex = 0;
let isPaid = false;

async function loadDesign() {
    try {
        const r = await fetch('/api/design');
        const d = await r.json();
        if (d.background_color) document.body.style.background = d.background_color;
        if (d.text_color)       document.body.style.color = d.text_color;
        if (d.font_family)      document.body.style.fontFamily = d.font_family;
    } catch (err) {
        console.warn('Не удалось загрузить дизайн', err);
    }
}

async function loadBlocks() {
    try {
        const r = await fetch('/api/blocks');
        const blocks = await r.json();
        const container = document.getElementById('blocks-list');
        container.innerHTML = '';

        blocks.forEach(b => {
            const el = document.createElement('div');
            el.className = 'block-card';
            el.innerHTML = `${b.name}${b.is_paid ? `<span class="paid"> • платный (${b.price} ₽)</span>` : ''}`;
            el.onclick = () => openBlock(b.id, b.is_paid, b.price);
            container.appendChild(el);
        });
    } catch (err) {
        tg.showAlert('Не удалось загрузить блоки');
        console.error(err);
    }
}

async function openBlock(blockId, paid, price) {
    const user = tg.initDataUnsafe.user;
    if (!user?.id) {
        tg.showAlert('Не удалось определить пользователя');
        return;
    }

    currentBlockId = blockId;
    isPaid = paid;

    if (paid) {
        try {
            const r = await fetch(`/api/check_purchase/${user.id}/${blockId}`);
            const data = await r.json();
            if (!data.purchased) {
                if (!confirm(`Купить блок за ${price} ₽? (демо)`)) return;
                await fetch('/api/purchase', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: user.id, block_id: blockId})
                });
            }
        } catch (err) {
            tg.showAlert('Ошибка проверки/покупки');
            console.error(err);
            return;
        }
    }

    try {
        const r = await fetch(`/api/questions/${blockId}`);
        questions = await r.json();

        if (questions.length === 0) {
            tg.showAlert('В блоке нет вопросов');
            return;
        }

        currentIndex = 0;
        showQuestion();
        document.getElementById('blocks-screen').style.display = 'none';
        document.getElementById('question-screen').style.display = 'flex';
    } catch (err) {
        tg.showAlert('Не удалось загрузить вопросы');
        console.error(err);
    }
}

function showQuestion() {
    if (!questions[currentIndex]) return;

    document.getElementById('question-text').textContent = questions[currentIndex].text;
    document.getElementById('progress').textContent = `${currentIndex + 1} / ${questions.length}`;

    // Логируем просмотр
    fetch('/api/view', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: tg.initDataUnsafe.user.id,
            question_id: questions[currentIndex].id
        })
    }).catch(console.error);

    // Активация/деактивация кнопок
    document.getElementById('btn-prev').disabled = currentIndex === 0;
    document.getElementById('btn-next').disabled = currentIndex === questions.length - 1;
}

function next() {
    if (currentIndex < questions.length - 1) {
        currentIndex++;
        showQuestion();
    }
}

function prev() {
    if (currentIndex > 0) {
        currentIndex--;
        showQuestion();
    }
}

// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadDesign();
    loadBlocks();

    document.getElementById('btn-next')?.addEventListener('click', next);
    document.getElementById('btn-prev')?.addEventListener('click', prev);

    document.getElementById('buy-all')?.addEventListener('click', async () => {
        const uid = tg.initDataUnsafe.user?.id;
        if (!uid) return;
        await fetch('/api/purchase', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: uid})
        });
        tg.showAlert('Все блоки разблокированы (демо-режим)');
    });

    // Hammer.js свайпы
    if (typeof Hammer !== 'undefined') {
        const hammer = new Hammer(document.getElementById('question-screen'));
        hammer.get('swipe').set({ direction: Hammer.DIRECTION_HORIZONTAL });

        hammer.on('swipeleft', next);
        hammer.on('swiperight', prev);

        console.log('Hammer.js инициализирован');
    } else {
        console.warn('Hammer.js НЕ загружен!');
    }
});
