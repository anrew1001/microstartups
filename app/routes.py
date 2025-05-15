from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from app import db
from app.models import User, Startup
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from email_validator import validate_email, EmailNotValidError

routes_bp = Blueprint('routes', __name__, url_prefix='')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@routes_bp.route('/')
def index():
    startups = Startup.query.all()
    return render_template('index.html', startups=startups)

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            flash(f'Недействительный email: {str(e)}', 'danger')
            return redirect(url_for('routes.register'))
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Имя пользователя уже занято.', 'danger')
            return redirect(url_for('routes.register'))
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email уже зарегистрирован.', 'danger')
            return redirect(url_for('routes.register'))
        new_user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('routes.index'))
        flash('Неверный email или пароль.', 'danger')
    return render_template('login.html')

@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@routes_bp.route('/startup/new', methods=['GET', 'POST'])
@login_required
def startup_form():
    print("Startup form accessed")
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name or not description:
            flash('Название и описание обязательны.', 'danger')
            return redirect(url_for('routes.startup_form'))
        if 'logo' not in request.files:
            print("No logo file part in the request")
            flash('Файл логотипа не выбран.', 'danger')
            return redirect(url_for('routes.startup_form'))
        logo = request.files['logo']
        logo_filename = None
        # Используем /tmp для Render
        upload_folder = os.environ.get('UPLOAD_FOLDER', '/tmp') if os.environ.get('RENDER') else current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print(f"Created directory: {upload_folder}")
        if logo and allowed_file(logo.filename):
            if logo.filename == '':
                print("No selected file")
                flash('Файл не выбран.', 'danger')
                return redirect(url_for('routes.startup_form'))
            base_filename = os.path.basename(logo.filename)
            safe_filename = ''.join(c for c in base_filename if c.isalnum() or c in '._-')[:50]
            logo_filename = f"{current_user.id}_{safe_filename}"
            file_path = os.path.join(upload_folder, logo_filename)
            try:
                logo.save(file_path)
                print(f"Logo successfully saved as: {logo_filename} at {file_path}")
                if not os.path.exists(file_path):
                    print(f"File {file_path} does not exist after saving")
                    flash('Ошибка: файл не был сохранён на сервере.', 'danger')
                    return redirect(url_for('routes.startup_form'))
                with open(file_path, 'rb') as f:
                    f.read(1)
                    print(f"File {file_path} is readable")
            except Exception as e:
                print(f"Error saving or accessing logo: {e}")
                flash(f'Ошибка при сохранении или доступе к файлу: {e}', 'danger')
                return redirect(url_for('routes.startup_form'))
        else:
            print("Logo file not provided or not allowed")
            flash('Недопустимый формат файла. Разрешены только .png, .jpg, .jpeg, .gif.', 'danger')
            return redirect(url_for('routes.startup_form'))
        startup = Startup(name=name, description=description, logo=logo_filename, owner=current_user)
        db.session.add(startup)
        db.session.commit()
        flash('Стартап успешно добавлен!', 'success')
        return redirect(url_for('routes.index'))
    return render_template('startup_form.html')

@routes_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    print(f"Search accessed with query: {query}")
    if not query:
        flash('Введите запрос для поиска.', 'warning')
        return redirect(url_for('routes.index'))
    try:
        startups = Startup.query.filter(
            (Startup.name.ilike(f'%{query}%')) | (Startup.description.ilike(f'%{query}%'))
        ).all()
        print(f"Found {len(startups)} startups matching query: {query}")
    except Exception as e:
        print(f"Error during search: {e}")
        flash('Ошибка при выполнении поиска.', 'danger')
        return redirect(url_for('routes.index'))
    return render_template('startup_list.html', startups=startups, query=query)