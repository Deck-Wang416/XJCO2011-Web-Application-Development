document.addEventListener('DOMContentLoaded', function() {
    var cityInput = document.getElementById('cityInput');
    var cityDropdown = document.getElementById('cityDropdown');

    cityInput.addEventListener('focus', function() {
        fetch('/cities').then(response => response.json()).then(data => {
            cityDropdown.innerHTML = '';
            data.forEach(function(city) {
                let cityElement = document.createElement('a');
                cityElement.textContent = city;
                cityElement.href = '#';
                cityElement.addEventListener('click', function() {
                    cityInput.value = city;
                    cityDropdown.style.display = 'none';
                });
                cityDropdown.appendChild(cityElement);
            });
            cityDropdown.style.display = 'block';
        });
    });

    document.addEventListener('click', function(event) {
        if (event.target !== cityInput && event.target.parentNode !== cityDropdown) {
            cityDropdown.style.display = 'none';
        }
    });

    const checkInElem = document.querySelector('#checkInInput');
    const checkOutElem = document.querySelector('#checkOutInput');
    // Assume Datepicker is a valid library or function
    const checkInDatepicker = new Datepicker(checkInElem, {
        format: 'yyyy-mm-dd'
    });
    const checkOutDatepicker = new Datepicker(checkOutElem, {
        format: 'yyyy-mm-dd'
    });

    // Set initial values from cookies, if available
    document.querySelector('#cityInput').value = getCookie('city') || '';
    document.querySelector('#checkInInput').value = getCookie('checkInDate') || '';
    document.querySelector('#checkOutInput').value = getCookie('checkOutDate') || '';
});

function redirectToCityPage() {
    var cityInput = document.getElementById('cityInput').value;
    if(cityInput) {
        window.location.href = '/selectCity/' + cityInput;
    }
}

function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

document.querySelector('.search-btn').addEventListener('click', handleSubmit);

function isValidCheckInDate(date) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date >= today;
}

function isValidCheckOutDate(checkInDate, checkOutDate) {
    const dayAfterCheckIn = new Date(checkInDate);
    dayAfterCheckIn.setDate(dayAfterCheckIn.getDate() + 1);
    return checkOutDate >= dayAfterCheckIn;
}

function isValidCity(city) {
    const validCities = ["Beijing, China", "Shanghai, China", "Guangzhou, China", "Tianjin, China"];

    return validCities.includes(city);
}

function displayError(inputId) {
    const inputElement = document.querySelector(`#${inputId}`);

    inputElement.classList.add('flash-red');

    inputElement.addEventListener('animationend', () => {
        inputElement.classList.remove('flash-red');
    }, { once: true });
}

function handleSubmit() {
    const city = document.querySelector('#cityInput').value;
    const checkInDate = new Date(document.querySelector('#checkInInput').value);
    const checkOutDate = new Date(document.querySelector('#checkOutInput').value);
    
    if (!isValidCheckInDate(checkInDate)) {
        displayError('checkInInput');
    }

    if (!isValidCheckOutDate(checkInDate, checkOutDate)) {
        displayError('checkOutInput');
    }

    if (!isValidCity(city)) {
        displayError('cityInput');
    }

    if (!isValidCheckInDate(checkInDate) || 
    !isValidCheckOutDate(checkInDate, checkOutDate) || 
    !isValidCity(city)) {
        return;
    }

    setCookie('city', city, 7);
    setCookie('checkInDate', checkInDate.toISOString().split('T')[0], 7);
    setCookie('checkOutDate', checkOutDate.toISOString().split('T')[0], 7);
    
    redirectToCityPage();
}

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}
