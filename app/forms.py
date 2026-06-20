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
    EmailField,
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
from app.utils import parse_decimal_input
from datetime import datetime, date
from flask import current_app


class BrazilianDecimalField(FloatField):
    """FloatField que aceita entrada no formato brasileiro (ex.: 1.000,50)."""

    def process_formdata(self, valuelist):
        if not valuelist or valuelist[0] in (None, ""):
            self.data = None
            return
        try:
            self.data = parse_decimal_input(valuelist[0])
        except (ValueError, TypeError) as exc:
            self.data = None
            raise ValueError(
                self.gettext("Valor invalido. Use numeros como 1000,50 ou 150.75")
            ) from exc


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
            "class": "form-control bg-transparent text-white border-0 fw-bold",
            "id": "date",
        },  # Campo somente leitura
    )
    due_date = DateField(
        "Data de Vencimento", 
        validators=[Optional()],
        render_kw={"required": False}
    )  # Campo opcional para data de vencimento
    amount = StringField("Valor", validators=[DataRequired()])
    discount = StringField("Desconto", validators=[Optional()], default="0,00")
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
    conta_id = SelectField("Conta", coerce=int, validators=[Optional()])
    parcelado = BooleanField("Parcelas", default=False)
    numero_parcelas = IntegerField(
        "Número de Parcelas",
        validators=[Optional(), NumberRange(min=1, max=360)],
    )

    submit = SubmitField("Salvar")

    def validate_numero_parcelas(self, field):
        if self.parcelado.data and (not field.data or field.data < 1):
            raise ValidationError(
                "Informe o número de parcelas (mínimo 1) quando a opção Parcelas estiver marcada."
            )

    def validate_amount(self, amount):
        if not amount.data:
            raise ValidationError("O valor é obrigatório.")
        try:
            # O valor já vem formatado do JavaScript (ex: "150.00")
            float_value = float(amount.data)
            if float_value <= 0:
                raise ValidationError("O valor deve ser maior que zero.")
            # Mantém o valor exatamente como recebido
            self.amount.data = amount.data
        except ValueError:
            raise ValidationError(
                "Formato de valor inválido. Use números com vírgula (ex: 1.600,00)"
            )

    def validate_discount(self, discount):
        if not discount.data:
            self.discount.data = "0.00"
            return
        try:
            # O valor já vem formatado do JavaScript (ex: "75.00")
            float_value = float(discount.data)
            if float_value < 0:
                raise ValidationError("O desconto não pode ser negativo.")
            # Mantém o valor exatamente como recebido
            self.discount.data = discount.data
        except ValueError:
            raise ValidationError(
                "Formato de valor inválido. Use números com vírgula (ex: 100,00)"
            )


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


class ProfileForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField("Senha Atual", validators=[DataRequired()])
    new_password = PasswordField(
        "Nova Senha",
        validators=[
            Optional(),
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres"),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar Nova Senha",
        validators=[EqualTo("new_password", message="As senhas não conferem")],
    )
    submit = SubmitField("Salvar Alterações")


class AdminUserForm(FlaskForm):
    user_id = SelectField("Usuário", coerce=int, validators=[DataRequired()])
    username = StringField("Nome de usuário", validators=[DataRequired(), Length(min=3, max=20)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Nova Senha",
        validators=[Optional(), Length(min=6, message="A senha deve ter pelo menos 6 caracteres")],
    )
    confirm_password = PasswordField(
        "Confirmar Nova Senha",
        validators=[EqualTo("password", message="As senhas não conferem")],
    )
    submit = SubmitField("Salvar Usuário")

    def validate_username(self, username):
        existing = User.query.filter_by(username=username.data).first()
        if existing and existing.id != self.user_id.data:
            raise ValidationError(
                "Este nome de usuário já está em uso. Por favor, escolha outro."
            )

    def validate_email(self, email):
        existing = User.query.filter_by(email=email.data).first()
        if existing and existing.id != self.user_id.data:
            raise ValidationError(
                "Este email já está registrado. Por favor, use outro."
            )


class ContaForm(FlaskForm):
    nome = StringField("Nome da Conta", validators=[DataRequired(), Length(max=100)])
    tipo_id = SelectField("Tipo de Conta", coerce=int, validators=[DataRequired()])
    saldo_inicial = BrazilianDecimalField("Saldo Inicial", validators=[Optional()], default=0.0)
    submit = SubmitField("Adicionar")

class InvestimentoForm(FlaskForm):
    submit = SubmitField("Adicionar")


class MovimentacaoInvestimentoForm(FlaskForm):
    data_movimentacao = DateField("Data da Movimentação", validators=[DataRequired()])
    tipo_movimentacao = SelectField(
        "Tipo de Movimentação",
        choices=[
            ("aplicacao", "Aplicação"),
            ("resgate", "Resgate"),
            ("rendimento", "Rendimento")
        ],
        validators=[DataRequired()]
    )
    valor = FloatField("Valor", validators=[DataRequired()])
    observacoes = TextAreaField("Observações", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Salvar")


class TipoInvestimentoForm(FlaskForm):
    nome = StringField("Nome do Tipo", validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField("Descrição", validators=[Optional(), Length(max=200)])
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class TipoContaForm(FlaskForm):
    nome = StringField("Nome do Tipo", validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField("Descrição", validators=[Optional(), Length(max=200)])
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")
