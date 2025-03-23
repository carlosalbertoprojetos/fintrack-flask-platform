from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from app.models import User
from datetime import datetime, date

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email já está registrado. Por favor, use outro ou faça login.')

class TransactionForm(FlaskForm):
    date = DateField('Data', default=datetime.today, validators=[DataRequired()])
    description = StringField('Descrição', validators=[DataRequired(), Length(max=128)])
    description_id = SelectField('Descrição Predefinida', coerce=int, validators=[Optional()])
    amount = FloatField('Valor', validators=[DataRequired(), NumberRange(min=0.01)])
    type = SelectField('Tipo', choices=[('income', 'Receita'), ('expense', 'Despesa')], validators=[DataRequired()])
    category_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    paid = BooleanField('Pago', default=True)
    notes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Salvar')

class CategoryForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=64)])
    type = SelectField('Tipo', choices=[('income', 'Receita'), ('expense', 'Despesa')], validators=[DataRequired()])
    icon = StringField('Ícone', validators=[Optional(), Length(max=50)])
    color = StringField('Cor', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Salvar')

class ExpenseForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=64)])
    exclusive = SelectField('Exclusivo para', choices=[
        ('', 'Ambos'),
        ('income', 'Receitas'),
        ('expense', 'Despesas')
    ], validators=[Optional()])
    
    submit = SubmitField('Salvar')

