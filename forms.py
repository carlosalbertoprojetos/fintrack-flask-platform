from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    FloatField,
    SubmitField,
    DateTimeField,
    TextAreaField,
    IntegerField,
    BooleanField,
)
from wtforms.validators import DataRequired


class GrupoForm(FlaskForm):
    nome = StringField("Nome do Grupo", validators=[DataRequired()])
    exclusivo = SelectField('Exclusivo', choices=[('Receita', 'Receita'), ('Despesa', 'Despesa')], default=None)
    submit = SubmitField("Cadastrar")


class DescricaoForm(FlaskForm):
    nome = StringField('Nome da Descrição', validators=[DataRequired()])
    grupo_id = SelectField('Grupo', coerce=int, choices=[])  # A lista de grupos será preenchida dinamicamente.


class TransacaoForm(FlaskForm):
    tipo = SelectField(
        "Tipo",
        choices=[("Receita", "Receita"), ("Despesa", "Despesa")],
        validators=[DataRequired()],
    )
    grupo = SelectField("Grupo", coerce=int, choices=[], validators=[DataRequired()])
    descricao = SelectField(
        "Descrição", coerce=int, choices=[], validators=[DataRequired()]
    )
    valor = FloatField("Valor", validators=[DataRequired()])
    data_pgto = DateTimeField(
        "Data de Pagamento", format="%Y-%m-%d %H:%M:%S", validators=[DataRequired()]
    )
    forma_pgto = SelectField(
        "Forma de Pagamento", coerce=int, choices=[], validators=[DataRequired()]
    )
    detalhes = TextAreaField("Detalhes")
    submit = SubmitField("Registrar")
