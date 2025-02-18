from flask import Blueprint, render_template, redirect, jsonify, url_for, request, session, flash
from app.forms import LoginForm, SignupForm
from app.models import License, Inventory, User
from functools import wraps
from app.db import (
    inventory_collection,
    sales_tracking_collection,
    buy_tracking_collection,
    salaries_collection,
    cart_collection,
    user_collection,
    licenses_collection
)
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from bson import ObjectId
from werkzeug.security import check_password_hash

main = Blueprint('main', __name__)

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to require admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_email') != 'admin@admin.com':
            flash("You must be an admin to access this page.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    item_count = len(session.get('cart', []))
    return render_template('index.html', item_count=item_count)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/inventory_management', methods=['GET', 'POST'])
@login_required
def inventory_management():
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    user_email = session.get("user_email", "")

    if request.method == 'POST':
        item_name = request.form['item_name']
        buy_price = float(request.form['buy_price'])
        sell_price = float(request.form['sell_price'])
        quantity = int(request.form['quantity'])
        category = request.form['category']

        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join('app', 'static', 'images', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                image_url = url_for('static', filename='images/' + filename)

        total_cost = buy_price * quantity

        inventory_collection.insert_one({
            'name': item_name,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'quantity': quantity,
            'category': category,
            'total_cost': total_cost,
            'image_url': image_url
        })

        return redirect(url_for('main.add_to_cart'))
    
    item_count = len(session.get('cart', []))
    return render_template('inventory.html', user_email=user_email, inventory=inventory, item_count=item_count)

@main.route("/api/inventory")
def api_inventory():
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    return jsonify({"inventory": inventory, "userEmail": session.get("user_email", "")})


@main.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []  # Initialize cart in session

    cart = session['cart']

    for item in inventory_collection.find():
        item_id = str(item['_id'])  # Convert ObjectId to string
        if f'item_{item_id}' in request.form:  # Check if item was selected
            quantity = int(request.form.get(f'quantity_{item_id}', 1))
            
            if quantity > 0:
                # Check if the item already exists in the cart
                existing_item = next((i for i in cart if i["item_id"] == item_id), None)
                
                if existing_item:
                    existing_item["quantity"] += quantity
                else:
                    cart.append({
                        "item_id": item_id,
                        "name": item['name'],
                        "image_url": item.get('image_url', ''),
                        "sell_price": item['sell_price'],
                        "quantity": quantity
                    })

    session['cart'] = cart
    session.modified = True  # Ensure session updates

    print("Cart after adding items:", session.get('cart'))  # Debugging line

    flash("Items added to cart!", "success")
    return redirect(url_for('main.view_cart'))


@main.route('/view_cart')
@login_required
def view_cart():
    if 'user_email' not in session:
        flash("You must be logged in to view your cart.", "warning")
        return redirect(url_for('main.login'))

    cart_items = session.get('cart', [])

    print("Session cart before rendering:", cart_items)  # Debugging line

    detailed_cart_items = []
    for cart_item in cart_items:
        try:
            item_data = inventory_collection.find_one({"_id": ObjectId(cart_item['item_id'])})
            if item_data:
                detailed_cart_items.append({
                    'item': item_data,
                    'quantity': cart_item['quantity'],
                    'total_price': item_data['sell_price'] * cart_item['quantity']
                })
        except Exception as e:
            print("Error fetching item from DB:", e)  # Debugging error

    return render_template('cart.html', cart_items=detailed_cart_items, item_count=len(cart_items))



@main.route('/checkout', methods=['POST'])
@login_required
def checkout():
    user_email = session.get('user_email')

    if not user_email:
        flash("You must be logged in to checkout.", "danger")
        return redirect(url_for('main.login'))

    cart = session.get('cart', [])

    if not cart:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('main.view_cart'))

    for item in cart:
        item_data = inventory_collection.find_one({"_id": ObjectId(item['item_id'])})
        if item_data:
            # Check if there is enough stock
            if item_data['quantity'] < item['quantity']:
                flash(f"Not enough stock for {item_data['name']}. Available: {item_data['quantity']}", "danger")
                return redirect(url_for('main.view_cart'))

            # Update inventory
            new_quantity = item_data['quantity'] - item['quantity']
            inventory_collection.update_one(
                {"_id": ObjectId(item['item_id'])},
                {"$set": {"quantity": new_quantity}}
            )

            # Record purchase
            buy_tracking_collection.insert_one({
                "name": item_data["name"],
                "quantity": item["quantity"],
                "total_price": item_data["sell_price"] * item["quantity"],
                "purchase_date": datetime.utcnow(),
                "supplier": item_data.get("supplier", "Unknown"),
                "buyer_email": user_email
            })

    # Clear the cart after successful checkout
    session.pop('cart', None)
    session.modified = True

    flash("Purchase successful! Items have been recorded.", "success")
    return redirect(url_for('main.buy_tracking'))



@main.route('/remove_from_cart/<item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    if 'cart' not in session:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('main.view_cart'))

    cart = session['cart']
    cart = [item for item in cart if item['item_id'] != item_id]
    session['cart'] = cart
    session.modified = True

    flash("Item removed from cart!", "success")
    return redirect(url_for('main.view_cart'))



@main.route('/cancel_order')
@login_required
def cancel_order():
    session.pop('cart', None)
    session.modified = True
    flash("Order cancelled", "info")
    return redirect(url_for('main.index'))

@main.route('/sales_tracking')
def sales_tracking():
    sales = list(sales_tracking_collection.find())
    inventory = list(inventory_collection.find({}, {"_id": 0}))

    item_count = len(session.get('cart', []))
    return render_template('sales_tracking.html', sales_tracking=sales, inventory=inventory, item_count=item_count)

@main.route('/buy_tracking')
@admin_required
def buy_tracking():
    purchases = list(buy_tracking_collection.find())
    inventory = list(inventory_collection.find({}, {"_id": 0}))

    item_count = len(session.get('cart', []))
    return render_template('buy_tracking.html', buy_tracking=purchases, inventory=inventory, item_count=item_count)

@main.route('/salaries', methods=['GET', 'POST'])
@login_required
def salaries():
    if request.method == 'POST':
        employee_name = request.form['employee_name']
        position = request.form['position']
        salary = float(request.form['salary'])
        last_paid = datetime.strptime(request.form['last_paid'], '%Y-%m-%d')

        salaries_collection.insert_one({
            'employee_name': employee_name,
            'position': position,
            'salary': salary,
            'last_paid': last_paid
        })

        return redirect(url_for('main.salaries'))

    salaries_data = list(salaries_collection.find())
    inventory = list(inventory_collection.find({}, {"_id": 0}))

    item_count = len(session.get('cart', []))
    return render_template('salaries.html', salaries=salaries_data, inventory=inventory, item_count=item_count)

@main.route('/licenses')
@admin_required
def licenses():
    license_data = list(licenses_collection.find())
    inventory = list(inventory_collection.find({}, {"_id": 0}))

    item_count = len(session.get('cart', []))
    return render_template('licenses.html', licenses=license_data, inventory=inventory, item_count=item_count)

@main.route('/edit_license/<license_id>', methods=['GET', 'POST'])
def edit_license(license_id):
    license_data = licenses_collection.find_one({'_id': license_id})

    if request.method == 'POST':
        licenses_collection.update_one(
            {'_id': license_id},
            {'$set': {
                'type': request.form['type'],
                'expiration_date': request.form['expiration_date'],
                'status': request.form['status']
            }}
        )
        flash('License updated successfully!', 'success')
        return redirect(url_for('main.licenses'))

    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('edit_license.html', license=license_data, inventory=inventory, item_count=item_count)

@main.route('/add_license', methods=['GET', 'POST'])
def add_license():
    if request.method == 'POST':
        licenses_collection.insert_one({
            'type': request.form['type'],
            'expiration_date': request.form['expiration_date'],
            'status': request.form['status']
        })
        flash('New license added successfully!', 'success')
        return redirect(url_for('main.licenses'))
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('add_license.html', inventory=inventory, item_count=item_count)

@main.route('/delete_license/<license_id>', methods=['POST'])
def delete_license(license_id):
    if session.get('email') == 'admin@admin.com':
        License.delete_license(license_id)
        flash('License deleted successfully', 'success')
    else:
        flash('You are not authorized to delete licenses', 'danger')
    return redirect(url_for('main.licenses'))

@main.route('/about_us')
def about_us():
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('aboutus.html', inventory=inventory, item_count=item_count)

@main.route('/contact_us')
def contact_us():
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('contactus.html', inventory=inventory, item_count=item_count)

@main.route('/user_profile')
def user_profile():
    if 'user_email' not in session:
        return redirect(url_for('main.login'))

    user_email = session['user_email']
    purchases = list(buy_tracking_collection.find({"buyer_email": user_email}))

    for purchase in purchases:
        purchase['purchase_date'] = purchase['purchase_date'].strftime('%Y-%m-%d')

    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('user_profile.html', user=user_email, purchases=purchases, inventory=inventory, item_count=item_count)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.find_user(email)
        if user and User.verify_password(user['password'], password):
            session['user_email'] = email
            session.modified = True
            flash("Login successful!", "success")

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        flash("Invalid email or password", "danger")

    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('login.html', form=form, inventory=inventory, item_count=item_count)

@main.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    form = SignupForm()
    if form.validate_on_submit():
        User.create_user(form.username.data, form.email.data, form.password.data)
        return redirect(url_for('main.login'))
    inventory = list(inventory_collection.find({}, {"_id": 0}))
    item_count = len(session.get('cart', []))
    return render_template('sign_up.html', form=form, inventory=inventory, item_count=item_count)

@main.route('/logout')
def logout():
    session.pop('user_email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('main.index'))