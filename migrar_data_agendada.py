"""
Migração única: adiciona a coluna 'data_agendada' na tabela 'schedules'.

Como rodar (uma vez só, com o servidor PARADO):
    python migrar_data_agendada.py

Coloque este arquivo na RAIZ do projeto (mesmo nível do requirements.txt)
antes de rodar, pois ele localiza o banco em backend/app/coletas.db.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "backend", "app", "coletas.db")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Banco não encontrado em: {DB_PATH}")
        print("Confira se este script está na raiz do projeto.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(schedules)")
    colunas_existentes = [linha[1] for linha in cursor.fetchall()]

    if "data_agendada" in colunas_existentes:
        print("Coluna 'data_agendada' já existe. Nada a fazer.")
        conn.close()
        return

    print("Adicionando coluna 'data_agendada' na tabela 'schedules'...")
    cursor.execute("ALTER TABLE schedules ADD COLUMN data_agendada DATE")
    conn.commit()
    conn.close()
    print("Concluído! Reinicie o servidor normalmente.")


if __name__ == "__main__":
    main()