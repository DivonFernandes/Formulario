# Inscricoes Flask

Projeto de exemplo para cadastro de inscrições com Flask, Bootstrap e validação de CPF.

## Como rodar

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt

set FLASK_APP=app.py
set FLASK_ENV=development
flask initdb
flask run
```

Abra http://127.0.0.1:5000
