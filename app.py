from datetime import datetime, timedelta, date
import time
import re

import click
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session)
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
from flask import abort

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the SQLAlchemy extension
db = SQLAlchemy(app)


class TokenBucket:
    def __init__(self, capacity, fill_rate):
        """
        Initialize the token bucket.

        :param capacity: The maximum number of tokens in the bucket.
        :param fill_rate: Rate at which the bucket is refilled.
        """
        self.capacity = capacity  # Max number of tokens in the bucket
        self._tokens = capacity  # Current number of tokens in the bucket
        self.fill_rate = fill_rate  # Rate of filling the bucket
        self.last_checked = time.time()  # Last time token count was updated

    def consume(self, tokens=1):
        """
        Consume tokens from the bucket.

        :param tokens: Number of tokens to consume.
        :return: True if there were enough tokens, False otherwise.
        """
        now = time.time()
        # Update the token count based on time elapsed and fill rate
        if self._tokens < self.capacity:
            self._tokens += (now - self.last_checked) * self.fill_rate
            self._tokens = min(self._tokens, self.capacity)
        self.last_checked = now
        # Check if enough tokens are available for consumption
        if tokens <= self._tokens:
            self._tokens -= tokens
            return True
        return False


# Allow up to 50 register and 100 login attempts per minute
register_bucket = TokenBucket(capacity=50, fill_rate=50/60)
login_bucket = TokenBucket(capacity=100, fill_rate=100/60)


@app.cli.command('initdb')
@click.option('--drop', is_flag=True, help='Create after drop.')
@with_appcontext
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')


