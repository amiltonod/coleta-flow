import shutil
import os
from datetime import datetime

def criar_backup():
    origem = "backend/app/coletas.db"
    # Pasta de backup (crie essa pasta antes)
    destino_pasta = "backups"
    
    if not os.path.exists(destino_pasta):
        os.makedirs(destino_pasta)
        
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
    destino = f"{destino_pasta}/coletas_backup_{data_hora}.db"
    
    shutil.copy2(origem, destino)
    print(f"Backup criado com sucesso: {destino}")

# Você pode chamar essa função ao iniciar o sistema ou criar uma rota 
# específica para isso: /fazer-backup