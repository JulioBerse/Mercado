import psycopg2
import requests
import time
from datetime import datetime

# CREDENCIAIS DO POSTGRESQL NO CONTÊINER
HOST = "localhost"
PORTA = "5432"
BANCO = "postgres"
USUARIO = "postgres"
SENHA = "j"  # COLOQUE SUA SENHA AQUI

MOEDAS = "USD-BRL,EUR-BRL,BTC-BRL"
INTERVALO_SEGUNDOS = 3600  # Roda a cada 60 segundos (1 minuto)

def executar_pipeline():
    try:
        conexao = psycopg2.connect(
            host=HOST, port=PORTA, dbname=BANCO, user=USUARIO, password=SENHA
        )
        cursor = conexao.cursor()

        # Busca dados na API
        url = f"https://economia.awesomeapi.com.br/last/{MOEDAS}"
        resposta = requests.get(url)
        dados = resposta.json()
        data_atual = datetime.now()

        query_insert = """
        INSERT INTO cotacoes_dolar (moeda, valor, data_hora)
        VALUES (%s, %s, %s);
        """

        for chave, info in dados.items():
            nome_moeda = info["name"]
            valor_compra = float(info["bid"])
            cursor.execute(query_insert, (nome_moeda, valor_compra, data_atual))

        conexao.commit()
        print(f"[{data_atual.strftime('%H:%M:%S')}] Cotações atualizadas no Postgres com sucesso!")

        cursor.close()
        conexao.close()

    except Exception as erro:
        print(f"Erro no pipeline: {erro}")

# LOOP AUTOMÁTICO EM SEGUNDO PLANO
print("=== PIPELINE AUTOMÁTICO INICIADO (Ctrl+C para parar) ===")
while True:
    executar_pipeline()
    time.sleep(INTERVALO_SEGUNDOS)
