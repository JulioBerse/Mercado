from flask import Flask, render_template_string
import psycopg2

app = Flask(__name__)

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
