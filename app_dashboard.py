from flask import Flask, render_template_string, jsonify
import psycopg2

app = Flask(__name__)

# CONFIGURAÇÕES DO BANCO DE DADOS
HOST = "localhost"
PORTA = "5432"
BANCO = "Mercado"
USUARIO = "postgres"
SENHA = "j" 
# SENHA CONFORME CONSTA NA CONEXÃO DO DBEAVER

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Dashboard de Vendas - Mercado</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; margin: 0; padding: 25px; }
        h1 { color: #a6e3a1; text-align: center; margin-bottom: 30px; }
        .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background-color: #313244; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .card h3 { margin: 0; font-size: 14px; color: #89b4fa; text-transform: uppercase; }
        .card p { font-size: 28px; font-weight: bold; margin: 10px 0 0 0; color: #a6e3a1; }
        .grid-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .chart-container { background-color: #313244; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { color: #89b4fa; font-size: 18px; margin-top: 0; text-align: center; }
    </style>
</head>
<body>
    <h1>📊 Dashboard de Desempenho do Mercado</h1>

    <div class="grid-cards">
        <div class="card">
            <h3>Total de Vendas</h3>
            <p id="total_vendas">0</p>
        </div>
        <div class="card">
            <h3>Faturamento Total</h3>
            <p id="faturamento_total">R$ 0,00</p>
        </div>
    </div>

    <div class="grid-charts">
        <div class="chart-container">
            <h2>Top Produtos Mais Vendidos (Qtd)</h2>
            <canvas id="graficoProdutos"></canvas>
        </div>
        <div class="chart-container">
            <h2>Vendas por Funcionário (R$)</h2>
            <canvas id="graficoFuncionarios"></canvas>
        </div>
    </div>

    <script>
        async function carregarDashboard() {
            const res = await fetch('/api/dados_dashboard');
            const data = await res.json();

            document.getElementById('total_vendas').innerText = data.resumo.total_vendas;
            document.getElementById('faturamento_total').innerText = 'R$ ' + data.resumo.faturamento.toFixed(2);

            // Gráfico 1: Produtos Mais Vendidos
            new Chart(document.getElementById('graficoProdutos'), {
                type: 'bar',
                data: {
                    labels: data.produtos.map(p => p.nome),
                    datasets: [{
                        label: 'Unidades Vendidas',
                        data: data.produtos.map(p => p.qtd),
                        backgroundColor: '#89b4fa'
                    }]
                },
                options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
            });

            // Gráfico 2: Vendas por Funcionário
            new Chart(document.getElementById('graficoFuncionarios'), {
                type: 'pie',
                data: {
                    labels: data.funcionarios.map(f => f.nome),
                    datasets: [{
                        data: data.funcionarios.map(f => f.total),
                        backgroundColor: ['#a6e3a1', '#fab387', '#f38ba8', '#cba6f7']
                    }]
                }
            });
        }

        carregarDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/dados_dashboard')
def dados_dashboard():
    conexao = psycopg2.connect(host=HOST, port=PORTA, dbname=BANCO, user=USUARIO, password=SENHA)
    cursor = conexao.cursor()

    # 1. Resumo de Vendas e Faturamento
    cursor.execute("SELECT COUNT(cod_venda), COALESCE(SUM(valor_total), 0) FROM venda;")
    resumo_raw = cursor.fetchone()
    resumo = {"total_vendas": resumo_raw[0], "faturamento": float(resumo_raw[1])}

    # 2. Top Produtos Mais Vendidos
    cursor.execute("""
        SELECT p.nome, SUM(iv.quantidade) as total_qtd
        FROM item_venda iv
        JOIN produto p ON p.cod_produto = iv.cod_produto
        GROUP BY p.nome
        ORDER BY total_qtd DESC
        LIMIT 5;
    """)
    produtos = [{"nome": row[0], "qtd": int(row[1])} for row in cursor.fetchall()]

    # 3. Vendas por Funcionário
    cursor.execute("""
        SELECT f.nome, SUM(v.valor_total) as total_vendido
        FROM venda v
        JOIN funcionario f ON f.cod_funcionario = v.cod_funcionario
        GROUP BY f.nome
        ORDER BY total_vendido DESC;
    """)
    funcionarios = [{"nome": row[0], "total": float(row[1])} for row in cursor.fetchall()]

    cursor.close()
    conexao.close()

    return jsonify({"resumo": resumo, "produtos": produtos, "funcionarios": funcionarios})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
