from flask import Flask, request, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ---------------- CONFIG ----------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quanlynhahang.db'
app.config['SECRET_KEY'] = 'sieu_bao_mat_2026'

db = SQLAlchemy(app)

# ---------------- USER ----------------

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

# ---------------- FOOD ----------------

class Food(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    price = db.Column(
        db.Integer
    )

    image = db.Column(
        db.String(255)
    )

# ---------------- CREATE DATABASE ----------------

with app.app_context():

    db.create_all()

    if Food.query.count() == 0:

        foods = [

            Food(
                name="Phở Bò",
                description="Phở bò tái nạm đặc biệt",
                price=50000,
                image="pho.jpg"
            ),

            Food(
                name="Cơm Tấm",
                description="Cơm tấm sườn bì chả",
                price=45000,
                image="comtam.jpg"
            ),

            Food(
                name="Bún Chả",
                description="Bún chả Hà Nội",
                price=40000,
                image="buncha.jpg"
            )
        ]

        db.session.add_all(foods)
        db.session.commit()

# ---------------- HOME ----------------

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']

        user_exists = User.query.filter_by(
            username=username
        ).first()

        if user_exists:
            return "Tài khoản đã tồn tại!"

        new_user = User(
            username=username,
            password=password,
            email=email,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return "Đăng ký thành công"

    return render_template('register.html')

# ---------------- LOGIN ----------------

@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(
        username=username,
        password=password
    ).first()

    if not user:
        return "Sai tài khoản hoặc mật khẩu"

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    if user.role == "customer":
        return redirect('/customer/menu')

    return redirect('/restaurant/dashboard')

# ---------------- CUSTOMER MENU ----------------

@app.route('/customer/menu')
def customer_menu():

    foods = Food.query.all()

    return render_template(
        'customer_menu.html',
        foods=foods
    )

# ---------------- FOOD DETAIL ----------------

@app.route('/food/<int:id>')
def food_detail(id):

    food = Food.query.get_or_404(id)

    return render_template(
        'food_detail.html',
        food=food
    )

# ---------------- ADD CART ----------------

@app.route('/add-cart/<int:id>', methods=['POST'])
def add_cart(id):

    quantity = int(
        request.form['quantity']
    )

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({

        'food_id': id,

        'quantity': quantity

    })

    session.modified = True

    return redirect('/cart')

# ---------------- CART ----------------

@app.route('/cart')
def cart():

    cart_data = session.get(
        'cart',
        []
    )

    items = []

    total = 0

    for item in cart_data:

        food = Food.query.get(
            item['food_id']
        )

        subtotal = (
            food.price *
            item['quantity']
        )

        total += subtotal

        items.append({

            'food': food,

            'quantity':
            item['quantity'],

            'subtotal':
            subtotal

        })

    return render_template(
        'cart.html',
        items=items,
        total=total
    )
# ---------------- REMOVE CART ----------------

@app.route('/remove-cart/<int:index>')
def remove_cart(index):

    cart = session.get('cart', [])

    if index < len(cart):
        cart.pop(index)

    session['cart'] = cart
    session.modified = True

    return redirect('/cart')


# ---------------- CHECKOUT ----------------

@app.route('/checkout')
def checkout():

    session['cart'] = []

    return render_template(
        'checkout_success.html'
    )


# ---------------- SEARCH FOOD ----------------

@app.route('/search')
def search():

    keyword = request.args.get(
        'keyword',
        ''
    )

    foods = Food.query.filter(
        Food.name.contains(keyword)
    ).all()

    return render_template(
        'customer_menu.html',
        foods=foods
    )
# ---------------- CUSTOMER DASHBOARD ----------------

@app.route('/customer/dashboard')
def customer_dashboard():

    if (
        'role' not in session or
        session['role'] != 'customer'
    ):
        return redirect('/')

    return redirect('/customer/menu')

# ---------------- RESTAURANT DASHBOARD ----------------

@app.route('/restaurant/dashboard')
def restaurant_dashboard():

    if (
        'role' not in session or
        session['role'] != 'restaurant'
    ):
        return redirect('/')

    return f"""
    <h1>Chào {session['username']} (Nhà hàng)</h1>

    <a href='/logout'>
        Đăng xuất
    </a>
    """

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)