@app.cli.command('forge')
@with_appcontext
def forge():
    """Generate sample hotels for testing selectCity functionality."""
    db.drop_all()
    db.create_all()

    # Create sample room types and bed types
    room_types = [
        RoomType(type_name='Deluxe Room', image_filename='images/bed1.jpg'),
        RoomType(type_name='Executive Suite', image_filename='images/bed2.jpg')
    ]
    bed_types = [
        BedType(bed_type='King Size'),
        BedType(bed_type='Twin Beds')
    ]

    for rt in room_types:
        db.session.add(rt)
    for bt in bed_types:
        db.session.add(bt)
    db.session.commit()

    # Sample data for hotels in different cities
    hotels_data = [
        {
            'name': 'CBD Shangri-La',
            'city': 'Beijing, China',
            'address': 'No 1 Jianguomenwai Avenue, Beijing China',
            'phone_number': '(86 10) 6505 2266',
            'description': 'The Shangri-La Beijing is ideally located at '
                           'the heart of Beijing\'s diplomatic '
                           'and central business district.',
            'image_filename': 'images/hotel1.jpg',
            'price': 1035.0
        },

        {
            'name': 'CBD Shangri-La',
            'city': 'Shanghai, China',
            'address': 'No 2 Jianguomenwai Avenue, Shanghai China',
            'phone_number': '(86 10) 6505 2266',
            'description': 'The Shangri-La Shanghai is ideally located at '
                           'the heart of Shanghai\'s diplomatic '
                           'and central business district.',
            'image_filename': 'images/hotel1.jpg',
            'price': 1035.0
        },

        {
            'name': 'CBD Shangri-La',
            'city': 'Guangzhou, China',
            'address': 'No 3 Jianguomenwai Avenue, Guangzhou China',
            'phone_number': '(86 10) 6505 2266',
            'description': 'The Shangri-La Guangzhou is ideally located at '
                           'the heart of Guangzhou\'s diplomatic '
                           'and central business district.',
            'image_filename': 'images/hotel2.jpg',
            'price': 1035.0
        },

        {
            'name': 'CBD Shangri-La',
            'city': 'Tianjin, China',
            'address': 'No 4 Jianguomenwai Avenue, Tianjin China',
            'phone_number': '(86 10) 6505 2266',
            'description': 'The Shangri-La Tianjin is ideally located at '
                           'the heart of Tianjin\'s diplomatic '
                           'and central business district.',
            'image_filename': 'images/hotel2.jpg',
            'price': 1035.0
        }
    ]

    for hotel_data in hotels_data:
        hotel = Hotel(**hotel_data)
        db.session.add(hotel)
    db.session.commit()

    # Define sold out and default dates for room availability
    sold_out_start_date = datetime.today().date()
    sold_out_end_date = sold_out_start_date + timedelta(days=3)
    default_start_date = datetime(2023, 1, 1).date()
    default_end_date = datetime(2025, 1, 1).date()

    # Create rooms and inventory for each hotel
    for hotel in Hotel.query.all():
        for rt in room_types:
            for bt in bed_types:
                room_description = f'{rt.type_name} with {bt.bed_type}'
                room = Room(
                    hotel_id=hotel.id,
                    room_type_id=rt.id,
                    bed_type_id=bt.id,
                    description=room_description,
                    price=1200.0,
                    facilities='Free WiFi, En-suite bathroom, Flat screen TV'
                )
                db.session.add(room)

                if hotel.name == 'CBD Shangri-La' and \
                   hotel.city == 'Tianjin, China' and \
                   rt.type_name == 'Executive Suite' and \
                   bt.bed_type == 'King Size':
                    available_quantity = 0
                    start_date = sold_out_start_date
                    end_date = sold_out_end_date
                else:
                    available_quantity = 4
                    start_date = default_start_date
                    end_date = default_end_date

                inventory = RoomInventory(
                    hotel_id=hotel.id,
                    room_type_id=rt.id,
                    bed_type_id=bt.id,
                    available_quantity=available_quantity,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(inventory)
    db.session.commit()

    # Create sample customers and admins
    customer = Customer(first_name="Deck", last_name="Wang",
                        contact="15522761141", password="20030416Wyf")
    db.session.add(customer)

    additional_customers = [
        Customer(first_name="Alice", last_name="Zhang",
                 contact="12345678901", password="alicepassword"),
        Customer(first_name="Bob", last_name="Li",
                 contact="12345678902", password="bobpassword"),
        Customer(first_name="Carol", last_name="Wu",
                 contact="12345678903", password="carolpassword"),
        Customer(first_name="Dave", last_name="Zhao",
                 contact="12345678904", password="davepassword"),
        Customer(first_name="Eve", last_name="Liu",
                 contact="12345678905", password="evepassword")
    ]

    for additional_customer in additional_customers:
        db.session.add(additional_customer)

    admins = [
        Customer(first_name="Admin", last_name="Userone",
                 contact="12345678910", password="54Administrator"),
        Customer(first_name="Admin", last_name="Usertwo",
                 contact="11223344556", password="54Administrator")
    ]

    for admin in admins:
        db.session.add(admin)

    db.session.commit()

    # Create sample bookings for a specific room
    tianjin_exec_suite_king_room = Room.query.join(RoomType, BedType).filter(
        Room.hotel.has(name='CBD Shangri-La', city='Tianjin, China'),
        RoomType.type_name == 'Executive Suite',
        BedType.bed_type == 'King Size'
    ).first()

    if tianjin_exec_suite_king_room:
        for _ in range(4):
            booking = Booking(
                customer_id=customer.id,
                room_id=tianjin_exec_suite_king_room.id,
                check_in_date=sold_out_start_date,
                check_out_date=sold_out_end_date,
                payment_status='confirmed',
                special_request="I don't smoke"
            )
            db.session.add(booking)
    db.session.commit()

    click.echo('Database initialized with sample data.')


class Customer(db.Model):
    """Model for customer data."""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bookings = db.relationship('Booking', backref='customer', lazy=True)


class RoomType(db.Model):
    """Model representing different types of rooms."""
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(100))
    rooms = db.relationship('Room', backref='room_type', lazy=True)


class BedType(db.Model):
    """Model for different types of bed configurations in rooms."""
    id = db.Column(db.Integer, primary_key=True)
    bed_type = db.Column(db.String(100), nullable=False)
    rooms = db.relationship('Room', backref='bed_type', lazy=True)


class Hotel(db.Model):
    """Model for hotel details."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(100))
    price = db.Column(db.Float)
    rooms = db.relationship('Room', backref='hotel', lazy=True)


class Room(db.Model):
    """Model for individual rooms in hotels."""
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'))
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'))
    bed_type_id = db.Column(db.Integer, db.ForeignKey('bed_type.id'))
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    facilities = db.Column(db.Text, nullable=False)
    bookings = db.relationship('Booking', backref='room', lazy=True)


class Booking(db.Model):
    """Model for booking information."""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    check_in_date = db.Column(db.DateTime, nullable=False)
    check_out_date = db.Column(db.DateTime, nullable=False)
    payment_status = db.Column(db.String(100), nullable=False)
    special_request = db.Column(db.Text)


class Tag(db.Model):
    """Model for tags that can be associated with rooms."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room_tags = db.relationship('RoomTag', backref='tag', lazy=True)


