// カードのボタンクリック時の処理
document.querySelectorAll('.card-button').forEach(button => {
    button.addEventListener('click', function() {
        alert('ボタンがクリックされました！');
    });
});