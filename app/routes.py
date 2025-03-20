from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Transaction, Category
from app.forms import LoginForm, RegistrationForm, TransactionForm, CategoryForm
from datetime import datetime

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Home')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate total income and expenses
    income = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='income').scalar() or 0
    expenses = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='expense').scalar() or 0
    balance = income - expenses
    
    return render_template('dashboard.html', title='Dashboard', 
                          transactions=recent_transactions,
                          income=income, expenses=expenses, balance=balance)

@main_bp.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    form = TransactionForm()
    # Populate category choices
    form.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            type=form.type.data,
            category_id=form.category.data,
            user_id=current_user.id,
            date=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!')
        return redirect(url_for('main.transactions'))
    
    # Get all transactions
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    return render_template('transactions.html', title='Transactions', 
                          form=form, transactions=transactions)

@main_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!')
        return redirect(url_for('main.categories'))
    
    # Get all categories
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template('categories.html', title='Categories', 
                          form=form, categories=categories)

@main_bp.route('/reports')
@login_required
def reports():
    # Get monthly income and expenses
    income_by_month = db.session.query(
        db.func.strftime('%Y-%m', Transaction.date).label('month'),
        db.func.sum(Transaction.amount).label('total')
    ).filter_by(user_id=current_user.id, type='income').group_by('month').all()
    
    expenses_by_month = db.session.query(
        db.func.strftime('%Y-%m', Transaction.date).label('month'),
        db.func.sum(Transaction.amount).label('total')
    ).filter_by(user_id=current_user.id, type='expense').group_by('month').all()
    
    # Get expenses by category
    expenses_by_category = db.session.query(
        Category.name,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense'
    ).group_by(Category.name).all()
    
    return render_template('reports.html', title='Reports',
                          income_by_month=income_by_month,
                          expenses_by_month=expenses_by_month,
                          expenses_by_category=expenses_by_category)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)