class RoomTag(db.Model):
    """Intermediate model for associating tags with rooms."""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))


class RoomInventory(db.Model):
    """Model for managing room inventory."""
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey(
        'room_type.id'), nullable=False)
    bed_type_id = db.Column(db.Integer, db.ForeignKey(
        'bed_type.id'), nullable=False)
    available_quantity = db.Column(db.Integer, default=4)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    room_type = db.relationship('RoomType', backref='inventory')
    bed_type = db.relationship('BedType', backref='inventory')
    hotel = db.relationship('Hotel', backref='inventory')


class Log(db.Model):
    """Model for logging actions in the system."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'customer.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Log {self.timestamp} {self.action}>'


def log_action(user_id, action, description):
    """
    Record an action in the log.

    Creates a new log entry in database with specified items.

    :param user_id: The ID of the user performing the action.
    :param action: The type of action being logged.
    :param description: A brief description of the action.
    """
    log_entry = Log(user_id=user_id, action=action, description=description)
    db.session.add(log_entry)
    db.session.commit()


@app.route('/')
def homepage():
    """
    Render the homepage of the website.

    Determines if the user or admin is logged in and passes this information
    to the template for rendering the appropriate view.
    """
    # Check if user and admin are logged in
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = session.get('admin_logged_in', False)

    context = {
        'user_logged_in': user_logged_in,
    }

    if admin_logged_in:
        context['admin_logged_in'] = admin_logged_in

    return render_template('homepage.html', **context)


@app.route('/cities')
def cities():
    """
    Retrieve and return a list of distinct cities from the Hotel records.

    Queries the database for all unique cities where hotels are located,
    and returns this list in JSON format.
    """
    cities = Hotel.query.with_entities(Hotel.city).distinct().all()
    return jsonify([city[0] for city in cities])


@app.route('/selectCity/<city_name>')
def selectCity(city_name):
    """
    Render the page for selecting hotels in a specified city.

    Retrieves a list of hotels in the given city and determines the login
    status of the user and admin. Passes this information along with the list
    of hotels to the template for rendering.

    :param city_name: The name of the city to query hotels in.
    """
    # Check user and admin login status
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = session.get('admin_logged_in', False)

    hotels = Hotel.query.filter_by(city=city_name).all()

    context = {
        'user_logged_in': user_logged_in,
        'hotels': hotels,
        'city_name': city_name
    }

    if admin_logged_in:
        context['admin_logged_in'] = admin_logged_in

    return render_template('selectCity.html', **context)


@app.route('/selectRoom/<int:hotel_id>')
def selectRoom(hotel_id):
    """
    Render the page for selecting rooms in a specified hotel.

    Retrieves a list of rooms for the given hotel and determines the login
    status of the user and admin. Passes this information along with the list
    of rooms to the template for rendering.

    :param hotel_id: The ID of the hotel to query rooms in.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = session.get('admin_logged_in', False)

    rooms = Room.query.filter_by(hotel_id=hotel_id).all()

    context = {
        'user_logged_in': user_logged_in,
        'rooms': rooms,
        'hotel_id': hotel_id
    }

    if admin_logged_in:
        context['admin_logged_in'] = admin_logged_in

    return render_template('selectRoom.html', **context)


