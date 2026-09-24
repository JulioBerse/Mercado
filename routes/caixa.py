from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import conectar_banco 

caixa_bp = Blueprint('caixa', __name__)

@caixa_bp.route('/')
@caixa_bp.route('/caixa')
def index():
    if not session.get('usuario'):
        return redirect(url_for('auth.login'))
    
    total_compra = session.get('total_compra_atual', 0.0)
    carrinho = session.get('carrinho', [])
    
    return render_template('caixa.html', total_compra_atual=total_compra, carrinho=carrinho)


@caixa_bp.route('/buscar_produto')
def buscar_produto():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'sucesso': False, 'mensagem': 'Termo de busca vazio'})

    conn = conectar_banco()
    cur = conn.cursor()
    
    # 1. Se for numérico, tenta buscar por ID exato, Código de Barras exato ou similar
    if query.isdigit():
        sql = """
            SELECT id, nome, preco, estoque 
            FROM produtos 
            WHERE id = %s OR codigo_barras = %s OR codigo_barras LIKE %s
            LIMIT 1
        """
        cur.execute(sql, (int(query), query, f"%{query}%"))
    else:
        # 2. Se for texto, busca por Código de Barras ou por Nome/Descrição (case-insensitive)
        sql = """
            SELECT id, nome, preco, estoque 
            FROM produtos 
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
            'preco': float(produto[2]),
            'estoque': produto[3]
        })
    
    return jsonify({'sucesso': False, 'mensagem': 'Produto não encontrado'})