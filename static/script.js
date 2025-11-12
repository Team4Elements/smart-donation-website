// Select main elements
const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

// When user clicks Register button
registerBtn.addEventListener('click', () => {
    container.classList.add('active');
});

// When user clicks Login button
loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
});