@app.route('/selectRoom/filter/<int:hotel_id>')
def filter_rooms(hotel_id):
    """
    Filter and return rooms based on specified criteria.

    Retrieves a list of rooms in the given hotel based on filters, such as
    room types, bed types, check-in and check-out dates. The function returns
    the filtered list of rooms with their availability status in JSON format.

    :param hotel_id: The ID of the hotel to query rooms in.
    """
    try:
        room_types = request.args.get('room_types')
        bed_types = request.args.get('bed_types')
        check_in_date = request.args.get('checkInDate')
        check_out_date = request.args.get('checkOutDate')

        check_in_date = datetime.strptime(
            check_in_date, '%Y-%m-%d') if check_in_date else None
        check_out_date = datetime.strptime(
            check_out_date, '%Y-%m-%d') if check_out_date else None

        query = Room.query.filter(Room.hotel_id == hotel_id)

        if room_types and room_types != 'All':
            room_type_list = room_types.split(',')
            query = query.join(Room.room_type).filter(
                RoomType.type_name.in_(room_type_list))

        if bed_types and bed_types != 'All':
            bed_type_list = bed_types.split(',')
            query = query.join(Room.bed_type, isouter=True).filter(
                BedType.bed_type.in_(bed_type_list))

        rooms = query.all()
        rooms_data = []

        for room in rooms:
            inventory = RoomInventory.query.filter(
                RoomInventory.hotel_id == hotel_id,
                RoomInventory.room_type_id == room.room_type_id,
                RoomInventory.bed_type_id == room.bed_type_id,
                RoomInventory.start_date <= check_in_date,
                RoomInventory.end_date >= check_out_date
            ).first()

            if not inventory:
                continue

            bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.check_in_date < check_out_date,
                Booking.check_out_date > check_in_date
            ).all()

            booked_rooms = sum(
                1 for booking in bookings
                if booking.check_out_date > check_in_date
                and booking.check_in_date < check_out_date
            )

            available_quantity = max(
                0, inventory.available_quantity - booked_rooms)

            room_data = {
                'id': room.id,
                'hotel_id': room.hotel_id,
                'room_type_id': room.room_type_id,
                'bed_type_id': room.bed_type_id,
                'description': room.description,
                'price': room.price,
                'facilities': room.facilities,
                'image_filename': (
                    room.room_type.image_filename if room.room_type else None
                ),
                'type_name': (
                    room.room_type.type_name if room.room_type else None,
                ),
                'bed_type': room.bed_type.bed_type if room.bed_type else None,
                'available_quantity': available_quantity
            }
            rooms_data.append(room_data)

    except Exception as e:
        print(e)
        return jsonify({'error': 'Server error'}), 500

    return jsonify(rooms_data)


@app.route('/joinNow', methods=['GET', 'POST'])
def joinNow():
    """
    Handle user registration requests.

    This function processes registration form submissions. It performs various
    checks such as rate limiting, data validation, and uniqueness of the mobile
    number. On successful registration, it logs the action and returns success
    messages. In case of any errors, appropriate error messages are returned.
    """
    if request.method == 'POST':
        if not register_bucket.consume():
            return jsonify({
                'status': 'error',
                'message': 'Too many attempts, try again later!'
            }), 429

        try:
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            mobile = request.form.get('mobile')
            password = request.form.get('password')

            existing_customer = Customer.query.filter_by(
                contact=mobile).first()
            if existing_customer:
                return jsonify({
                    'status': 'error',
                    'message': 'Mobile Number Already Registered!'
                }), 400

            if not all([first_name, last_name, mobile, password]):
                return jsonify({
                    'status': 'error',
                    'message': 'All fields are required!'
                }), 400

            name_pattern = re.compile(r"^[A-Za-z\s]+$")
            if not (re.match(name_pattern, first_name) and
                    re.match(name_pattern, last_name)):

                return jsonify({
                    'status': 'error',
                    'message': 'Invalid Names!'
                }), 400

            if len(mobile) != 11 or not mobile.isdigit():
                return jsonify({
                    'status': 'error',
                    'message': 'Mobile Number Must Be 11 Digits!'
                }), 400

            if (len(password) < 8 or
                    not any(char.isdigit() for char in password) or
                    not any(char.isalpha() for char in password)):
                return jsonify({
                    'status': 'error',
                    'message': ' Invalid Password!'
                }), 400

            new_customer = Customer(
                first_name=first_name, last_name=last_name,
                contact=mobile, password=password)
            db.session.add(new_customer)
            db.session.commit()

            log_action(new_customer.id, 'register',
                       f'New user registered: {mobile}')

            return jsonify({
                'status': 'success',
                'message': 'You Have Successfully Joined!'
            })

        except Exception as e:
            app.logger.error(f'Error in joinNow: {e}')
            return jsonify({
                'status': 'error',
                'message': 'Internal Server Error'
            }), 500

    return render_template('joinNow.html')


