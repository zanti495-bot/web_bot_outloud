const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

let currentBlock = null;
let questions = [];
let currentIndex = 0;

async function loadBlocks() {
  const res = await fetch('/api/blocks');
  const blocks = await res.json();
  const list = document.getElementById('blocks-list');
  list.innerHTML = '';
  blocks.forEach(b => {
    const div = document.createElement('div');
    div.className = 'block-card';
    div.innerHTML = `<h3>${b.title}</h3><p>${b.is_paid ? 'Платный — ' + b.price + '₽' : 'Бесплатно'}</p>`;
    div.onclick = () => startBlock(b);
    list.appendChild(div);
  });
}

async function startBlock(block) {
  currentBlock = block;
  const res = await fetch(`/api/blocks/${block.id}/questions`);
  questions = await res.json();

  if (block.is_paid && !await hasPurchased(block.id)) {
    tg.showAlert("Этот блок платный. Купить?");
    return;
  }

  document.getElementById('blocks-list').style.display = 'none';
  document.getElementById('question-screen').style.display = 'block';
  showQuestion(0);
}

function showQuestion(idx) {
  if (idx < 0 || idx >= questions.length) return;
  currentIndex = idx;
  document.getElementById('question-text').innerText = questions[idx].text;

  // отправка просмотра
  fetch('/api/view', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question_id: questions[idx].id})
  });
}

// Hammer.js свайпы
const hammer = new Hammer(document.getElementById('question-screen'));
hammer.on('swipeleft', () => showQuestion(currentIndex + 1));
hammer.on('swiperight', () => showQuestion(currentIndex - 1));
document.getElementById('question-screen').addEventListener('click', () => showQuestion(currentIndex + 1));

async function hasPurchased(blockId) {
  // заглушка — в реальности запрос к /api/has_purchased
  return false;
}

loadBlocks();
