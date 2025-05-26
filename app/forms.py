from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    SelectField,
    FloatField,
    DateField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    NumberRange,
    Optional,
)
from app.models import Category, User, PaymentMethod
from datetime import datetime, date
from flask import current_app


class RegistrationForm(FlaskForm):
    username = StringField(
        "Nome de Usuário", validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Confirmar Senha", validators=[DataRequired(), EqualTo("password")]
    )

    submit = SubmitField("Registrar")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "Este nome de usuário já está em uso. Por favor, escolha outro."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(
                "Este email já está registrado. Por favor, use outro ou faça login."
            )


class LoginForm(FlaskForm):
    username = StringField("Nome de Usuário", validators=[DataRequired()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember_me = BooleanField("Lembrar-me")
    submit = SubmitField("Entrar")


class SecureDataForm(FlaskForm):
    data = StringField("Data", validators=[DataRequired()])
    submit = SubmitField("Save")


class CategoryForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=64)])
    type = SelectField(
        "Tipo",
        choices=[("receita", "Receita"), ("despesa", "Despesa")],
        validators=[DataRequired()],
    )
    icon = StringField("Ícone", validators=[Optional(), Length(max=50)])
    color = StringField("Cor", validators=[Optional(), Length(max=20)])
    exclusive = BooleanField("Exclusivo", default=False)
    submit = SubmitField("Cadastrar")


class ExpenseForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=64)])
    category_id = SelectField("Categoria", coerce=int, validators=[Optional()])
    submit = SubmitField("Cadastrar")


class PaymentMethodForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=64)])
    is_active = BooleanField("Ativo", default=True)

    submit = SubmitField("Salvar")


class TransactionForm(FlaskForm):
    date = DateField(
        default=datetime.today,
        render_kw={
            "readonly": True,
            "class": "form-control transparent-white",
        },  # Campo somente leitura
    )
    due_date = DateField(
        "Data de Vencimento", validators=[Optional()]
    )  # Campo opcional para data de vencimento
    amount = FloatField("Valor", validators=[DataRequired(), NumberRange(min=0.01)])
    discount = FloatField(
        "Desconto", validators=[Optional(), NumberRange(min=0)], default=0.0
    )
    type = SelectField(
        "Tipo",
        choices=[("receita", "Receita"), ("despesa", "Despesa")],
        default="receita",
    )
    category_id = SelectField("Categoria", coerce=int, validators=[Optional()])
    expense_id = SelectField("Descrição", coerce=int, validators=[Optional()])
    description = StringField(
        "Descrição", validators=[Optional(), Length(max=500)]
    )  # Campo para descrição manual
    payment_method_id = SelectField(
        "Forma de Pagamento", coerce=int, validators=[Optional()]
    )
    payment_date = DateField("Data de Pagamento", validators=[Optional()])
    paid = BooleanField("Pago", default=False)
    recurrence = SelectField(
        "Recorrência",
        choices=[
            ("nenhuma", "Nenhuma"),
            ("diaria", "Diária"),
            ("semanal", "Semanal"),
            ("mensal", "Mensal"),
        ],
        validators=[Optional()],
    )
    details = TextAreaField("Detalhes", validators=[Optional(), Length(max=500)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=500)])

    submit = SubmitField("Salvar")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Solicitar Recuperação de Senha")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError(
                "Não existe uma conta com este email. Por favor, verifique o email ou registre-se."
            )


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nova Senha", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Confirmar Nova Senha", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Redefinir Senha")
