from flask import Flask, request, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CẤU HÌNH ỨNG DỤNG ---
UPLOAD_FOLDER = os.path.join('static', 'food')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quanlynhahang.db'
app.config['SECRET_KEY'] = 'sieu_bao_mat_2026'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- KHỞI TẠO DATABASE ---
db = SQLAlchemy(app)

# --- MODELS CƠ SỞ DỮ LIỆU ---

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text)
    image = db.Column(db.String(255), default='default_staff.jpg')

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    issuer = db.Column(db.String(150))
    image = db.Column(db.String(255))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    image = db.Column(db.String(255))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'))
    username = db.Column(db.String(100))
    star = db.Column(db.Integer)
    comment = db.Column(db.Text)
    reply = db.Column(db.Text, nullable=True)

# --- KHỞI TẠO DỮ LIỆU MẪU ---
with app.app_context():
    db.create_all()
    # tự thêm cột reply nếu database cũ chưa có
    try:
        db.session.execute(db.text(
            "ALTER TABLE review ADD COLUMN reply TEXT"
        ))
        db.session.commit()
    except:
        db.session.rollback()
    if Food.query.count() == 0:
        foods = [
            Food(name="Phở Bò", description="Phở bò tái nạm đặc biệt", price=50000, image="pho.jpg"),
            Food(name="Cơm Tấm", description="Cơm tấm sườn bì chả", price=45000, image="comtam.jpg"),
            Food(name="Bún Chả", description="Bún chả Hà Nội", price=40000, image="buncha.jpg")
        ]
        db.session.add_all(foods)
        db.session.commit()

# --- CÁC ROUTE ĐIỀU HƯỚNG ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return "Tài khoản đã tồn tại!"

        new_user = User(username=username, password=password, email=email, role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            return "Sai tài khoản hoặc mật khẩu"

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        if user.role == "customer":
            return redirect(url_for('customer_menu'))
        if user.role == "restaurant":
            return redirect(url_for('restaurant_dashboard'))

        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/customer/menu')
def customer_menu():
    foods = Food.query.all()
    return render_template('customer_menu.html', foods=foods)

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    foods = Food.query.filter(Food.name.contains(keyword)).all()
    return render_template('customer_menu.html', foods=foods)

@app.route('/food/<int:id>')
def food_detail(id):
    food = Food.query.get_or_404(id)
    return render_template('food_detail.html', food=food)

@app.route('/add-cart/<int:id>', methods=['POST'])
def add_cart(id):
    quantity = int(request.form['quantity'])
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({'food_id': id, 'quantity': quantity})
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_data = session.get('cart', [])
    items = []
    total = 0

    for item in cart_data:
        food = db.session.get(Food, item['food_id'])
        if food:
            subtotal = food.price * item['quantity']
            total += subtotal
            items.append({
                'food': food,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
    return render_template('cart.html', items=items, total=total)

@app.route('/customer/dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))
    return redirect(url_for('customer_menu'))

@app.route('/restaurant/dashboard')
def restaurant_dashboard():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    all_foods = Food.query.all()
    all_staff = Staff.query.all()
    all_certs = Certificate.query.all()
    all_reviews = Review.query.all()

    return render_template(
        'restaurant_dashboard.html',
        foods=all_foods,
        staff=all_staff,
        certs=all_certs,
        reviews=all_reviews
    )

# --- QUẢN LÝ MÓN ĂN ---

@app.route('/restaurant/food/add', methods=['POST'])
def add_food():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    name = request.form.get('name')
    description = request.form.get('description')
    price = int(request.form.get('price', 0))
    file = request.files.get('image')

    image_name = 'pho.jpg'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_name = filename

    new_food = Food(name=name, description=description, price=price, image=image_name)
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

@app.route('/restaurant/food/edit/<int:food_id>', methods=['POST'])
def edit_food(food_id):
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    food = Food.query.get_or_404(food_id)
    food.name = request.form.get('name')
    food.description = request.form.get('description')
    food.price = int(request.form.get('price', 0))

    file = request.files.get('image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        food.image = filename

    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

@app.route('/restaurant/food/delete/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    food = Food.query.get_or_404(food_id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

# --- QUẢN LÝ NHÂN SỰ ---

@app.route('/restaurant/staff/add', methods=['POST'])
def add_staff():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    name = request.form.get('name')
    role = request.form.get('role')
    bio = request.form.get('bio')
    file = request.files.get('image')

    image_name = 'default_staff.jpg'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_name = filename

    new_staff = Staff(name=name, role=role, bio=bio, image=image_name)
    db.session.add(new_staff)
    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

@app.route('/restaurant/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

# --- QUẢN LÝ CHỨNG CHỈ / THÀNH TÍCH ---

@app.route('/restaurant/certificate/add', methods=['POST'])
def add_certificate():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    title = request.form.get('title')
    issuer = request.form.get('issuer')
    file = request.files.get('image')

    image_name = 'default_cert.jpg'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_name = filename

    new_cert = Certificate(title=title, issuer=issuer, image=image_name)
    db.session.add(new_cert)
    db.session.commit()

    return redirect(url_for('restaurant_dashboard'))

# --- TRẢ LỜI ĐÁNH GIÁ ---

@app.route('/restaurant/review/reply/<int:review_id>', methods=['POST'])
def reply_review(review_id):
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))

    review = Review.query.get_or_404(review_id)
    reply_content = request.form.get('reply')

    review.reply = reply_content
    db.session.commit()
    return redirect(url_for('restaurant_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)