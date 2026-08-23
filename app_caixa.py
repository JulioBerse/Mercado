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
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #e9ecef; padding-bottom: 8px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 18px; font-weight: bold; }
        .user-info { font-size: 12px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 6px; font-weight: bold; }
        .footer-system { text-align: center; margin-top: 20px; font-size: 11px; color: #888; border-top: 1px solid #e9ecef; padding-top: 10px; }
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
             
             <!-- Data e Hora posicionadas estrategicamente no topo -->
             <div id="data-extenso" style="font-size: 12px; color: #555; margin-bottom: 12px;"></div>

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
