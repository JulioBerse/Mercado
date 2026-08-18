import psycopg2

# AJUSTE COM OS DADOS DO SEU CONTÊINER POSTGRESQL:
HOST = "localhost"
PORTA = "5432"
BANCO = "postgres"        # Nome do banco existente no contêiner
USUARIO = "postgres"      # Seu usuário do Postgres
SENHA = "j"    # Sua senha definida no contêiner

try:
    conexao = psycopg2.connect(
        host=HOST,
        port=PORTA,
        dbname=BANCO,
        user=USUARIO,
        password=SENHA
    )
    print("\n-----------------------------------------------------")
    print("Sucesso! O Python conectou no PostgreSQL do contêiner!")
    print("-----------------------------------------------------\n")
    conexao.close()

except Exception as erro:
    print("\nOps, deu erro na conexão:")
    print(erro)
