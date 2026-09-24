from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import conectar_banco, TABELA_PRODUTO, TABELA_VENDAS, registrar_backup

caixa_bp = Blueprint('caixa', __name__)

@caixa_bp.route('/', methods=['GET', 'POST'])
@caixa_bp.route('/caixa', methods=['GET', 'POST'])
def index():
    usuario_logado = session.get('usuario')
    if not usuario_logado:
        return redirect(url_for('auth.login'))
    
    if 'carrinho' not in session:
        session['carrinho'] = []

    msg = None

    if request.method == 'POST':
        acao = request.form.get('acao')

        # --- AÇÃO: ADICIONAR ITEM ---
        if acao == 'adicionar':
            identificador = request.form.get('identificador', '').strip()
            quantidade = int(request.form.get('quantidade', 1))

            if identificador:
                conn = conectar_banco()
                cur = conn.cursor()
                
                # Busca flexível por ID, Código de Barras ou Nome
                if identificador.isdigit():
                    sql = f"""
                        SELECT id, nome, preco 
                        FROM {TABELA_PRODUTO} 
                        WHERE id = %s OR codigo_barras = %s OR codigo_barras LIKE %s OR LOWER(nome) LIKE LOWER(%s)
                        LIMIT 1
                    """
                    cur.execute(sql, (int(identificador), identificador, f"%{identificador}%", f"%{identificador}%"))
                else:
                    sql = f"""
                        SELECT id, nome, preco 
                        FROM {TABELA_PRODUTO} 
                        WHERE codigo_barras = %s OR LOWER(nome) LIKE LOWER(%s)
                        LIMIT 1
                    """
                    cur.execute(sql, (identificador, f"%{identificador}%"))
                
                prod = cur.fetchone()
                cur.close()
                conn.close()

                if prod:
                    prod_id, prod_nome, prod_preco = prod[0], prod[1], float(prod[2])
                    item_total = prod_preco * quantidade
                    
                    carrinho = session.get('carrinho', [])
                    carrinho.append({
                        'id': prod_id,
                        'nome': prod_nome,
                        'quantidade': quantidade,
                        'preco': prod_preco,
                        'total': item_total
                    })
                    session['carrinho'] = carrinho
                    session.modified = True
                else:
                    msg = "Produto não encontrado!"

        # --- AÇÃO: REMOVER ITEM ---
        elif acao == 'remover':
            indice = int(request.form.get('indice', -1))
            carrinho = session.get('carrinho', [])
            if 0 <= indice < len(carrinho):
                carrinho.pop(indice)
                session['carrinho'] = carrinho
                session.modified = True

        # --- AÇÃO: CANCELAR COMPRA ---
        elif acao == 'cancelar':
            session['carrinho'] = []
            session.modified = True

        # --- AÇÃO: FINALIZAR VENDA ---
        elif acao == 'finalizar':
            carrinho = session.get('carrinho', [])
            forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')

            if carrinho:
                try:
                    conn = conectar_banco()
                    cur = conn.cursor()
                    
                    for item in carrinho:
                        total_item = item['preco'] * item['quantidade']
                        
                        cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s", (item['quantidade'], item['id']))
                        
                        cur.execute(
                            f"INSERT INTO {TABELA_VENDAS} (produto_id, quantidade, valor_total, forma_pagamento, operador) VALUES (%s, %s, %s, %s, %s)",
                            (item['id'], item['quantidade'], total_item, forma_pagamento, usuario_logado)
                        )
                        
                        registrar_backup(cur, item['id'], item['nome'], item['preco'], item['quantidade'], f"VENDA_{forma_pagamento.upper()}", usuario_logado)
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    session['carrinho'] = []
                    session.modified = True
                    msg = "Venda finalizada com sucesso!"
                except Exception as e:
                    print(f"Erro ao finalizar venda: {e}")
                    msg = f"Erro ao finalizar venda: {e}"

    carrinho_atual = session.get('carrinho', [])
    total_compra_atual = sum(item['total'] for item in carrinho_atual)

    return render_template(
        'caixa.html',
        carrinho_atual=carrinho_atual,
        total_compra_atual=total_compra_atual,
        usuario=usuario_logado,
        msg=msg
    )


@caixa_bp.route('/buscar_produto')
def buscar_produto():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'sucesso': False, 'mensagem': 'Termo de busca vazio'})

    try:
        conn = conectar_banco()
        cur = conn.cursor()
        
        # Busca abrangente por ID, Código de Barras parcial ou Nome
        if query.isdigit():
            sql = f"""
                SELECT id, nome, preco 
                FROM {TABELA_PRODUTO} 
                WHERE id = %s OR codigo_barras = %s OR codigo_barras LIKE %s OR LOWER(nome) LIKE LOWER(%s)
                LIMIT 1
            """
            cur.execute(sql, (int(query), query, f"%{query}%", f"%{query}%"))
        else:
            sql = f"""
                SELECT id, nome, preco 
                FROM {TABELA_PRODUTO} 
                WHERE codigo_barras = %s OR LOWER(nome) LIKE LOWER(%s)
                LIMIT 1
            """
            cur.execute(sql, (query, f"%{query}%"))
            
        produto = cur.fetchone()
        cur.close()
        conn.close()

        if produto:
            return jsonify({
                'sucesso': True,
                'id': produto[0],
                'nome': produto[1],
                'preco': float(produto[2])
            })
        
        return jsonify({'sucesso': False, 'mensagem': 'Produto não encontrado'})

    except Exception as e:
        print(f"Erro na busca: {e}")
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 200