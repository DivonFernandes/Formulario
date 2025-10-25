# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, Optional, ValidationError, NumberRange
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# --- Configuração ---
APP_START_DATE = os.environ.get("APP_START_DATE", "2025-11-01")  # AAAA-MM-DD
SECRET_KEY = os.environ.get("SECRET_KEY", "troque_esta_chave_para_producao")
DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///inscricoes.db")  # Produção: PostgreSQL/MySQL

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Modelo ---
class Inscricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(200), nullable=False)
    estado_civil = db.Column(db.String(50))
    sexo = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    endereco = db.Column(db.String(300))
    bairro = db.Column(db.String(150))
    cidade_estado = db.Column(db.String(150))
    telefone = db.Column(db.String(20))
    idade = db.Column(db.Integer)
    chefe_de_equipe = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Inscricao {self.cpf} - {self.nome}>"

# --- Utilitários ---
def limpar_cpf(cpf_str: str) -> str:
    return "".join([c for c in (cpf_str or "") if c.isdigit()])

def validar_cpf_algoritmo(cpf: str) -> bool:
    cpf = limpar_cpf(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    def calc(digs):
        s = sum(int(d) * w for d, w in zip(digs, range(len(digs)+1, 1, -1)))
        r = (s * 10) % 11
        return r if r < 10 else 0
    first = calc(cpf[:9])
    second = calc(cpf[:10])
    return first == int(cpf[9]) and second == int(cpf[10])

# --- Formulário ---
class InscricaoForm(FlaskForm):
    cpf = StringField("CPF", validators=[DataRequired(message="CPF obrigatório"),
                                         Regexp(r'^[\d\.\- ]+$', message="Apenas números (ou . - )")])
    nome = StringField("Nome", validators=[DataRequired(), Length(max=200)])
    estado_civil = SelectField("Estado Civil", choices=[
        ("", "—"), ("solteiro", "Solteiro(a)"), ("casado", "Casado(a)"),
        ("divorciado", "Divorciado(a)"), ("viuvo", "Viúvo(a)")
    ], validators=[Optional()])
    sexo = SelectField("Sexo", choices=[
        ("", "—"), ("M", "Masculino"), ("F", "Feminino"), ("O", "Outro")
    ], validators=[Optional()])
    data_nascimento = DateField("Data de Nascimento", format="%Y-%m-%d", validators=[Optional()])
    endereco = StringField("Endereço", validators=[Optional(), Length(max=300)])
    bairro = StringField("Bairro", validators=[Optional(), Length(max=150)])
    cidade_estado = StringField("Cidade – Estado", validators=[Optional(), Length(max=150)])
    telefone = StringField("Número de Telefone", validators=[
        Optional(), Regexp(r'^[\d\(\)\s\-\+]+$', message="Formato de telefone inválido")
    ])
    idade = IntegerField("Idade", validators=[Optional(), NumberRange(min=0, max=150)])
    chefe_de_equipe = SelectField("Chefe de Equipe?", choices=[("nao", "Não"), ("sim", "Sim")], validators=[Optional()])
    submit = SubmitField("Enviar")

    def validate_cpf(form, field):
        raw = field.data or ""
        cpf_norm = limpar_cpf(raw)
        if not validar_cpf_algoritmo(cpf_norm):
            raise ValidationError("CPF inválido.")
        field.data = cpf_norm

# --- Rotas ---
@app.route("/", methods=["GET", "POST"])
def index():
    form = InscricaoForm()
    start_date = datetime.strptime(APP_START_DATE, "%Y-%m-%d").date()
    hoje = date.today()

    if hoje < start_date:
        return render_template("bloqueado.html", start_date=start_date)

    if form.validate_on_submit():
        chefe = True if form.chefe_de_equipe.data == "sim" else False
        inscr = Inscricao(
            cpf=form.cpf.data,
            nome=form.nome.data,
            estado_civil=form.estado_civil.data,
            sexo=form.sexo.data,
            data_nascimento=form.data_nascimento.data,
            endereco=form.endereco.data,
            bairro=form.bairro.data,
            cidade_estado=form.cidade_estado.data,
            telefone=form.telefone.data,
            idade=form.idade.data,
            chefe_de_equipe=chefe
        )
        db.session.add(inscr)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("❌ CPF já cadastrado — não é permitido cadastrar o mesmo CPF duas vezes.", "danger")
            return render_template("register.html", form=form)

        flash("✅ Inscrição realizada com sucesso!", "success")
        return redirect(url_for("sucesso", cpf=inscr.cpf))

    return render_template("register.html", form=form)

@app.route("/sucesso")
def sucesso():
    cpf = request.args.get("cpf")
    return render_template("success.html", cpf=cpf)

# --- Inicialização do banco ---
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)