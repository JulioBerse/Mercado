from flask import Flask, render_template_string, request, redirect, url_for, session
import psycopg2

app = Flask(__name__)

app.secret_key = 'uma_chave_bem_secreta_aqui' # Troque por algo aleatório


# CREDENCIAIS DO POSTGRESQL
HOST = "localhost"
PORTA = "5432"
BANCO = "postgres"
USUARIO = "postgres"
SENHA = "j"  # AJUSTE AQUI SUA SENHA

# TEMPLATE HTML PARA EXIBIR OS DADOS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Dashboard de Cotações - Aurora Linux</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; padding: 40px; }
        h1 { color: #89b4fa; text-align: center; }
        table { width: 80%; margin: 30px auto; border-collapse: collapse; background-color: #313244; }
        th, td { padding: 12px 15px; border: 1px solid #45475a; text-align: center; }
        th { background-color: #45475a; color: #a6e3a1; }
        tr:nth-child(even) { background-color: #181825; }
        .destaque { color: #f9e2af; font-weight: bold; }
    </style>
</head>
<body>
    <h1>📊 Painel de Cotações em Tempo Real</h1>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Moeda</th>
                <th>Valor (R$)</th>
                <th>Data / Hora</th>
            </tr>
        </thead>
        <tbody>
            {% for item in cotacoes %}
            <tr>
                <td>{{ item[0] }}</td>
                <td>{{ item[1] }}</td>
                <td class="destaque">R$ {{ "%.2f"|format(item[2]) }}</td>
                <td>{{ item[3].strftime('%d/%m/%Y %H:%M:%S') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

# TELA DE LOGIN EM HTML (Estilo Limpo e Profissional)
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Login - Grupo Yamasaki</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #2a2a3c; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 300px; text-align: center; }
        h2 { margin-bottom: 20px; color: #4CAF50; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #444; border-radius: 4px; background: #1e1e2e; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #4CAF50; border: none; border-radius: 4px; color: white; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:hover { background: #45a049; }
        .erro { color: #ff5555; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Grupo Yamasaki</h2>
        <form method="POST">
            <input type="text" name="login" placeholder="Usuário" required autocomplete="off">
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Entrar</button>
            {% if erro %}
                <div class="erro">{{ erro }}</div>
            {% endif %}
        </form>
    </div>
</body>
</html>
"""


@app.route('/')
def home():
    try:
        conexao = psycopg2.connect(
            host=HOST, port=PORTA, dbname=BANCO, user=USUARIO, password=SENHA
        )
        cursor = conexao.cursor()
        
        # Busca as últimas 15 cotações salvas no Postgres
        cursor.execute("SELECT id, moeda, valor, data_hora FROM cotacoes_dolar ORDER BY id DESC LIMIT 15;")
        cotacoes = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        return render_template_string(HTML_TEMPLATE, cotacoes=cotacoes)
    except Exception as e:
        return f"Erro ao carregar dados do Postgres: {e}"

if __name__ == '__main__':
    # Roda o servidor web na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
