document.addEventListener('DOMContentLoaded', function() {
    var joinForm = document.getElementById('joinForm');
    var signInForm = document.getElementById('signInForm');
    var guestInfoForm = document.getElementById('guestInfoForm');

    if (joinForm) {
        addFormSubmitListener(joinForm, '/joinNow');
    }

    if (signInForm) {
        addFormSubmitListener(signInForm, '/signIn');
    }

    if (guestInfoForm) {
        addFormSubmitListener(guestInfoForm, '/submitBooking');
    }
});

function addFormSubmitListener(form, actionUrl) {
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        document.querySelector('[type="submit"]').disabled = true;
        showNotification('processing', 'Operation in progress...');

        var formData = new FormData(form);

        setTimeout(function() {
            fetch(actionUrl, {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                document.querySelector('[type="submit"]').disabled = false;
                return response.json();
            })
            .then(function(data) {
                showNotification(data.status === 'success' ? 'success' : 'fail', data.message);
                if (data.status === 'success') {
                    setTimeout(function() {
                        window.location.href = '/';
                    }, 2000);
                }
            })
            .catch(function(error) {
                document.querySelector('[type="submit"]').disabled = false;
                showNotification('fail', error.message);
            });
        }, 2000); 
    });
}

function showNotification(status, message) {
    var notificationElement = document.getElementById('notification');
    var messageElement = document.getElementById('notification-message');

    notificationElement.classList.remove('notification-processing', 'notification-success', 'notification-fail');
    notificationElement.classList.add('notification-' + status);

    messageElement.textContent = message;

    notificationElement.style.display = 'flex'; 
    notificationElement.style.justifyContent = 'center';
    notificationElement.style.alignItems = 'center';

    notificationElement.scrollIntoView({ behavior: 'smooth', block: 'center' });

    setTimeout(function() {
        notificationElement.style.display = 'none';
    }, 2000);
}

function confirmSignOut() {
    if (confirm("Are you sure to sign out?")) {
        window.location.href = signOutUrl;
    }
}
