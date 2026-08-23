import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_berse"

TABELA_PRODUTO = "produto"
TABELA_USUARIO = "usuario"
TABELA_VENDAS = "vendas"

def conectar_banco():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("A variável de ambiente DATABASE_URL não está configurada!")
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    return psycopg2.connect(db_url, sslmode='require')

# ==========================================
# 1. TEMPLATES HTML
# ==========================================

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
   <meta charset="UTF-8">
   <title>Login - Grupo Yamasaki PDV</title>
   <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .login-card { background: #ffffff; width: 100%; max-width: 400px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #007bff; text-align: center; margin-top: 0; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .msg { margin-top: 15px; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; background: #ffebee; color: #c62828; }
   </style>
</head>
<body>
   <div class="login-card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 36px; height: 36px; background-color: #bc002d; border-radius: 50%; line-height: 36px; color: white; font-weight: bold; font-size: 16px; margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <p style="text-align: center; color: #666; font-size: 14px;">Faça login para acessar o PDV</p>
        
        <form method="POST">
            <label for="username">Usuário:</label>
            <input type="text" id="username" name="username" required autofocus>
            
            <label for="password">Senha:</label>
            <input type="password" id="password" name="password" required>
            
            <button type="submit">Entrar</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
   </div>
</body>
</html>
"""

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Berse Supermercados - PDV</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            min-height: 100vh;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            box-sizing: border-box;
        }
        .main-container { display: flex; gap: 20px; align-items: flex-start; max-width: 1050px; width: 100%; justify-content: center; }
        .cart-card { background: #ffffff; width: 100%; max-width: 400px; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
        .cart-card h3 { color: #007bff; margin-top: 0; font-size: 16px; border-bottom: 2px solid #007bff; padding-bottom: 8px; }
        .items-table-container { overflow-y: auto; max-height: 350px; margin-top: 10px; border: 1px solid #eee; border-radius: 6px; }
        .items-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .items-table th, .items-table td { padding: 8px; text-align: left; border-bottom: 1px solid #f0f2f5; }
        .items-table th { background: #f8f9fa; color: #666; position: sticky; top: 0; }
        .card { background: #ffffff; width: 100%; max-width: 550px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        label { display: block; margin-top: 12px; font-weight: 600; color: #444; font-size: 14px; }
        input, select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 14px; background-color: #fff; }
        input:focus, select:focus { border-color: #007bff; outline: none; }
        button { margin-top: 15px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #0056b3; }
        .btn-success { background-color: #28a745; }
        .btn-success:hover { background-color: #218838; }
        .btn-danger { background-color: #dc3545; font-size: 13px; padding: 8px; margin-top: 8px; }
        .btn-danger:hover { background-color: #c82333; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 12px; margin-top: 12px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 15px; }
        .info-row strong { color: #333; }
        .total-box { font-size: 18px; color: #28a745; border-top: 2px solid #28a745; padding-top: 8px; margin-top: 8px; }
        .nav-link { display: inline-block; margin-bottom: 10px; color: #28a745; text-decoration: none; font-weight: bold; font-size: 13px; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #e9ecef; padding-bottom: 8px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 18px; font-weight: bold; }
        .user-info { font-size: 12px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 6px; font-weight: bold; }
        .pix-card { background: #ffffff; width: 100%; max-width: 550px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: none; text-align: center; }
    </style>
</head>
<body>
   <div class="main-container">
        
       <div class="cart-card">
            <h3>🛒 Itens da Compra Atual</h3>
            <div class="items-table-container">
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Produto</th>
                            <th>Qtd</th>
                            <th>Total</th>
                            <th style="text-align: center;">Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in carrinho_atual %}
                        <tr>
                            <td>{{ item.nome }}</td>
                            <td>{{ item.quantidade }}x</td>
                            <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(item.total) }}</td>
                            <td style="text-align: center;">
                                <form method="POST" style="margin: 0; display: inline;">
                                    <input type="hidden" name="acao" value="remover">
                                    <input type="hidden" name="indice" value="{{ loop.index0 }}">
                                    <button type="submit" title="Remover item" style="background: none; border: none; color: #dc3545; cursor: pointer; font-size: 14px; padding: 2px 6px; font-weight: bold;">❌</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" style="text-align: center; color: #888;">Nenhum item na compra atual.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 12px; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 10px; border-radius: 6px; text-align: center;">
                <span style="font-size: 12px; color: #2e7d32; font-weight: bold;">TOTAL DA COMPRA:</span><br>
                <span style="font-size: 18px; color: #2e7d32; font-weight: bold;">R$ {{ "%.2f"|format(total_compra_atual) }}</span>
            </div>

            {% if carrinho_atual %}
            <form method="POST">
                <input type="hidden" name="acao" value="cancelar">
                <button type="submit" class="btn-danger">❌ Cancelar Compra</button>
            </form>
            {% endif %}

            <div style="margin-top: 15px; font-size: 12px; color: #666; text-align: center;">
                Operador: <strong>{{ usuario }}</strong>
            </div>
       </div>

       <div class="card" id="cardPrincipal">
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="display: inline-block; width: 32px; height: 32px; background-color: #bc002d; border-radius: 50%; line-height: 32px; color: white; font-weight: bold; font-size: 15px; margin-bottom: 2px;">山</div>
                <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
            </div>
            <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 12px;">

            <div class="brand-header">
                <h2>🏪 Frente de Caixa</h2>
                <div class="user-info">
                    Operador: <strong>{{ usuario }}</strong> <a href="/logout">[Sair]</a>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
                <a class="nav-link" href="/fechamento" style="color: #bc002d; margin-left: 10px;">📊 Fechamento</a>
            </div>

            <form id="formVenda" method="POST">
                <input type="hidden" name="acao" value="adicionar">
                
                <label for="identificador">ID ou Código de Barras:</label>
                <input type="text" id="identificador" name="identificador" placeholder="Digite ou bipe o código" required autofocus onblur="buscarProduto()" onkeydown="tratarTeclaIdentificador(event)">
                
                <div class="info-box">
                    <div class="info-row">
                        <span>Produto:</span>
                        <strong id="nome_produto">Aguardando busca...</strong>
                    </div>
                    <div class="info-row">
                        <span>Valor Unitário:</span>
                        <strong id="valor_unitario">R$ 0,00</strong>
                    </div>
                </div>

                <label for="quantidade">Quantidade:</label>
                <input type="number" id="quantidade" name="quantidade" value="1" min="1" required oninput="calcularTotal()" onkeydown="tratarTeclaQuantidade(event)">

                <div class="info-box total-box">
                    <div class="info-row">
                        <span>TOTAL DO ITEM:</span>
                        <strong id="valor_total">R$ 0,00</strong>
                    </div>
                </div>

                <button type="submit" id="btnAdicionar">Adicionar Item (ENTER)</button>
            </form>

            {% if carrinho_atual %}
            <form method="POST" style="margin-top: 15px; border-top: 2px dashed #007bff; padding-top: 15px;">
                <input type="hidden" name="acao" value="finalizar">
                
                <label for="forma_pagamento">Forma de Pagamento:</label>
                <select name="forma_pagamento" id="forma_pagamento" onchange="tratarFormaPagamento()">
                    <option value="Dinheiro">Dinheiro</option>
                    <option value="Cartao">Cartão</option>
                    <option value="Pix">Pix</option>
                </select>

                <button type="submit" class="btn-success">✅ Finalizar Venda / Fechar Compra</button>
                <div id="data-extenso" style="font-size: 13px; color: #555; text-align: center; margin-top: 10px;"></div>
            </form>
            {% endif %}
       </div>

       <div class="pix-card" id="cardPix">
            <h2 style="color: #007bff; margin-top: 0;">📱 Pagamento via Pix</h2>
            <p>Escaneie o QR Code abaixo com o aplicativo do seu banco:</p>
            
            <div style="margin: 15px 0;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=00020126400014br.gov.bcb.pix0118py9dm.mt@gmail.com5204000053039865802BR5915BERSEJULIOCESAR6009Sao Paulo610901227-20062230519daqr2112582259416686304F335" alt="QR Code Pix" style="width: 200px; height: 200px; border-radius: 8px; border: 1px solid #ddd; padding: 5px; background: #fff;">
            </div>
            
            <p style="font-size: 13px; color: #555;">Chave Pix: <strong>py9dm.mt@gmail.com</strong></p>
            <p style="font-size: 16px; color: #28a745; font-weight: bold;">Valor: R$ {{ "%.2f"|format(total_compra_atual) }}</p>
            
            <form method="POST">
                <input type="hidden" name="acao" value="finalizar">
                <input type="hidden" name="forma_pagamento" value="Pix">
                <button type="submit" class="btn-success" style="margin-top: 10px;">✅ Confirmar Recebimento Pix e Concluir</button>
            </form>

            <button type="button" onclick="voltarDoPix()" style="background-color: #6c757d; margin-top: 8px;">← Voltar / Alterar Pagamento</button>
       </div>

   </div>

   {% if msg %}
        <div style="position: fixed; bottom: 10px; right: 10px; z-index: 999; background: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; font-weight: bold;">
            {{ msg }}
        </div>
   {% endif %}

   <script>
        let precoUnitarioAtual = 0;

        async function buscarProduto() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    precoUnitarioAtual = parseFloat(data.preco);
                    document.getElementById('valor_unitario').innerText = 'R$ ' + precoUnitarioAtual.toFixed(2).replace('.', ',');
                    calcularTotal();
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    resetarCampos();
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificador(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProduto();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function tratarTeclaQuantidade(e) { if (e.key === 'Enter') { calcularTotal(); } }
        function calcularTotal() {
            const qtd = parseInt(document.getElementById('quantidade').value) || 0;
            const total = precoUnitarioAtual * qtd;
            document.getElementById('valor_total').innerText = 'R$ ' + total.toFixed(2).replace('.', ',');
        }
        function resetarCampos() {
            document.getElementById('valor_unitario').innerText = 'R$ 0,00';
            document.getElementById('valor_total').innerText = 'R$ 0,00';
            precoUnitarioAtual = 0;
        }

        function tratarFormaPagamento() {
            const forma = document.getElementById('forma_pagamento').value;
            if (forma === 'Pix') {
                document.getElementById('cardPrincipal').style.display = 'none';
                document.getElementById('cardPix').style.display = 'block';
            }
        }

        function voltarDoPix() {
            document.getElementById('forma_pagamento').value = 'Dinheiro';
            document.getElementById('cardPix').style.display = 'none';
            document.getElementById('cardPrincipal').style.display = 'block';
        }
   </script>
   <script>
    window.addEventListener('DOMContentLoaded', (event) => {
        function atualizarDataEHora() {
            const hoje = new Date();
            const opcoesData = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            let dataFormatada = hoje.toLocaleDateString('pt-BR', opcoesData);
            dataFormatada = dataFormatada.charAt(0).toUpperCase() + dataFormatada.slice(1);
            const horaFormatada = hoje.toLocaleTimeString('pt-BR');
            const elementoData = document.getElementById('data-extenso');
            if (elementoData) {
                elementoData.innerHTML = `📅 <strong>${dataFormatada}</strong> — ⏰ <strong>${horaFormatada}</strong>`;
            }
        }
        atualizarDataEHora();
        setInterval(atualizarDataEHora, 1000);
    });
</script>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
   <meta charset="UTF-8">
   <title>Entrada de Estoque - Grupo Yamasaki</title>
   <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .card { background: #ffffff; width: 100%; max-width: 600px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: auto; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #fff; }
        input:focus { border-color: #28a745; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #218838; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 20px; font-weight: bold; }
   </style>
</head>
<body>
 <div class="card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 36px; height: 36px; background-color: #bc002d; border-radius: 50%; line-height: 36px; color: white; font-weight: bold; font-size: 16px; margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="brand-header">
            <h2>📦 Gerenciamento de Estoque</h2>
            <div style="font-size: 13px; color: #555;">
                Operador: <strong>{{ usuario }}</strong> <a href="/logout" style="color: #dc3545; text-decoration: none; font-weight: bold;">[Sair]</a>
            </div>
        </div>
        <a class="nav-link" href="/">← Voltar para o Caixa</a>

        <form method="POST">
            <label for="identificador">Código de Barras ou ID:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProdutoEstoque()" onkeydown="tratarTeclaIdentificadorEstoque(event)">
            
            <div class="info-box">
                <div class="info-row">
                    <span>Produto:</span>
                    <strong id="nome_produto">Aguardando busca...</strong>
                </div>
                <div class="info-row">
                    <span>Estoque Atual:</span>
                    <strong id="estoque_atual">-</strong>
                </div>
            </div>

            <label for="quantidade">Quantidade a Adicionar / Retirar (ex: 10 ou -10):</label>
            <input type="number" id="quantidade" name="quantidade" value="1" required>

            <button type="submit">Atualizar Estoque</button>
        </form>

        {% if msg %}
            <div style="margin-top: 20px; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; background: #e8f5e9; color: #2e7d32;">{{ msg }}</div>
        {% endif %}
   </div>

   <script>
        async function buscarProdutoEstoque() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    document.getElementById('estoque_atual').innerText = data.estoque;
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    document.getElementById('estoque_atual').innerText = '-';
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificadorEstoque(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProdutoEstoque();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function resetarCampos() {
            document.getElementById('nome_produto').innerText = 'Aguardando busca...';
            document.getElementById('estoque_atual').innerText = '-';
        }
   </script>
</body>
</html>
"""

HTML_FECHAMENTO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Fechamento de Caixa - Grupo Yamasaki</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; padding: 30px; display: flex; justify-content: center; }
        .card { background: #ffffff; width: 100%; max-width: 950px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: auto; }
        .header-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #bc002d; padding-bottom: 12px; margin-bottom: 20px; }
        h1 { color: #bc002d; margin: 0; font-size: 22px; }
        .nav-link { color: #007bff; text-decoration: none; font-weight: bold; font-size: 14px; }
        .nav-link:hover { text-decoration: underline; }
        
        /* Dashboard Cards */
        .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }
        .dash-card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .dash-card h4 { margin: 0; font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
        .dash-card .value { font-size: 20px; font-weight: bold; color: #333; margin-top: 8px; }
        .dash-card.highlight .value { color: #28a745; }

        /* Filter Form */
        .filter-form { background: #fdfdfd; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 15px; align-items: flex-end; flex-wrap: wrap; }
        .filter-group { flex: 1; min-width: 200px; }
        .filter-group label { display: block; font-size: 13px; font-weight: 600; color: #444; margin-bottom: 5px; }
        .filter-group input, .filter-group select { width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; box-sizing: border-box; background: #fff; }
        .btn-filter { background-color: #007bff; color: white; border: none; padding: 9px 20px; font-size: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; height: 38px; }
        .btn-filter:hover { background-color: #0056b3; }

        /* Table */
        .table-container { overflow-x: auto; border: 1px solid #eee; border-radius: 8px; max-height: 400px; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th, td { padding: 12px 15px; border-bottom: 1px solid #eee; }
        th { background-color: #f8f9fa; color: #444; position: sticky; top: 0; font-weight: 600; }
        tr:hover { background-color: #fcfcfc; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; background: #e2e3e5; color: #383d41; }
        .badge-dinheiro { background: #d4edda; color: #155724; }
        .badge-cartao { background: #cce5ff; color: #004085; }
        .badge-pix { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align: center; margin-bottom: 10px;">
            <div style="display: inline-block; width: 32px; height: 32px; background-color: #bc002d; border-radius: 50%; line-height: 32px; color: white; font-weight: bold; font-size: 15px; margin-bottom: 2px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 15px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="header-top">
            <h1>📊 Painel de Fechamento de Caixa</h1>
            <a class="nav-link" href="/">← Voltar para Frente de Caixa</a>
        </div>

        <!-- Filtro por Data e Operador -->
        <form method="GET" class="filter-form">
            <div class="filter-group">
                <label for="data_filtro">Filtrar por Data:</label>
                <input type="date" id="data_filtro" name="data" value="{{ data_selecionada }}">
            </div>

            <div class="filter-group">
                <label for="operador_filtro">Operador:</label>
                <select id="operador_filtro" name="operador">
                    <option value="todos">🌐 Todos os Operadores</option>
                    {% for op in lista_operadores %}
                        <option value="{{ op }}" {% if operador_selecionado == op %}selected{% endif %}>{{ op }}</option>
                    {% endfor %}
                </select>
            </div>

            <button type="submit" class="btn-filter">🔍 Pesquisar</button>
            <a href="/fechamento" style="padding: 9px 15px; background: #6c757d; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold; height: 38px; display: flex; align-items: center; box-sizing: border-box;">Hoje</a>
        </form>

        <p style="font-size: 14px; color: #555; margin-top: 0; margin-bottom: 15px;">
            Exibindo dados para: <strong>{% if operador_selecionado == 'todos' %}Todos os Operadores{% else %}{{ operador_selecionado }}{% endif %}</strong> | Período: <strong>{{ data_extenso }}</strong>
        </p>

        <!-- Dashboard Cards -->
        <div class="dashboard-grid">
            <div class="dash-card highlight">
                <h4>Total Vendido</h4>
                <div class="value">R$ {{ "%.2f"|format(total_geral) }}</div>
            </div>
            <div class="dash-card">
                <h4>Total de Itens Vendidos</h4>
                <div class="value">{{ total_quantidade }}</div>
            </div>
            <div class="dash-card">
                <h4>Ticket Médio por Venda</h4>
                <div class="value">R$ {{ "%.2f"|format(ticket_medio) }}</div>
            </div>
        </div>

        <!-- Tabela Detalhada -->
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Data e Hora</th>
                        <th>Operador</th>
                        <th>Produto</th>
                        <th>Qtd</th>
                        <th>Pagamento</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for venda in vendas %}
                    <tr>
                        <td>{{ venda.data_venda_str }}</td>
                        <td>{{ venda.operador }}</td>
                        <td><strong>{{ venda.produto }}</strong></td>
                        <td>{{ venda.quantidade }}x</td>
                        <td>
                            {% if venda.forma_pagamento == 'Dinheiro' %}
                                <span class="badge badge-dinheiro">Dinheiro</span>
                            {% elif venda.forma_pagamento == 'Cartao' %}
                                <span class="badge badge-cartao">Cartão</span>
                            {% else %}
                                <span class="badge badge-pix">Pix</span>
                            {% endif %}
                        </td>
                        <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(venda.total) }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" style="text-align: center; color: #777; padding: 25px;">Nenhum registro de venda encontrado para os filtros selecionados.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# ==========================================
# 2. ROTAS DO FLASK
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = conectar_banco()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {TABELA_USUARIO} WHERE login = %s AND senha = %s", (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                session['usuario'] = username
                return redirect(url_for('caixa'))
            else:
                msg = "Usuário ou senha incorretos."
        except Exception as e:
            msg = f"Erro no banco: {e}"
    return render_template_string(HTML_LOGIN, msg=msg)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    msg = None

    if 'carrinho_atual' not in session:
        session['carrinho_atual'] = []

    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'adicionar':
            identificador = request.form.get('identificador', '').strip()
            quantidade = int(request.form.get('quantidade', 1))
            try:
                conn = conectar_banco()
                cur = conn.cursor()
                
                if identificador.isdigit():
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s OR codigo_barra = %s", (int(identificador), identificador))
                else:
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barra = %s", (identificador,))
                
                produto = cur.fetchone()
                cur.close()
                conn.close()

                if produto:
                    prod_id, nome, preco, estoque = produto
                    total_item = float(preco) * quantidade
                    session['carrinho_atual'].append({
                        'id': prod_id,
                        'nome': nome,
                        'preco': float(preco),
                        'quantidade': quantidade,
                        'total': total_item
                    })
                    session.modified = True
                else:
                    msg = "Produto não encontrado."
            except Exception as e:
                msg = f"Erro ao adicionar: {e}"

        elif acao == 'remover':
            indice = int(request.form.get('indice'))
            if 0 <= indice < len(session['carrinho_atual']):
                session['carrinho_atual'].pop(indice)
                session.modified = True

        elif acao == 'cancelar':
            session['carrinho_atual'] = []
            session.modified = True
    import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_berse"

TABELA_PRODUTO = "produto"
TABELA_USUARIO = "usuario"
TABELA_VENDAS = "vendas"

def conectar_banco():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("A variável de ambiente DATABASE_URL não está configurada!")
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    return psycopg2.connect(db_url, sslmode='require')

# ==========================================
# 1. TEMPLATES HTML
# ==========================================

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
   <meta charset="UTF-8">
   <title>Login - Grupo Yamasaki PDV</title>
   <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .login-card { background: #ffffff; width: 100%; max-width: 400px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #007bff; text-align: center; margin-top: 0; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .msg { margin-top: 15px; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; background: #ffebee; color: #c62828; }
   </style>
</head>
<body>
   <div class="login-card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 36px; height: 36px; background-color: #bc002d; border-radius: 50%; line-height: 36px; color: white; font-weight: bold; font-size: 16px; margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <p style="text-align: center; color: #666; font-size: 14px;">Faça login para acessar o PDV</p>
        
        <form method="POST">
            <label for="username">Usuário:</label>
            <input type="text" id="username" name="username" required autofocus>
            
            <label for="password">Senha:</label>
            <input type="password" id="password" name="password" required>
            
            <button type="submit">Entrar</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
   </div>
</body>
</html>
"""

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Berse Supermercados - PDV</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            min-height: 100vh;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            box-sizing: border-box;
        }
        .main-container { display: flex; gap: 20px; align-items: flex-start; max-width: 1050px; width: 100%; justify-content: center; }
        .cart-card { background: #ffffff; width: 100%; max-width: 400px; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
        .cart-card h3 { color: #007bff; margin-top: 0; font-size: 16px; border-bottom: 2px solid #007bff; padding-bottom: 8px; }
        .items-table-container { overflow-y: auto; max-height: 350px; margin-top: 10px; border: 1px solid #eee; border-radius: 6px; }
        .items-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .items-table th, .items-table td { padding: 8px; text-align: left; border-bottom: 1px solid #f0f2f5; }
        .items-table th { background: #f8f9fa; color: #666; position: sticky; top: 0; }
        .card { background: #ffffff; width: 100%; max-width: 550px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        label { display: block; margin-top: 12px; font-weight: 600; color: #444; font-size: 14px; }
        input, select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 14px; background-color: #fff; }
        input:focus, select:focus { border-color: #007bff; outline: none; }
        button { margin-top: 15px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #0056b3; }
        .btn-success { background-color: #28a745; }
        .btn-success:hover { background-color: #218838; }
        .btn-danger { background-color: #dc3545; font-size: 13px; padding: 8px; margin-top: 8px; }
        .btn-danger:hover { background-color: #c82333; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 12px; margin-top: 12px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 15px; }
        .info-row strong { color: #333; }
        .total-box { font-size: 18px; color: #28a745; border-top: 2px solid #28a745; padding-top: 8px; margin-top: 8px; }
        .nav-link { display: inline-block; margin-bottom: 10px; color: #28a745; text-decoration: none; font-weight: bold; font-size: 13px; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #e9ecef; padding-bottom: 8px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 18px; font-weight: bold; }
        .user-info { font-size: 12px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 6px; font-weight: bold; }
        .pix-card { background: #ffffff; width: 100%; max-width: 550px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: none; text-align: center; }
    </style>
</head>
<body>
   <div class="main-container">
        
       <div class="cart-card">
            <h3>🛒 Itens da Compra Atual</h3>
            <div class="items-table-container">
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Produto</th>
                            <th>Qtd</th>
                            <th>Total</th>
                            <th style="text-align: center;">Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in carrinho_atual %}
                        <tr>
                            <td>{{ item.nome }}</td>
                            <td>{{ item.quantidade }}x</td>
                            <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(item.total) }}</td>
                            <td style="text-align: center;">
                                <form method="POST" style="margin: 0; display: inline;">
                                    <input type="hidden" name="acao" value="remover">
                                    <input type="hidden" name="indice" value="{{ loop.index0 }}">
                                    <button type="submit" title="Remover item" style="background: none; border: none; color: #dc3545; cursor: pointer; font-size: 14px; padding: 2px 6px; font-weight: bold;">❌</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" style="text-align: center; color: #888;">Nenhum item na compra atual.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 12px; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 10px; border-radius: 6px; text-align: center;">
                <span style="font-size: 12px; color: #2e7d32; font-weight: bold;">TOTAL DA COMPRA:</span><br>
                <span style="font-size: 18px; color: #2e7d32; font-weight: bold;">R$ {{ "%.2f"|format(total_compra_atual) }}</span>
            </div>

            {% if carrinho_atual %}
            <form method="POST">
                <input type="hidden" name="acao" value="cancelar">
                <button type="submit" class="btn-danger">❌ Cancelar Compra</button>
            </form>
            {% endif %}

            <div style="margin-top: 15px; font-size: 12px; color: #666; text-align: center;">
                Operador: <strong>{{ usuario }}</strong>
            </div>
       </div>

       <div class="card" id="cardPrincipal">
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="display: inline-block; width: 32px; height: 32px; background-color: #bc002d; border-radius: 50%; line-height: 32px; color: white; font-weight: bold; font-size: 15px; margin-bottom: 2px;">山</div>
                <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
            </div>
            <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 12px;">

            <div class="brand-header">
                <h2>🏪 Frente de Caixa</h2>
                <div class="user-info">
                    Operador: <strong>{{ usuario }}</strong> <a href="/logout">[Sair]</a>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
                <a class="nav-link" href="/fechamento" style="color: #bc002d; margin-left: 10px;">📊 Fechamento</a>
            </div>

            <form id="formVenda" method="POST">
                <input type="hidden" name="acao" value="adicionar">
                
                <label for="identificador">ID ou Código de Barras:</label>
                <input type="text" id="identificador" name="identificador" placeholder="Digite ou bipe o código" required autofocus onblur="buscarProduto()" onkeydown="tratarTeclaIdentificador(event)">
                
                <div class="info-box">
                    <div class="info-row">
                        <span>Produto:</span>
                        <strong id="nome_produto">Aguardando busca...</strong>
                    </div>
                    <div class="info-row">
                        <span>Valor Unitário:</span>
                        <strong id="valor_unitario">R$ 0,00</strong>
                    </div>
                </div>

                <label for="quantidade">Quantidade:</label>
                <input type="number" id="quantidade" name="quantidade" value="1" min="1" required oninput="calcularTotal()" onkeydown="tratarTeclaQuantidade(event)">

                <div class="info-box total-box">
                    <div class="info-row">
                        <span>TOTAL DO ITEM:</span>
                        <strong id="valor_total">R$ 0,00</strong>
                    </div>
                </div>

                <button type="submit" id="btnAdicionar">Adicionar Item (ENTER)</button>
            </form>

            {% if carrinho_atual %}
            <form method="POST" style="margin-top: 15px; border-top: 2px dashed #007bff; padding-top: 15px;">
                <input type="hidden" name="acao" value="finalizar">
                
                <label for="forma_pagamento">Forma de Pagamento:</label>
                <select name="forma_pagamento" id="forma_pagamento" onchange="tratarFormaPagamento()">
                    <option value="Dinheiro">Dinheiro</option>
                    <option value="Cartao">Cartão</option>
                    <option value="Pix">Pix</option>
                </select>

                <button type="submit" class="btn-success">✅ Finalizar Venda / Fechar Compra</button>
                <div id="data-extenso" style="font-size: 13px; color: #555; text-align: center; margin-top: 10px;"></div>
            </form>
            {% endif %}
       </div>

       <div class="pix-card" id="cardPix">
            <h2 style="color: #007bff; margin-top: 0;">📱 Pagamento via Pix</h2>
            <p>Escaneie o QR Code abaixo com o aplicativo do seu banco:</p>
            
            <div style="margin: 15px 0;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=00020126400014br.gov.bcb.pix0118py9dm.mt@gmail.com5204000053039865802BR5915BERSEJULIOCESAR6009Sao Paulo610901227-20062230519daqr2112582259416686304F335" alt="QR Code Pix" style="width: 200px; height: 200px; border-radius: 8px; border: 1px solid #ddd; padding: 5px; background: #fff;">
            </div>
            
            <p style="font-size: 13px; color: #555;">Chave Pix: <strong>py9dm.mt@gmail.com</strong></p>
            <p style="font-size: 16px; color: #28a745; font-weight: bold;">Valor: R$ {{ "%.2f"|format(total_compra_atual) }}</p>
            
            <form method="POST">
                <input type="hidden" name="acao" value="finalizar">
                <input type="hidden" name="forma_pagamento" value="Pix">
                <button type="submit" class="btn-success" style="margin-top: 10px;">✅ Confirmar Recebimento Pix e Concluir</button>
            </form>

            <button type="button" onclick="voltarDoPix()" style="background-color: #6c757d; margin-top: 8px;">← Voltar / Alterar Pagamento</button>
       </div>

   </div>

   {% if msg %}
        <div style="position: fixed; bottom: 10px; right: 10px; z-index: 999; background: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; font-weight: bold;">
            {{ msg }}
        </div>
   {% endif %}

   <script>
        let precoUnitarioAtual = 0;

        async function buscarProduto() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    precoUnitarioAtual = parseFloat(data.preco);
                    document.getElementById('valor_unitario').innerText = 'R$ ' + precoUnitarioAtual.toFixed(2).replace('.', ',');
                    calcularTotal();
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    resetarCampos();
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificador(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProduto();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function tratarTeclaQuantidade(e) { if (e.key === 'Enter') { calcularTotal(); } }
        function calcularTotal() {
            const qtd = parseInt(document.getElementById('quantidade').value) || 0;
            const total = precoUnitarioAtual * qtd;
            document.getElementById('valor_total').innerText = 'R$ ' + total.toFixed(2).replace('.', ',');
        }
        function resetarCampos() {
            document.getElementById('valor_unitario').innerText = 'R$ 0,00';
            document.getElementById('valor_total').innerText = 'R$ 0,00';
            precoUnitarioAtual = 0;
        }

        function tratarFormaPagamento() {
            const forma = document.getElementById('forma_pagamento').value;
            if (forma === 'Pix') {
                document.getElementById('cardPrincipal').style.display = 'none';
                document.getElementById('cardPix').style.display = 'block';
            }
        }

        function voltarDoPix() {
            document.getElementById('forma_pagamento').value = 'Dinheiro';
            document.getElementById('cardPix').style.display = 'none';
            document.getElementById('cardPrincipal').style.display = 'block';
        }
   </script>
   <script>
    window.addEventListener('DOMContentLoaded', (event) => {
        function atualizarDataEHora() {
            const hoje = new Date();
            const opcoesData = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            let dataFormatada = hoje.toLocaleDateString('pt-BR', opcoesData);
            dataFormatada = dataFormatada.charAt(0).toUpperCase() + dataFormatada.slice(1);
            const horaFormatada = hoje.toLocaleTimeString('pt-BR');
            const elementoData = document.getElementById('data-extenso');
            if (elementoData) {
                elementoData.innerHTML = `📅 <strong>${dataFormatada}</strong> — ⏰ <strong>${horaFormatada}</strong>`;
            }
        }
        atualizarDataEHora();
        setInterval(atualizarDataEHora, 1000);
    });
</script>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
   <meta charset="UTF-8">
   <title>Entrada de Estoque - Grupo Yamasaki</title>
   <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .card { background: #ffffff; width: 100%; max-width: 600px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: auto; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #fff; }
        input:focus { border-color: #28a745; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #218838; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 20px; font-weight: bold; }
   </style>
</head>
<body>
 <div class="card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 36px; height: 36px; background-color: #bc002d; border-radius: 50%; line-height: 36px; color: white; font-weight: bold; font-size: 16px; margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="brand-header">
            <h2>📦 Gerenciamento de Estoque</h2>
            <div style="font-size: 13px; color: #555;">
                Operador: <strong>{{ usuario }}</strong> <a href="/logout" style="color: #dc3545; text-decoration: none; font-weight: bold;">[Sair]</a>
            </div>
        </div>
        <a class="nav-link" href="/">← Voltar para o Caixa</a>

        <form method="POST">
            <label for="identificador">Código de Barras ou ID:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProdutoEstoque()" onkeydown="tratarTeclaIdentificadorEstoque(event)">
            
            <div class="info-box">
                <div class="info-row">
                    <span>Produto:</span>
                    <strong id="nome_produto">Aguardando busca...</strong>
                </div>
                <div class="info-row">
                    <span>Estoque Atual:</span>
                    <strong id="estoque_atual">-</strong>
                </div>
            </div>

            <label for="quantidade">Quantidade a Adicionar / Retirar (ex: 10 ou -10):</label>
            <input type="number" id="quantidade" name="quantidade" value="1" required>

            <button type="submit">Atualizar Estoque</button>
        </form>

        {% if msg %}
            <div style="margin-top: 20px; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; background: #e8f5e9; color: #2e7d32;">{{ msg }}</div>
        {% endif %}
   </div>

   <script>
        async function buscarProdutoEstoque() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    document.getElementById('estoque_atual').innerText = data.estoque;
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    document.getElementById('estoque_atual').innerText = '-';
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificadorEstoque(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProdutoEstoque();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function resetarCampos() {
            document.getElementById('nome_produto').innerText = 'Aguardando busca...';
            document.getElementById('estoque_atual').innerText = '-';
        }
   </script>
</body>
</html>
"""

HTML_FECHAMENTO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Fechamento de Caixa - Grupo Yamasaki</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; padding: 30px; display: flex; justify-content: center; }
        .card { background: #ffffff; width: 100%; max-width: 950px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: auto; }
        .header-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #bc002d; padding-bottom: 12px; margin-bottom: 20px; }
        h1 { color: #bc002d; margin: 0; font-size: 22px; }
        .nav-link { color: #007bff; text-decoration: none; font-weight: bold; font-size: 14px; }
        .nav-link:hover { text-decoration: underline; }
        
        /* Dashboard Cards */
        .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }
        .dash-card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .dash-card h4 { margin: 0; font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
        .dash-card .value { font-size: 20px; font-weight: bold; color: #333; margin-top: 8px; }
        .dash-card.highlight .value { color: #28a745; }

        /* Filter Form */
        .filter-form { background: #fdfdfd; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 15px; align-items: flex-end; flex-wrap: wrap; }
        .filter-group { flex: 1; min-width: 200px; }
        .filter-group label { display: block; font-size: 13px; font-weight: 600; color: #444; margin-bottom: 5px; }
        .filter-group input, .filter-group select { width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; box-sizing: border-box; background: #fff; }
        .btn-filter { background-color: #007bff; color: white; border: none; padding: 9px 20px; font-size: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; height: 38px; }
        .btn-filter:hover { background-color: #0056b3; }

        /* Table */
        .table-container { overflow-x: auto; border: 1px solid #eee; border-radius: 8px; max-height: 400px; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th, td { padding: 12px 15px; border-bottom: 1px solid #eee; }
        th { background-color: #f8f9fa; color: #444; position: sticky; top: 0; font-weight: 600; }
        tr:hover { background-color: #fcfcfc; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; background: #e2e3e5; color: #383d41; }
        .badge-dinheiro { background: #d4edda; color: #155724; }
        .badge-cartao { background: #cce5ff; color: #004085; }
        .badge-pix { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align: center; margin-bottom: 10px;">
            <div style="display: inline-block; width: 32px; height: 32px; background-color: #bc002d; border-radius: 50%; line-height: 32px; color: white; font-weight: bold; font-size: 15px; margin-bottom: 2px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 15px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="header-top">
            <h1>📊 Painel de Fechamento de Caixa</h1>
            <a class="nav-link" href="/">← Voltar para Frente de Caixa</a>
        </div>

        <!-- Filtro por Data e Operador -->
        <form method="GET" class="filter-form">
            <div class="filter-group">
                <label for="data_filtro">Filtrar por Data:</label>
                <input type="date" id="data_filtro" name="data" value="{{ data_selecionada }}">
            </div>

            <div class="filter-group">
                <label for="operador_filtro">Operador:</label>
                <select id="operador_filtro" name="operador">
                    <option value="todos">🌐 Todos os Operadores</option>
                    {% for op in lista_operadores %}
                        <option value="{{ op }}" {% if operador_selecionado == op %}selected{% endif %}>{{ op }}</option>
                    {% endfor %}
                </select>
            </div>

            <button type="submit" class="btn-filter">🔍 Pesquisar</button>
            <a href="/fechamento" style="padding: 9px 15px; background: #6c757d; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold; height: 38px; display: flex; align-items: center; box-sizing: border-box;">Hoje</a>
        </form>

        <p style="font-size: 14px; color: #555; margin-top: 0; margin-bottom: 15px;">
            Exibindo dados para: <strong>{% if operador_selecionado == 'todos' %}Todos os Operadores{% else %}{{ operador_selecionado }}{% endif %}</strong> | Período: <strong>{{ data_extenso }}</strong>
        </p>

        <!-- Dashboard Cards -->
        <div class="dashboard-grid">
            <div class="dash-card highlight">
                <h4>Total Vendido</h4>
                <div class="value">R$ {{ "%.2f"|format(total_geral) }}</div>
            </div>
            <div class="dash-card">
                <h4>Total de Itens Vendidos</h4>
                <div class="value">{{ total_quantidade }}</div>
            </div>
            <div class="dash-card">
                <h4>Ticket Médio por Venda</h4>
                <div class="value">R$ {{ "%.2f"|format(ticket_medio) }}</div>
            </div>
        </div>

        <!-- Tabela Detalhada -->
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Data e Hora</th>
                        <th>Operador</th>
                        <th>Produto</th>
                        <th>Qtd</th>
                        <th>Pagamento</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for venda in vendas %}
                    <tr>
                        <td>{{ venda.data_venda_str }}</td>
                        <td>{{ venda.operador }}</td>
                        <td><strong>{{ venda.produto }}</strong></td>
                        <td>{{ venda.quantidade }}x</td>
                        <td>
                            {% if venda.forma_pagamento == 'Dinheiro' %}
                                <span class="badge badge-dinheiro">Dinheiro</span>
                            {% elif venda.forma_pagamento == 'Cartao' %}
                                <span class="badge badge-cartao">Cartão</span>
                            {% else %}
                                <span class="badge badge-pix">Pix</span>
                            {% endif %}
                        </td>
                        <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(venda.total) }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" style="text-align: center; color: #777; padding: 25px;">Nenhum registro de venda encontrado para os filtros selecionados.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# ==========================================
# 2. ROTAS DO FLASK (Versão Corrigida e Limpa)
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = conectar_banco()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {TABELA_USUARIO} WHERE login = %s AND senha = %s", (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                session['usuario'] = username
                return redirect(url_for('caixa'))
            else:
                msg = "Usuário ou senha incorretos."
        except Exception as e:
            msg = f"Erro no banco: {e}"
    return render_template_string(HTML_LOGIN, msg=msg)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))
# ==========================================
# ROTA DO CAIXA COM GRAVAÇÃO GARANTIDA NA TABELA 'produtobkp'
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    msg = None

    if 'carrinho_atual' not in session:
        session['carrinho_atual'] = []

    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'adicionar':
            identificador = request.form.get('identificador', '').strip()
            quantidade = int(request.form.get('quantidade', 1))
            try:
                conn = conectar_banco()
                cur = conn.cursor()
                
                if identificador.isdigit():
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s OR codigo_barra = %s", (int(identificador), identificador))
                else:
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barra = %s", (identificador,))
                
                produto = cur.fetchone()
                cur.close()
                conn.close()

                if produto:
                    prod_id, nome, preco, estoque = produto
                    total_item = float(preco) * quantidade
                    session['carrinho_atual'].append({
                        'id': prod_id,
                        'nome': nome,
                        'preco': float(preco),
                        'quantidade': quantidade,
                        'total': total_item
                    })
                    session.modified = True
                else:
                    msg = "Produto não encontrado."
            except Exception as e:
                msg = f"Erro ao adicionar: {e}"

        elif acao == 'remover':
            indice = int(request.form.get('indice'))
            if 0 <= indice < len(session['carrinho_atual']):
                session['carrinho_atual'].pop(indice)
                session.modified = True

        elif acao == 'cancelar':
            session['carrinho_atual'] = []
            session.modified = True

        elif acao == 'finalizar':
            carrinho = session.get('carrinho_atual', [])
            if carrinho:
                forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
                
                try:
                    conn = conectar_banco()
                    cur = conn.cursor()
                    
                    for item in carrinho:
                        # 1. Registra na tabela de vendas principal
                        cur.execute(
                            f"INSERT INTO {TABELA_VENDAS} (operador, forma_pagamento, produto, quantidade, total) VALUES (%s, %s, %s, %s, %s)",
                            (usuario, forma_pagamento, item['nome'], item['quantidade'], item['total'])
                        )
                        
                        # 2. Atualiza o estoque na tabela de produtos
                        cur.execute(
                            f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s",
                            (item['quantidade'], item['id'])
                        )

                        # 3. Busca o código de barras para o backup detalhado
                        cur.execute(f"SELECT codigo_barra FROM {TABELA_PRODUTO} WHERE id = %s", (item['id'],))
                        res_prod = cur.fetchone()
                        codigo_barra = res_prod[0] if res_prod and res_prod[0] else ''

                        # 4. Gravação na tabela produtobkp
                        cur.execute(
                            """
                            INSERT INTO produtobkp 
                            (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, tipo_operacao, operador) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (item['id'], codigo_barra, item['nome'], item['preco'], item['quantidade'], 'VENDA', usuario)
                        )
                        
                    conn.commit()
                    cur.close()
                    conn.close()

                    session['carrinho_atual'] = []
                    session.modified = True
                    msg = "Venda finalizada com sucesso e registrada na tabela produtobkp!"
                except Exception as e:
                    msg = f"Erro crítico ao gravar na produtobkp ou banco: {e}"

    total_compra_atual = sum(item['total'] for item in session['carrinho_atual'])
    
    return render_template_string(
        HTML_CAIXA, 
        usuario=usuario, 
        carrinho_atual=session['carrinho_atual'], 
        total_compra_atual=total_compra_atual,
        msg=msg
    )

@app.route('/buscar_produto')
def buscar_produto():
    q = request.args.get('q', '').strip()
    try:
        conn = conectar_banco()
        cur = conn.cursor()
        
        if q.isdigit():
            cur.execute(f"SELECT nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s OR codigo_barra = %s", (int(q), q))
        else:
            cur.execute(f"SELECT nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barra = %s", (q,))
            
        produto = cur.fetchone()
        cur.close()
        conn.close()

        if produto:
            return jsonify({'sucesso': True, 'nome': produto[0], 'preco': float(produto[1]), 'estoque': produto[2]})
        else:
            return jsonify({'sucesso': False})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)})

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def estoque_entrada():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    msg = None

    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 0))
        try:
            conn = conectar_banco()
            cur = conn.cursor()
            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE id = %s OR codigo_barra = %s", (quantidade, int(identificador), identificador))
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE codigo_barra = %s", (quantidade, identificador))
            conn.commit()
            cur.close()
            conn.close()
            msg = "Estoque atualizado e sincronizado com sucesso!"
        except Exception as e:
            msg = f"Erro ao atualizar estoque: {e}"

    return render_template_string(HTML_ESTOQUE, usuario=usuario, msg=msg)

@app.route('/fechamento')
def fechamento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Parâmetros de Filtro
    data_filtro = request.args.get('data', '').strip()
    if not data_filtro:
        data_filtro = datetime.now().strftime('%Y-%m-%d')
        
    operador_filtro = request.args.get('operador', 'todos').strip()
    
    vendas = []
    total_geral = 0.0
    total_quantidade = 0
    lista_operadores = []
    
    dias_semana = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    meses = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril', 5: 'maio', 6: 'junho',
        7: 'julho', 8: 'agosto', 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }

    try:
        dt_obj = datetime.strptime(data_filtro, '%Y-%m-%d')
        dia_sem = dias_semana.get(dt_obj.strftime('%A'), '')
        mes_nome = meses.get(dt_obj.month, '')
        data_extenso = f"{dia_sem}, {dt_obj.day} de {mes_nome} de {dt_obj.year}"
    except:
        data_extenso = data_filtro

    try:
        conn = conectar_banco()
        cur = conn.cursor()
        
        # Buscar lista de todos os operadores cadastrados para preencher o select
        cur.execute(f"SELECT DISTINCT login FROM {TABELA_USUARIO} ORDER BY login")
        ops = cur.fetchall()
        lista_operadores = [op[0] for op in ops]

        # Monta a query dinamicamente baseada no filtro de operador
        if operador_filtro == 'todos':
            query = f"""
                SELECT data_venda, operador, produto, quantidade, forma_pagamento, total 
                FROM {TABELA_VENDAS} 
                WHERE DATE(data_venda) = %s 
                ORDER BY data_venda DESC
            """
            cur.execute(query, (data_filtro,))
        else:
            query = f"""
                SELECT data_venda, operador, produto, quantidade, forma_pagamento, total 
                FROM {TABELA_VENDAS} 
                WHERE operador = %s AND DATE(data_venda) = %s 
                ORDER BY data_venda DESC
            """
            cur.execute(query, (operador_filtro, data_filtro))
            
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            data_str = row[0].strftime('%d/%m/%Y %H:%M:%S') if row[0] else ''
            val = float(row[5])
            qtd = int(row[3])
            vendas.append({
                'data_venda_str': data_str,
                'operador': row[1],
                'produto': row[2],
                'quantidade': qtd,
                'forma_pagamento': row[4],
                'total': val
            })
            total_geral += val
            total_quantidade += qtd
    except Exception as e:
        print(f"Erro ao carregar fechamento do banco: {e}")

    ticket_medio = (total_geral / len(vendas)) if len(vendas) > 0 else 0.0

    return render_template_string(
        HTML_FECHAMENTO, 
        usuario=session['usuario'],
        vendas=vendas,
        total_geral=total_geral,
        total_quantidade=total_quantidade,
        ticket_medio=ticket_medio,
        data_selecionada=data_filtro,
        data_extenso=data_extenso,
        lista_operadores=lista_operadores,
        operador_selecionado=operador_filtro
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

