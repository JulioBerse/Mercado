from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from datetime import datetime
from database import conectar_banco, TABELA_VENDAS, TABELA_USUARIO

fechamento_bp = Blueprint('fechamento', __name__)

@fechamento_bp.route('/fechamento', methods=['GET'])
def fechamento():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    data_selecionada = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    operador_selecionado = request.args.get('operador', 'todos')

    total_vendas = 0.0
    total_transacoes = 0
    lista_operadores = []

    try:
        conn = conectar_banco()
        cur = conn.cursor()

        cur.execute(f"SELECT DISTINCT login FROM {TABELA_USUARIO}")
        lista_operadores = [row[0] for row in cur.fetchall()]

        query = f"SELECT total FROM {TABELA_VENDAS} WHERE DATE(data_venda) = %s"
        params = [data_selecionada]

        if operador_selecionado != 'todos':
            query += " AND operador = %s"
            params.append(operador_selecionado)

        cur.execute(query, tuple(params))
        vendas = cur.fetchall()

        total_vendas = sum(float(row[0]) for row in vendas)
        total_transacoes = len(vendas)

        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Erro ao carregar dados do fechamento: {e}", "danger")

    return render_template(
        'fechamento.html',
        total_vendas=total_vendas,
        total_transacoes=total_transacoes,
        data_selecionada=data_selecionada,
        operador_selecionado=operador_selecionado,
        lista_operadores=lista_operadores,
        data_extenso=data_selecionada
    )

@fechamento_bp.route('/realizar_fechamento', methods=['POST'])
def realizar_fechamento():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    data_fechamento = request.form.get('data_fechamento')
    operador = request.form.get('operador_fechamento')

    flash(f"Caixa do dia {data_fechamento} ({operador}) fechado com sucesso!", "success")
    return redirect(url_for('fechamento.fechamento', data=data_fechamento, operador=operador))