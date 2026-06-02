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

# Trang đăng ký
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
        return "Đăng ký thành công! Bạn có thể quay lại trang chủ để Đăng nhập."
        
    return render_template('register.html')

# Xử lý đăng nhập
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    user = User.query.filter_by(username=username, password=password).first()
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        if user.role == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif user.role == 'restaurant':
            return redirect(url_for('restaurant_dashboard'))
    else:
        return "Sai tài khoản hoặc mật khẩu rồi!"

# Giao diện Khách hàng
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('index'))
    return f"<h1>Chào {session['username']} (Khách hàng)!</h1><p></p><a href='/logout'>Đăng xuất</a>"

# Giao diện Nhà hàng
@app.route('/restaurant/dashboard')
def restaurant_dashboard():
    if 'role' not in session or session['role'] != 'restaurant':
        return redirect(url_for('index'))
    return f"<h1>Chào {session['username']} (Nhà hàng)!</h1><p></p><a href='/logout'>Đăng xuất</a>"

# Đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)