@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    """
    Handle user sign-in requests.

    This function processes sign-in form submissions, performing rate limiting,
    data validation, and authentication checks. It sets session variables upon
    successful authentication and returns appropriate messages for success or
    failure cases.
    """
    if request.method == 'POST':
        if not login_bucket.consume():
            return jsonify({
                'status': 'error',
                'message': 'Too many attempts, try again later!'
            }), 429

        mobile = request.form.get('mobile')
        password = request.form.get('password')

        if not all([mobile, password]):
            return jsonify({
                'status': 'error',
                'message': 'All fields are required!'
            }), 400

        if len(mobile) != 11 or not mobile.isdigit():
            return jsonify({
                'status': 'error',
                'message': 'Mobile Number Must Be 11 Digits!'
            }), 400

        customer = Customer.query.filter_by(contact=mobile).first()

        if customer:
            if customer.password == password:
                session['user_logged_in'] = True
                session['user_id'] = customer.id
                log_action(customer.id, 'login', 'User logged in')
                if password == "54Administrator":
                    session['admin_logged_in'] = True
                else:
                    session['admin_logged_in'] = False
                return jsonify({
                    'status': 'success',
                    'message': 'You Have Successfully Signed In!'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Wrong Password!'
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'message': 'The Account Does Not Exist!'
            }), 400

    return render_template('signIn.html')


@app.route('/signOut')
def signOut():
    """
    Handle the sign-out process for a logged-in user.

    Logs out user by clearing relevant session variables. If users logged in,
    their logout action is recorded. The user is then redirected to homepage.
    """
    user_id = session.get('user_id')
    session.pop('user_logged_in', None)
    session.pop('admin_logged_in', None)

    if user_id:
        log_action(user_id, 'logout', 'User logged out')

    return redirect(url_for('homepage'))


@app.route('/review/<int:room_id>')
def review(room_id):
    """
    Render the review page for a specific room.

    Checks if the user is logged in and redirects to sign-in page if not.
    Retrieves room, hotel, and room type information for the given room ID,
    along with the user's check-in and check-out dates,
    to display on the review page.

    :param room_id: The ID of the room to review.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = session.get('admin_logged_in', False)

    if not user_logged_in:
        return redirect(url_for('signIn'))

    user_id = session.get('user_id')
    customer = Customer.query.get(user_id) if user_id else None

    check_in_date = request.args.get('checkInDate')
    check_out_date = request.args.get('checkOutDate')

    room = Room.query.get(room_id)
    hotel = Hotel.query.get(room.hotel_id) if room else None
    room_type = RoomType.query.get(room.room_type_id) if room else None

    context = {
        'user_logged_in': user_logged_in,
        'hotel': hotel,
        'room': room,
        'room_type': room_type,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'customer': customer
    }

    if admin_logged_in:
        context['admin_logged_in'] = admin_logged_in

    return render_template('review.html', **context)


@app.route('/submitBooking', methods=['POST'])
def submit_booking():
    """
    Handle the booking submission request.

    Processes the booking form submission, validating the input data
    and creating a new booking record. It returns a success message
    upon successful booking or an error message in case of validation failure.
    """
    try:
        check_in_date = datetime.strptime(
            request.cookies.get('checkInDate'), '%Y-%m-%d')
        check_out_date = datetime.strptime(
            request.cookies.get('checkOutDate'), '%Y-%m-%d')

    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid date format!'
        }), 400

    room_id = request.form.get('room_id')
    if not room_id:
        return jsonify({
            'status': 'error',
            'message': 'Room ID is missing!'
        }), 400
    room_id = int(room_id)

    user_id = session.get('user_id')
    special_request = request.form.get('specialRequest')
    guest_first_name = request.form.get('guestFirstName')
    guest_last_name = request.form.get('guestLastName')
    guest_mobile = request.form.get('guestMobile')

    name_pattern = re.compile(r"^[A-Za-z\s]+$")
    if not (re.match(name_pattern, guest_first_name) and
            re.match(name_pattern, guest_last_name)):
        return jsonify({
            'status': 'error',
            'message': 'Invalid Names!'
        }), 400
    if len(guest_mobile) != 11 or not guest_mobile.isdigit():
        return jsonify({
            'status': 'error',
            'message': 'Mobile Number Must Be 11 Digits!'
        }), 400

    # Update booking information
    booking = Booking(customer_id=user_id, room_id=room_id,
                      check_in_date=check_in_date,
                      check_out_date=check_out_date,
                      special_request=special_request,
                      payment_status='confirmed')
    db.session.add(booking)

    # Update customer information if changed
    customer = Customer.query.get(user_id)
    if customer:
        if customer.first_name != guest_first_name:
            customer.first_name = guest_first_name
        if customer.last_name != guest_last_name:
            customer.last_name = guest_last_name
        if customer.contact != guest_mobile:
            customer.contact = guest_mobile

    db.session.commit()

    log_action(user_id, 'booking',
               f'Booking made for room {room_id} by user {user_id}')

    return jsonify({
        'status': 'success',
        'message': 'Booking submitted successfully!'
    })


@app.route('/userCenter')
def userCenter():
    """
    Render the user center page showing user details and bookings.

    The function retrieves logged-in user's details and their booking history,
    and renders the user center page with this information.
    Redirects to a 404 page if the user is not logged in.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = session.get('admin_logged_in', False)

    user_id = session.get('user_id')
    if not user_id or not user_logged_in:
        abort(404)
    user = Customer.query.get(user_id)

    bookings = Booking.query.filter_by(customer_id=user_id).all()
    booking_details = []

    for booking in bookings:
        room = Room.query.get(booking.room_id)
        hotel = Hotel.query.get(room.hotel_id) if room else None
        room_type = RoomType.query.get(room.room_type_id) if room else None

        booking_info = {
            'hotel': hotel,
            'room': room,
            'room_type': room_type,
            'check_in_date': booking.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': booking.check_out_date.strftime('%Y-%m-%d'),
            'special_request': booking.special_request
        }
        booking_details.append(booking_info)

    context = {
        'user_logged_in': user_logged_in,
        'user': user,
        'bookings': booking_details
    }

    if admin_logged_in:
        context['admin_logged_in'] = admin_logged_in

    return render_template('userCenter.html', **context)


