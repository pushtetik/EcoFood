
document.addEventListener('DOMContentLoaded', function() {
    const ratingFills = document.querySelectorAll('.rating-fill');
    ratingFills.forEach(fill => {
        const width = fill.getAttribute('data-width');
        if (width) {
       
            setTimeout(() => {
                fill.style.width = width + '%';
            }, 100);
        }
    });
});

let correctAnswer = 0;

function generateCaptcha() {
    const num1 = Math.floor(Math.random() * 10) + 1;
    const num2 = Math.floor(Math.random() * 10) + 1;
    document.getElementById('captcha').textContent = `${num1} + ${num2} = ?`;
    return num1 + num2;
}


document.addEventListener('DOMContentLoaded', function() {

    correctAnswer = generateCaptcha();

    const commentField = document.querySelector('textarea[name="comment"]');
    if (commentField) {
        commentField.addEventListener('input', function(e) {
            const count = e.target.value.length;
            document.getElementById('charCount').textContent = count;
            
            if (count > 500) {
                e.target.value = e.target.value.substring(0, 500);
                document.getElementById('charCount').textContent = 500;
            }
        });
    }
    

    document.getElementById('reviewForm').addEventListener('submit', function(e) {
        const userAnswer = parseInt(document.getElementById('captchaInput').value);
        
        if (userAnswer !== correctAnswer) {
            e.preventDefault();
            alert('Неправильный ответ на капчу! Попробуйте еще раз.');
            correctAnswer = generateCaptcha();
            document.getElementById('captchaInput').value = '';
            return;
        }

        const requiredFields = [
            'product_quality',
            'product_freshness', 
            'service_quality',
            'recommend'
        ];
        
        let allFilled = true;
        requiredFields.forEach(field => {
            const fieldValue = document.querySelector(`input[name="${field}"]:checked`);
            if (!fieldValue) {
                allFilled = false;
            }
        });
        
        if (!allFilled) {
            e.preventDefault();
            alert('Пожалуйста, ответьте на все вопросы опросника!');
            return;
        }
        
        console.log('✅ Опросник отправляется');
    });
});


function openModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        const currentUserElement = document.querySelector('.current-user strong');
        if (currentUserElement) {
            const userName = currentUserElement.textContent;

        }
    }
}
function closeModal() {
    document.getElementById('reviewModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('reviewModal');
    if (event.target == modal) {
        closeModal();
    }
}
