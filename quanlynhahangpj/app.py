from flask import Flask, request, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- CẤU HÌNH ỨNG DỤNG ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quanlynhahang.db'
app.config['SECRET_KEY'] = 'sieu_bao_mat_2026'

# --- KHỞI TẠO DATABASE ---
db = SQLAlchemy(app)

# --- MODEL USER ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'customer' hoặc 'restaurant'

# Tạo bảng tự động trong context
with app.app_context():
    db.create_all()

# --- CÁC ROUTE ĐIỀU HƯỚNG ---

# Trang chủ giới thiệu
@app.route('/')
def index():
    return render_template('index.html')

# Thay thế hàm register cũ trong app.py bằng hàm này:
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return "Tài khoản hoặc Email đã tồn tại!"
            
        new_user = User(username=username, password=password, email=email, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        # --- TỰ ĐỘNG ĐĂNG NHẬP NGAY SAU KHI ĐĂNG KÝ THÀNH CÔNG ---
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = new_user.role
        
        # Điều hướng thẳng vào Dashboard tương ứng luôn
        if new_user.role == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif new_user.role == 'restaurant':
            return redirect(url_for('restaurant_dashboard'))
        
    return render_template('register.html')


# Đồng thời chỉnh sửa lại 2 hàm hiển thị trang Dashboard để nó gọi file HTML thay vì chuỗi chữ thô:
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))
    return render_template('customerux.html') # Gọi file giao diện khách

@app.route('/restaurant/dashboard')
def restaurant_dashboard():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))
    return render_template('restaurantux.html') # Gọi file giao diện nhà hàng