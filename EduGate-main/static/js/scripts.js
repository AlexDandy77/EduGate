document.addEventListener('DOMContentLoaded', function() {
    const logInButton = document.getElementById('logInButton');

    logInButton.addEventListener('click', function() {
        window.location.href = 'login_page.html';
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const signInButton = document.getElementById('signUpButton');

    signInButton.addEventListener('click', function() {
        window.location.href = 'signin_page.html';
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const studentButton = document.getElementById('createStudent');
    const adminButton = document.getElementById('createAdmin');
    const parentButton = document.getElementById('createParent');

    studentButton.addEventListener('click', function() {
        window.location.href = 'signin_data_page.html';
    });

    adminButton.addEventListener('click', function() {
        window.location.href = 'signin_data_page.html'; 
    });

    parentButton.addEventListener('click', function() {
        window.location.href = 'signin_data_page.html'; 
    });
});

let list = document.querySelector('.card-wrapper .card-list');
let items = document.querySelectorAll('.card-wrapper .card-list .card-item');
let dots = document.querySelectorAll('.card-wrapper .dots li');
let prev = document.getElementById('prev');
let next = document.getElementById('next');


let active = 1;
let lengthItems = items.length - 1 ;

reloadSlider();

next.onclick = function(){
    if(active + 1 > lengthItems){
        active = 0;
    }else{
        active = active + 1;
    }
    reloadSlider();
}

prev.onclick = function(){
    if(active - 1 < 0){
        active = lengthItems;
    }else{
        active = active - 1;
    }
    reloadSlider();
}

// let refreshSlider = setInterval(()=> {next.click()}, 10000);

function reloadSlider() {
    let checkLeft = items[active].offsetLeft;
    let pageWidth = window.innerWidth;
    const leftRightItemWidth = (pageWidth - pageWidth*0.50 - 50) / 2;
    let translateX = - checkLeft + leftRightItemWidth;

    // Apply the translateX transformation to the list (slider)
    list.style.transform = `translateX(${translateX}px)`;

    // Update the active dot
    let lastActiveDot = document.querySelector('.card-wrapper .dots li.active');
    if (lastActiveDot) {
        lastActiveDot.classList.remove('active');
    }
    dots[active].classList.add('active');
}



dots.forEach((li, key) => {
    li.addEventListener('click', function(){
        active = key;
        reloadSlider();
    })
})