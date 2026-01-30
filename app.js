// app.js для Mini App (в static/app.js)
Telegram.WebApp.ready();
Telegram.WebApp.expand();

let currentBlock = null;
let questions = [];
let currentIndex = 0;

// Загрузка дизайна
fetch('/api/design').then(res => res.json()).then(design => {
    document.body.style.backgroundColor = design.background_color || '#fff';
    document.body.style.color = design.text_color || '#000';
    document.body.style.fontFamily = design.font_family || 'Arial';
});

// Загрузка блоков
fetch('/api/blocks').then(res => res.json()).then(blocks => {
    const container = document.getElementById('blocks');
    blocks.forEach(block => {
        const div = document.createElement('div');
        div.textContent = block.name + (block.is_paid ? ' (Платный)' : '');
        div.onclick = () => loadBlock(block.id, block.is_paid);
        container.appendChild(div);
    });
});

async function loadBlock(blockId, isPaid) {
    const userId = Telegram.WebApp.initDataUnsafe.user.id;
    if (isPaid) {
        const purchased = await fetch(`/api/check_purchase/${userId}/${blockId}`).then(res => res.json()).then(d => d.purchased);
        if (!purchased) {
            if (confirm('Купить блок?')) {
                fetch('/api/purchase', {method: 'POST', body: JSON.stringify({user_id: userId, block_id: blockId}), headers: {'Content-Type': 'application/json'}});
            } else return;
        }
    }
    fetch(`/api/questions/${blockId}`).then(res => res.json()).then(qs => {
        questions = qs;
        currentIndex = 0;
        showQuestion();
    });
}

function showQuestion() {
    const questionElem = document.getElementById('question');
    questionElem.textContent = questions[currentIndex].text;
    fetch('/api/view', {method: 'POST', body: JSON.stringify({user_id: Telegram.WebApp.initDataUnsafe.user.id, question_id: questions[currentIndex].id}), headers: {'Content-Type': 'application/json'}});
}

// Свайпы с Hammer.js
const hammertime = new Hammer(document.body);
hammertime.on('swipeleft', () => {
    if (currentIndex < questions.length - 1) currentIndex++;
    showQuestion();
});
hammertime.on('swiperight', () => {
    if (currentIndex > 0) currentIndex--;
    showQuestion();
});

// Купить все
document.getElementById('buy_all').onclick = () => {
    fetch('/api/purchase', {method: 'POST', body: JSON.stringify({user_id: Telegram.WebApp.initDataUnsafe.user.id}), headers: {'Content-Type': 'application/json'}});
};
