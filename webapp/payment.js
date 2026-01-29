function buyBlock(blockId, price) {
    // Условная покупка
    fetch('/api/create_invoice', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({block_id: blockId, user_id: userId})
    }).then(res => res.json()).then(data => {
        if (data.ok) {
            alert('Покупка успешна (условно)!');
            location.reload();  // Рефреш для обновления блоков
        } else {
            alert('Ошибка покупки');
        }
    });
}

function buyAll(price) {
    // Условная покупка всех
    fetch('/api/create_invoice', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({all_blocks: true, user_id: userId})
    }).then(res => res.json()).then(data => {
        if (data.ok) {
            alert('Покупка всех блоков успешна (условно)!');
            location.reload();
        } else {
            alert('Ошибка покупки');
        }
    });
}