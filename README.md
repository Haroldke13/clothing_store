https://clothing-store-j0ua.onrender.com/
See how the site works on the above webpage

# Inventory Management System

## Overview
This project is a web-based Inventory Management System built using Flask. It allows users to manage inventory, track sales, handle purchases, and manage user authentication.

## Features
- **User Authentication**
  - Login and signup system
  - Admin and user roles
  
- **Inventory Management**
  - Add, edit, and delete inventory items
  - Upload item images
  - View available stock

- **Shopping Cart & Checkout**
  - Add items to cart
  - View cart details
  - Remove items from cart
  - Checkout process with inventory updates

- **Sales & Purchase Tracking**
  - Track sales transactions
  - Record purchase history
  - Monitor inventory updates

- **Salary Management**
  - Add and manage employee salaries

- **License Management**
  - Add, edit, and delete licenses

- **Additional Pages**
  - About Us
  - Contact Us
  - User Profile

## Technologies Used
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, Jinja2 Templates
- **Security**: Werkzeug for password hashing

## Installation Guide
### Prerequisites
- Python 3.x
- MongoDB
- Virtual Environment (optional but recommended)

### Setup Instructions
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd inventory-management
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file and add necessary configurations such as database URI.

5. Run the application:
   ```bash
   flask run
   ```

6. Open the browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage
- **Admin Access**: The default admin user can access purchase tracking, salary management, and license management.
- **Regular Users**: Can view inventory, add to cart, and checkout purchases.

## Directory Structure
```
app/
|-- static/               # Static assets (CSS, JS, images)
|-- templates/            # HTML templates
|-- routes.py             # Flask routes
|-- models.py             # Database models
|-- forms.py              # WTForms for authentication
|-- db.py                 # Database connections
|-- __init__.py           # Flask app initialization
```

## API Endpoints
- `GET /api/inventory` - Fetch all inventory items
- `POST /add_to_cart` - Add items to cart
- `GET /view_cart` - View current cart items
- `POST /checkout` - Complete a purchase

## Contributing
If you'd like to contribute, feel free to fork the repository and submit a pull request.

## License
This project is open-source and available under the [MIT License](LICENSE).


