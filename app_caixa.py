import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from datetime import datetime


app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_berse"

TABELA_PRODUTO = "produto"
TABELA_USUARIO = "usuario"

def conectar_banco():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url)
    
# HTML da tela de login

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
        <h2>🏪 GRUPO YAMASAKI</h2>
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

# HTML para a tela Frente de Caixa (PDV) 

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
        .msg { margin-top: 15px; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; font-size: 13px; }
        .msg-sucesso { background: #e8f5e9; color: #2e7d32; }
        .msg-erro { background: #ffebee; color: #c62828; }
        .nav-link { display: inline-block; margin-bottom: 10px; color: #28a745; text-decoration: none; font-weight: bold; font-size: 13px; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #e9ecef; padding-bottom: 8px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 18px; font-weight: bold; }
        .user-info { font-size: 12px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 6px; font-weight: bold; }
        .footer-system { text-align: center; margin-top: 20px; font-size: 11px; color: #888; border-top: 1px solid #e9ecef; padding-top: 10px; }
        
        /* Estilo do card de Pix */
        .pix-card { background: #ffffff; width: 100%; max-width: 550px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: none; text-align: center; }
    </style>
</head>
<body>
   <div class="main-container">
        
       <!-- PAINEL LATERAL: ITENS DA COMPRA ATUAL -->
       <div class="cart-card">
           <h3>🛒 Itens da Compra Atual</h3>
           <div class="items-table-container">
               <table class="items-table">
                   <thead>
                       <tr>
                           <th>Produto</th>
                           <th>Qtd</th>
                           <th>Total</th>
                       </tr>
                   </thead>
                   <tbody>
                       {% for item in carrinho_atual %}
                       <tr>
                           <td>{{ item.nome }}</td>
                           <td>{{ item.quantidade }}x</td>
                           <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(item.total) }}</td>
                       </tr>
                       {% else %}
                       <tr>
                           <td colspan="3" style="text-align: center; color: #888;">Nenhum item na compra atual.</td>
                       </tr>
                       {% endfor %}
                   </tbody>
               </table>
           </div>

           <!-- Totalizador da Compra Atual -->
           <div style="margin-top: 12px; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 10px; border-radius: 6px; text-align: center;">
               <span style="font-size: 12px; color: #2e7d32; font-weight: bold;">TOTAL DA COMPRA:</span><br>
               <span style="font-size: 18px; color: #2e7d32; font-weight: bold;">R$ {{ "%.2f"|format(total_compra_atual) }}</span>
           </div>

           <!-- Botão para cancelar/limpar a compra atual -->
           {% if carrinho_atual %}
           <form method="POST">
               <input type="hidden" name="acao" value="cancelar">
               <button type="submit" class="btn-danger">❌ Cancelar Compra</button>
           </form>
           {% endif %}

           <div style="margin-top: 15px; font-size: 12px; color: #666; text-align: center;">
               Total Geral do Caixa Hoje: <strong>R$ {{ "%.2f"|format(total_geral_dia) }}</strong><br>
               Operador: <strong>{{ usuario }}</strong>
           </div>
       </div>

       <!-- CARD PRINCIPAL DE ENTRADA DE ITENS E FECHAMENTO -->
       <div class="card" id="cardPrincipal">
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="display: inline-block; width: 32px; height: 32px; background-color: #bc002d; border-radius: 50%; line-height: 32px; color: white; font-weight: bold; font-size: 15px; margin-bottom: 2px;">山</div>
                <h2 style="color: #1a1a1a; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
            </div>
            <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 12px;">

            <div class="brand-header">
                <h2>🏪 Frente de Caixa</h2>
                <div class="user-info">
                    <a href="/logout">[Sair]</a>
                </div>
            </div>
            <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
            <a class="nav-link" href="/fechamento" style="color: #bc002d; margin-left: 10px;">📊 Fechamento</a>

            <!-- FORMULÁRIO 1: Adicionar item ao carrinho -->
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

            <!-- FORMULÁRIO 2: Finalizar a Compra inteira -->
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
            </form>
            {% endif %}
       </div>

       <!-- CARD PIX COM O SEU QR CODE -->
       <div class="pix-card" id="cardPix">
            <h2 style="color: #007bff; margin-top: 0;">📱 Pagamento via Pix</h2>
            <p>Escaneie o QR Code abaixo com o aplicativo do seu banco:</p>
            
            <div style="margin: 15px 0;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=00020126400014br.gov.bcb.pix0118py9dm.mt@gmail.com5204000053039865802BR5915BERSEJULIOCESAR6009Sao Paulo610901227-20062230519daqr2112582259416686304F335" alt="QR Code Pix" style="width: 200px; height: 200px; border-radius: 8px; border: 1px solid #ddd; padding: 5px; background: #fff;">
            </div>
            
            <p style="font-size: 13px; color: #555;">Chave Pix: <strong>py9dm.mt@gmail.com</strong></p>
            <p style="font-size: 16px; color: #28a745; font-weight: bold;">Valor: R$ {{ "%.2f"|format(total_compra_atual) }}</p>
            
            <!-- Botão para efetivar a venda após o pagamento via Pix -->
            <form method="POST">
                <input type="hidden" name="acao" value="finalizar">
                <input type="hidden" name="forma_pagamento" value="Pix">
                <button type="submit" class="btn-success" style="margin-top: 10px;">✅ Confirmar Recebimento Pix e Concluir</button>
            </form>

            <button type="button" onclick="voltarDoPix()" style="background-color: #6c757d; margin-top: 8px;">← Voltar / Alterar Pagamento</button>
       </div>

   </div>

   {% if msg %}
       <div style="position: fixed; bottom: 10px; right: 10px; z-index: 999;" class="msg {{ 'msg-sucesso' if 'sucesso' in msg.lower() or 'adicionado' in msg.lower() else 'msg-erro' }}">
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

        // Funções para alternar a tela de Pix
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
</body>
</html>
"""

# HTML da tela Entrada de Estoque 

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
   <meta charset="UTF-8">
   <title>Entrada de Estoque - Grupo Yamasaki</title>
   <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .card { background: #ffffff; width: 100%; max-width: 600px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: auto; }
        h1 { color: #1a1a1a; margin-top: 0; font-size: 24px; border-bottom: 2px solid #28a745; padding-bottom: 10px; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #fff; }
        input:focus { border-color: #28a745; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #218838; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; }
        .info-row strong { color: #333; }
        .msg { margin-top: 20px; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; }
        .msg-sucesso { background: #e8f5e9; color: #2e7d32; }
        .msg-erro { background: #ffebee; color: #c62828; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 20px; font-weight: bold; }
        .user-info { font-size: 13px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 8px; font-weight: bold; }
        .footer-system { text-align: center; margin-top: 30px; font-size: 12px; color: #888; border-top: 1px solid #e9ecef; padding-top: 15px; }
   </style>
</head>
<body>
 <div class="card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 40px; height: 40px; background-color: #bc002d; border-radius: 50%; line-height: 40px; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 18px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
            <span style="color: #666; font-size: 10px; letter-spacing: 3px; text-transform: uppercase;">山崎グループ</span>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="brand-header">
            <h2>📦 Gerenciamento de Estoque</h2>
            <div class="user-info">
                Operador: <strong>{{ usuario }}</strong> <a href="/logout">[Sair]</a>
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
            <div class="msg {{ 'msg-sucesso' if 'sucesso' in msg.lower() else 'msg-erro' }}">{{ msg }}</div>
        {% endif %}

        <div class="footer-system">
            Powered by <strong>Yamasaki Technology Solution</strong> 🚀
        </div>
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

# HTML da tela de Fechamento de Caixa 
    
HTML_FECHAMENTO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Fechamento de Caixa - Grupo Yamasaki</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; display: flex; justify-content: center; }
        .card { background: white; padding: 30px; border-radius: 12px; max-width: 600px; width: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #1a1a1a; text-align: center; margin-top: 0; font-size: 22px; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .chart-container { width: 280px; margin: 20px auto; }
        h3 { color: #333; font-size: 16px; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #f0f2f5; font-size: 14px; }
        th { color: #666; font-weight: 600; background: #f8f9fa; }
        td { color: #333; }
        .nav-link { display: inline-block; margin-top: 25px; color: #007bff; text-decoration: none; font-weight: bold; }
        .nav-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📊 Fechamento de Caixa - {{ data_hoje }}</h2>
        <!-- 👇 COLE O CÓDIGO DO BOTÃO EXATAMENTE AQUI EMBAIXO DO H2: -->
        {% if msg %}
            <div style="background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>
        {% endif %}

        {% if fechamento_salvo %}
            <div style="background: #e3f2fd; color: #0d47a1; padding: 8px; border-radius: 6px; margin-bottom: 15px; text-align: center; font-size: 13px;">
                🔒 Caixa fechado e estocado por <strong>{{ fechamento_salvo[0] }}</strong>
            </div>
        {% else %}
            <form method="POST" style="margin-bottom: 20px;">
                <button type="submit" style="background-color: #28a745; margin-top: 0; padding: 12px; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">💾 Salvar / Estocar Fechamento do Dia</button>
            </form>
        {% endif %}
        <!-- 👆 FIM DO CÓDIGO DO BOTÃO -->
        
        <div class="chart-container">
            <canvas id="meuGrafico"></canvas>
        </div>

        <h3>👥 Vendas por Operador (Hoje)</h3>
        <table>
            <thead>
                <tr>
                    <th>Operador</th>
                    <th>Qtd. Vendas</th>
                    <th>Total Vendido</th>
                </tr>
            </thead>
            <tbody>
                {% for v in vendedores %}
                <tr>
                    <td><strong>{{ v[0] }}</strong></td>
                    <td>{{ v[2] }}x</td>
                    <td style="color: #28a745; font-weight: bold;">R$ {{ "%.2f"|format(v[1]) }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="3" style="text-align: center; color: #888;">Nenhuma venda registrada hoje.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <a class="nav-link" href="/">← Voltar ao Caixa</a>
    </div>

    <script>
        const ctx = document.getElementById('meuGrafico').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: {{ labels | tojson }},
                datasets: [{
                    data: {{ valores | tojson }},
                    backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    </script>
</body>
</html>
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = conectar_banco()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM {TABELA_USUARIO} WHERE login = %s AND senha = %s;", (username, password))
            usuario = cur.fetchone()

            if usuario:
                session['usuario'] = username
                return redirect(url_for('index'))
            else:
                mensagem = "Usuário ou senha inválidos!"
        except Exception as e:
            mensagem = f"Erro no login: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_LOGIN, msg=mensagem)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/buscar_produto')
def buscar_produto():
    if 'usuario' not in session:
        return jsonify({'sucesso': False})
    
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'sucesso': False})

    conn = conectar_banco()
    cur = conn.cursor()
    try:
        if q.isdigit():
            cur.execute(f"SELECT id, codigo_barra, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s;", (int(q),))
        else:
            cur.execute(f"SELECT id, codigo_barra, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (q,))
        
        prod = cur.fetchone()
        if prod:
            return jsonify({
                'sucesso': True,
                'id': prod[0],
                'codigo_barra': prod[1],
                'nome': prod[2],
                'preco': float(prod[3]),
                'estoque': prod[4]
            })
        return jsonify({'sucesso': False})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    operador_atual = session['usuario']
    mensagem = None

    # Inicializa o carrinho temporário na sessão se não existir
    if 'carrinho_atual' not in session:
        session['carrinho_atual'] = []

    conn = conectar_banco()
    cur = conn.cursor()

    if request.method == 'POST':
        acao = request.form.get('acao')

        # AÇÃO 1: Adicionar item ao carrinho atual
        if acao == 'adicionar':
            identificador = request.form.get('identificador', '').strip()
            quantidade = int(request.form.get('quantidade', 1))
            
            try:
                if identificador.isdigit():
                    cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
                else:
                    cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))

                produto = cur.fetchone()
                if not produto:
                    raise Exception("Produto não encontrado no cadastro!")

                prod_id = produto[0]
                codigo_barra = produto[1]
                nome_produto = produto[2]
                preco_unitario = float(produto[3])
                total_item = preco_unitario * quantidade

                # Adiciona na lista temporária da sessão
                session['carrinho_atual'].append({
                    'id': prod_id,
                    'codigo_barra': codigo_barra,
                    'nome': nome_produto,
                    'preco': preco_unitario,
                    'quantidade': quantidade,
                    'total': total_item
                })
                session.modified = True
                mensagem = f"Adicionado: {quantidade}x {nome_produto}"
            except Exception as e:
                mensagem = f"Erro ao adicionar: {e}"

        # AÇÃO 2: Finalizar a venda de todos os itens do carrinho
        elif acao == 'finalizar':
            carrinho = session.get('carrinho_atual', [])
            forma_pagto = request.form.get('forma_pagamento', 'Dinheiro')

            if not carrinho:
                mensagem = "O carrinho está vazio!"
            else:
                try:
                    for item in carrinho:
                        prod_id = item['id']
                        codigo_barra = item['codigo_barra']
                        nome_produto = item['nome']
                        preco_unitario = item['preco']
                        quantidade = item['quantidade']
                        total_venda = item['total']

                        # Dá baixa no estoque
                        cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s;", (quantidade, prod_id))

                        # Insere no Backup
                        cur.execute(
                            "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao, operador) VALUES (%s, %s, %s, %s, %s, NOW(), 'VENDA', %s);",
                            (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade, operador_atual)
                        )

                        # Insere na tabela vendas
                        cur.execute(
                            "INSERT INTO vendas (data_venda, total, forma_pagamento, produto, quantidade, operador) VALUES (NOW(), %s, %s, %s, %s, %s);",
                            (total_venda, forma_pagto, nome_produto, quantidade, operador_atual)
                        )

                    conn.commit()
                    # Zera o carrinho após finalizar com sucesso
                    session['carrinho_atual'] = []
                    session.modified = True
                    mensagem = "Venda realizada com sucesso!"
                except Exception as e:
                    conn.rollback()
                    mensagem = f"Erro ao fechar venda: {e}"

        # AÇÃO 3: Limpar/Cancelar o carrinho atual
        elif acao == 'cancelar':
            session['carrinho_atual'] = []
            session.modified = True
            mensagem = "Venda cancelada/limpa com sucesso!"

    # Calcula o total geral da compra atual que está na tela
    carrinho_atual = session.get('carrinho_atual', [])
    total_compra_atual = sum(item['total'] for item in carrinho_atual)

    # Busca o total geral vendido no dia por este operador para o rodapé/indicador
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) 
        FROM vendas 
        WHERE data_venda::date = CURRENT_DATE AND operador = %s;
    """, (operador_atual,))
    total_geral_dia = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template_string(
        HTML_CAIXA, 
        usuario=operador_atual, 
        msg=mensagem, 
        carrinho_atual=carrinho_atual,
        total_compra_atual=total_compra_atual,
        total_geral_dia=total_geral_dia
    )
    
@app.route('/fechamento', methods=['GET', 'POST'])
def fechamento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    operador_atual = session['usuario']
    conn = conectar_banco()
    cur = conn.cursor()
    
    mensagem = None
    
    # Se o usuário clicou no botão para salvar o fechamento
    if request.method == 'POST':
        try:
            # Pega o total geral do dia e os detalhes
            cur.execute("""
                SELECT SUM(total), string_agg(forma_pagamento || ': R$ ' || total, ', ') 
                FROM vendas WHERE data_venda::date = CURRENT_DATE
            """)
            res = cur.fetchone()
            total_geral = res[0] or 0
            detalhes = res[1] or "Sem vendas"
            
            # Insere ou atualiza o fechamento do dia atual na tabela nova
            cur.execute("""
                INSERT INTO fechamento_caixa (data_fechamento, total_geral, detalhes_pagamento, operador_responsavel)
                VALUES (CURRENT_DATE, %s, %s, %s)
                ON CONFLICT (data_fechamento) 
                DO UPDATE SET total_geral = EXCLUDED.total_geral, 
                              detalhes_pagamento = EXCLUDED.detalhes_pagamento, 
                              operador_responsavel = EXCLUDED.operador_responsavel;
            """, (total_geral, detalhes, operador_atual))
            
            conn.commit()
            mensagem = "Fechamento de caixa salvo com sucesso no banco de dados!"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao salvar fechamento: {e}"

    # Busca vendas por forma de pagamento (gráfico)
    cur.execute("""
        SELECT forma_pagamento, SUM(total) as soma 
        FROM vendas 
        WHERE data_venda::date = CURRENT_DATE 
        GROUP BY forma_pagamento
    """)
    dados_grafico = cur.fetchall()
    
    # Busca total de vendas por operador no dia
    cur.execute("""
        SELECT operador, SUM(total) as total_vendido, COUNT(*) as qtd_vendas
        FROM vendas 
        WHERE data_venda::date = CURRENT_DATE 
        GROUP BY operador
        ORDER BY total_vendido DESC
    """)
    dados_vendedores = cur.fetchall()
    
    # Verifica se o dia de hoje já foi estocado/salvo
    cur.execute("SELECT operador_responsavel, criado_em FROM fechamento_caixa WHERE data_fechamento = CURRENT_DATE;")
    fechamento_salvo = cur.fetchone()
    
    cur.close()
    conn.close()
    
    labels = [d[0] for d in dados_grafico]
    valores = [float(d[1]) for d in dados_grafico]
    data_atual = datetime.now().strftime('%d/%m/%Y')
    
    return render_template_string(
        HTML_FECHAMENTO, 
        labels=labels, 
        valores=valores, 
        vendedores=dados_vendedores, 
        data_hoje=data_atual, 
        msg=mensagem,
        fechamento_salvo=fechamento_salvo
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