@app.errorhandler(404)
def page_not_found(e):
    """Error handler for 404 page not found."""
    return render_template('404.html'), 404


@app.route('/userInfor')
def userInfor():
    """
    Render the user information page.

    This function displays a list of all customers. It's accessible only to
    administrators. If non-admin tries to access it, 404 error is triggered.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = 'admin_logged_in' in session

    if 'admin_logged_in' not in session:
        abort(404)

    customers = Customer.query.all()
    return render_template('userInfor.html',
                           customers=customers,
                           user_logged_in=user_logged_in,
                           admin_logged_in=admin_logged_in)


@app.route('/orderInfor')
def orderInfor():
    """
    Render the order information page.

    This function displays a list of all bookings. Like user information page,
    it's accessible only to admins. Non-admin access results in a 404 error.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = 'admin_logged_in' in session

    if 'admin_logged_in' not in session:
        abort(404)

    bookings = Booking.query.join(Room, RoomType, BedType, Customer).all()
    return render_template('orderInfor.html',
                           bookings=bookings, user_logged_in=user_logged_in,
                           admin_logged_in=admin_logged_in)


@app.route('/inventory')
def inventory():
    """
    Render the inventory page.

    Shows current room inventory, accessible only to administrators.
    Non-admin access leads to 404 error. The inventory is shown for today.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = 'admin_logged_in' in session

    if 'admin_logged_in' not in session:
        abort(404)

    today = date.today()
    inventories = RoomInventory.query.join(Hotel, RoomType, BedType).filter(
        RoomInventory.start_date <= today,
        RoomInventory.end_date >= today
    ).all()
    return render_template('inventory.html',
                           inventories=inventories,
                           user_logged_in=user_logged_in,
                           admin_logged_in=admin_logged_in)


@app.route('/logs')
def logs():
    """
    Render the logs page.

    Displays a list of all system logs. This page is accessible only to
    administrators, and unauthorized access leads to a 404 error.
    """
    user_logged_in = 'user_logged_in' in session
    admin_logged_in = 'admin_logged_in' in session

    if 'admin_logged_in' not in session:
        abort(404)

    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('logs.html',
                           logs=logs,
                           user_logged_in=user_logged_in,
                           admin_logged_in=admin_logged_in)


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """
    Handle the deletion of a user.

    Only accessible to administrators. Deletes a user with specified user ID
    and redirects to the user information page.
    """
    if 'admin_logged_in' not in session:
        abort(404)

    user_to_delete = Customer.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()

    return redirect(url_for('userInfor'))


@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    """
    Handle the deletion of an order.

    Only accessible to administrators. Deletes an order with specified order ID
    and redirects to the order information page.
    """
    if 'admin_logged_in' not in session:
        abort(404)

    order_to_delete = Booking.query.get(order_id)
    if order_to_delete:
        db.session.delete(order_to_delete)
        db.session.commit()

    return redirect(url_for('orderInfor'))
