from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Fixed deprecated function


DATASET_PATH = "C:\\Users\\TecQnio\\OneDrive\\Desktop\\Tello\\water data foot print\\daily_water_usage.csv"
df = pd.read_csv(DATASET_PATH) if os.path.exists(DATASET_PATH) else None

DATASET_PATH1 = r"C:\Users\TecQnio\OneDrive\Desktop\Tello\water data foot print - Copy\water_footprint.csv"
df1 = pd.read_csv(DATASET_PATH1) if os.path.exists(DATASET_PATH1) else None


water_data = {
    "shower": {"avg_usage": 50, "recommended": 35, "tip": "Take shorter showers to save water."},
    "toilet": {"avg_usage": 10, "recommended": 6, "tip": "Use a dual-flush toilet to reduce water waste."},
    "washing_machine": {"avg_usage": 60, "recommended": 45, "tip": "Run full loads to maximize water efficiency."},
    "dishwasher": {"avg_usage": 20, "recommended": 15, "tip": "Use an eco-mode setting for better efficiency."},
    "garden_watering": {"avg_usage": 30, "recommended": 20, "tip": "Water plants early in the morning or late evening."}
}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        return jsonify({'message': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)


@app.route('/save_water', methods=['POST'])
@login_required
def save_water():
    water_type = request.form.get('water_type', "").strip().lower().replace(" ", "_")
    water_amount = request.form.get('water_amount')

    if not water_type or not water_amount:
        return jsonify({"error": "Missing input data!"}), 400

    if water_type not in water_data:
        return jsonify({"error": f"Invalid water type '{water_type}'. Please use: {', '.join(water_data.keys())}"}), 400

    try:
        water_amount = float(water_amount)
        avg_usage = water_data[water_type]["avg_usage"]
        recommended_usage = water_data[water_type]["recommended"]
        
        
        if water_amount > recommended_usage:
            savings = round(water_amount - recommended_usage, 2)
        else:
            savings = 0  

        tip = water_data[water_type]["tip"]

        return jsonify({
            "water_type": water_type.replace("_", " ").title(),
            "water_amount": water_amount,
            "average_usage": avg_usage,
            "recommended_usage": recommended_usage,
            "savings": savings,
            "tip": tip if savings > 0 else "Great job! Your water usage is efficient."
        })

    except ValueError:
        return jsonify({"error": "Invalid water amount! Must be a number."}), 400
    
@app.route('/chart')
@login_required
def chart():
    return render_template('chart.html', username=current_user.username)

@app.route('/get_water_data')
@login_required
def get_water_data():
    if df1 is None:
        return jsonify({"error": "No data available"}), 404
    
    categories = df1['Category'].unique().tolist()
    usage = [int(df1[df1['Category'] == category]['Water_Usage_Liters'].sum()) for category in categories]  # Convert to int
    
    return jsonify({"categories": categories, "usage": usage})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'message': 'User already exists'}), 400

        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  

    return render_template('register.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
