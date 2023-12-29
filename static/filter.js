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

function formatDate(dateString) {
    const parts = dateString.split('/');
    if (parts.length === 3) {
        return `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
    }
    return dateString;
}

function updateRooms() {
    if (typeof hotel_id === 'undefined') {
        console.log('hotel_id is not defined');
        return; 
    }
    
    console.log('updateRooms called'); 
    var selectedRoomTypes = Array.from(document.querySelectorAll('.filter-option.selected[data-type="room_type"]'))
                                .map(opt => opt.textContent.trim());
    var selectedBedTypes = Array.from(document.querySelectorAll('.filter-option.selected[data-type="bed_type"]'))
                                .map(opt => opt.textContent.trim());
    var checkInDate = formatDate(getCookie('checkInDate'));
    var checkOutDate = formatDate(getCookie('checkOutDate'));
    var queryParams = [`checkInDate=${checkInDate}`, `checkOutDate=${checkOutDate}`];
    
    if (selectedRoomTypes.length === 0 && selectedBedTypes.length === 0) {
        queryParams.push('room_types=All');
        queryParams.push('bed_types=All');
    } else {
        if (selectedRoomTypes.length > 0) {
            queryParams.push(`room_types=${encodeURIComponent(selectedRoomTypes.join(','))}`);
        }
        if (selectedBedTypes.length > 0) {
            queryParams.push(`bed_types=${encodeURIComponent(selectedBedTypes.join(','))}`);
        }
    }
    var queryStr = queryParams.join('&');
    var fetchUrl = `/selectRoom/filter/${hotel_id}?${queryStr}`;
    fetch(fetchUrl)
    .then(response => {
        if (!response.ok) {
            throw new Error('Server responded with status: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        updateRoomList(data);
    })
    .catch(error => {
        console.error('Error fetching filtered rooms:', error);
    });
}

function updateRoomList(rooms) {
    const hotelList = document.querySelector('.hotel-list');
    hotelList.innerHTML = '';
    rooms.forEach(room => {
        const checkInDate = getCookie('checkInDate');
        const checkOutDate = getCookie('checkOutDate');
        const bookingUrl = `/review/${room.id}?checkInDate=${checkInDate}&checkOutDate=${checkOutDate}`;
        const roomElement = document.createElement('div');
        roomElement.className = 'hotel-entry';
        roomElement.innerHTML = `
            <img src="/static/${room.image_filename}" alt="${room.description}">
            <div class="hotel-info">
                <h2>${room.type_name}</h2>
                <p><strong>Bed Type:</strong> ${room.bed_type}</p>
                <p><strong>Facilities:</strong> ${room.facilities}</p>
                <div class="hotel-booking">
                    <span class="price">CNY ${room.price}</span>
                    ${room.available_quantity > 0 ? 
                        `<a tabindex="0" href="${bookingUrl}" class="booking-btn">Book Now</a>` :
                        '<a class="disabled">SOLD OUT</a>'}
                </div>
            </div>`;
        hotelList.appendChild(roomElement);
    });
}


document.querySelectorAll('.filter-option').forEach(option => {
    option.addEventListener('click', function() {
        this.classList.toggle('selected');
        updateSelectedFilters();
        updateRooms();
    });
});

function updateSelectedFilters() {
    const selectedFilters = document.querySelectorAll('.filter-option.selected');
    const selectedFiltersContainer = document.getElementById('selected-filters');
    selectedFiltersContainer.innerHTML = '';
    selectedFilters.forEach(filter => {
        const filterTag = document.createElement('div');
        filterTag.className = 'filter-tag';
        filterTag.textContent = filter.textContent;
        const closeBtn = document.createElement('span');
        closeBtn.textContent = '×';
        closeBtn.className = 'close';
        closeBtn.addEventListener('click', function() {
            filter.classList.remove('selected');
            filterTag.remove();
            updateRooms();
        });
        filterTag.appendChild(closeBtn);
        selectedFiltersContainer.appendChild(filterTag);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    updateRooms(); 
});
