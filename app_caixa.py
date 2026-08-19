import os
from flask import Flask, render_template_string, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

# CONFIGURAÇÕES DO BANCO DE DADOS
HOST = "localhost"
PORTA = "5432"
BANCO = "Mercado"
USUARIO = "postgres"
SENHA = "j"  # COLOQUE SUA SENHA DO POSTGRESQL AQUI

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Berse Supermercados - PDV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; background-color: #f4f4f9; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
        button { margin-top: 15px; width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #28a745; text-decoration: none; font-weight: bold; }
        .msg { margin-top: 15px; padding: 10px; background: #e2e3e5; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
        <h1>Frente de Caixa (PDV)</h1>
        <form method="POST" action="/registrar_venda">
            <label for="codigo_barra">Código de Barras:</label>
            <input type="text" id="codigo_barra" name="codigo_barra" required>

            <label for="quantidade">Quantidade:</label>
            <input type="number" id="quantidade" name="quantidade" value="1" required min="1">

            <button type="submit">Registrar Venda</button>
        </form>

        {% if erro %}
            <div class="msg" style="color: red;">{{ erro }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Entrada de Estoque - Berse Supermercados</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; background-color: #f4f4f9; }
        .container { max-width: 500px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
        button { margin-top: 15px; width: 100%; padding: 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #218838; }
        .msg { margin-top: 15px; padding: 10px; background: #e2e3e5; border-radius: 4px; }
        .voltar { display: inline-block; margin-top: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Entrada de Estoque</h1>
        <form method="POST">
            <label for="codigo_barra">Código de Barras do Produto:</label>
            <input type="text" id="codigo_barra" name="codigo_barra" required>

            <label for="quantidade">Quantidade a Adicionar:</label>
            <input type="number" id="quantidade" name="quantidade" required min="1">

            <button type="submit">Adicionar ao Estoque</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}

        <br>
        <a class="voltar" href="/">← Voltar para o PDV (Frente de Caixa)</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_CAIXA)

@app.route('/registrar_venda', methods=['POST'])
def registrar_venda():
    try:
        codigo_barra = request.form.get('codigo_barra')
        quantidade = int(request.form.get('quantidade'))

        db_url = os.environ.get('DATABASE_URL', f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute(
            "UPDATE produto SET estoque = estoque - %s WHERE codigo_barra = %s",
            (quantidade, codigo_barra)
        )
        conn.commit()
        cur.close()
        conn.close()

        return render_template_string(HTML_CAIXA, msg="Venda registrada com sucesso!")
    except Exception as e:
        return render_template_string(HTML_CAIXA, erro=f"Erro ao salvar venda: {e}")

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    mensagem = None

    if request.method == 'POST':
        codigo_barra = request.form.get('codigo_barra')
        quantidade = int(request.form.get('quantidade'))

        db_url = os.environ.get('DATABASE_URL', f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute(
            "UPDATE produto SET estoque = estoque + %s WHERE codigo_barra = %s",
            (quantidade, codigo_barra)
        )
        conn.commit()

        if cur.rowcount > 0:
            mensagem = f"Sucesso! Adicionadas {quantidade} unidades ao produto."
        else:
            mensagem = "Erro: Produto não encontrado com esse código!"

        cur.close()
        conn.close()

    return render_template_string(HTML_ESTOQUE, msg=mensagem)

if __name__ == '__main__':
    app.run(debug=True)