import os
from flask import Flask
from routes.auth import auth_bp
from routes.caixa import caixa_bp
from routes.estoque import estoque_bp
from routes.fechamento import fechamento_bp

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "chave_secreta_super_segura_berse")

app.register_blueprint(auth_bp)
app.register_blueprint(caixa_bp)
app.register_blueprint(estoque_bp)
app.register_blueprint(fechamento_bp)

if __name__ == "__main__":
    app.run(debug=True)