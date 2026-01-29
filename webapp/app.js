const tg = window.Telegram.WebApp;
tg.expand();

let currentBlockId = null;
let questions = [];
let currentIndex = 0;
let design = {};

// Fetch design
fetch('/api/design')
    .then(res => res.json())
    .then(data => {
        design = data;
        document.body.style.backgroundColor = design.background_color;
        document.body.style.color = design.text_color;
        document.body.style.fontFamily = design.font_family;
    });

// Auth
const initData = tg.initDataUnsafe;
const userId = initData.user ? initData.user.id : null;
if (!userId) {
    alert('Ошибка авторизации');
}

// Fetch blocks
fetch(`/api/blocks?user_id=${userId}`)
    .then(res => res.json())
    .then(blocks => {
        const list = document.getElementById('blocks-list');
        blocks.forEach(block => {
            const li = document.createElement('li');
            if (block.accessible) {
                const btn = document.createElement('button');
                btn.textContent = block.name;
                btn.onclick = () => loadQuestions(block.id);
                li.appendChild(btn);
            } else {
                const buyBtn = document.createElement('button');
                buyBtn.textContent = `${block.name} - Купить за ${block.price} RUB`;
                buyBtn.onclick = () => buyBlock(block.id, block.price);
                li.appendChild(buyBtn);
            }
            list.appendChild(li);
        });
    });

// Buy all
document.getElementById('buy-all').onclick = () => {
    fetch('/api/all_blocks_price')
        .then(res => res.json())
        .then(data => buyAll(data.price));
};

// Load questions
function loadQuestions(blockId) {
    currentBlockId = blockId;
    fetch(`/api/questions?block_id=${blockId}`)
        .then(res => res.json())
        .then(qs => {
            questions = qs;
            currentIndex = 0;
            showCard();
            document.getElementById('menu').style.display = 'none';
            document.getElementById('cards').style.display = 'block';
        });
}

function showCard() {
    if (currentIndex >= questions.length) {
        document.querySelector('.card').innerText = 'Конец блока';
        document.getElementById('next').style.display = 'none';
        document.getElementById('back-to-menu').style.display = 'block';
        return;
    }
    const card = document.querySelector('.card');
    card.innerText = questions[currentIndex].text;
    fetch('/api/log_view', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: userId, question_id: questions[currentIndex].id})
    });
}

// Swipe with Hammer.js
const cardElement = document.querySelector('.card');
const hammer = new Hammer(cardElement);
hammer.on('swipeleft swiperight', () => {
    currentIndex++;
    showCard();
});

// Next button
document.getElementById('next').onclick = () => {
    currentIndex++;
    showCard();
};

// Back to menu
document.getElementById('back-to-menu').onclick = () => {
    document.getElementById('menu').style.display = 'block';
    document.getElementById('cards').style.display = 'none';
};