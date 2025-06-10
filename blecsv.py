import asyncio
import csv
from datetime import datetime
import os
import sys
from bleak import BleakClient, BleakScanner

# --- Configurações BLE ---
UUID_SERVICO = "12345678-1234-5678-1234-56789abcdef0"
UUID_IMU = "abcdefab-1234-5678-1234-56789abcdef0"
NOME_DISPOSITIVO = "IMU-Vaca"

# --- Configurações de Coleta ---
CSV_DIR = "dados_imu_rotulados"
WINDOW_DURATION_SECONDS = 10 # Duração de cada janela de coleta em segundos)

#  Teclas para rótulos 
LABEL_MAPPING = {
    'p': 'parada',
    'a': 'andando',
    'c': 'comendo',
    'd': 'deitada',
    'r': 'ruminando',
    'o': 'outros', 
    'q': 'sair'    
}


current_window_data = []
is_collecting = False



def notification_handler(sender, data):
    """Função chamada ao receber dados da característica via notificação."""
    global current_window_data, is_collecting
    if is_collecting:
        try:
            mensagem = data.decode("utf-8")
            timestamp = datetime.now().isoformat(timespec='milliseconds')
            current_window_data.append([timestamp] + mensagem.split(','))
            
        except Exception as e:
            print(f"Erro ao processar dado no handler: {e}") 

async def get_label_input():
    """Aguarda e retorna a entrada do teclado para o rótulo."""
    while True:
        print("\n--- ROTULAGEM ---")
        print("Digite a letra correspondente à atividade da vaca:")
        for key, label in LABEL_MAPPING.items():
            print(f"  '{key}' para '{label}'")
        print("-----------------")

        try:
            raw_input = await asyncio.to_thread(input, "Sua escolha: ")
            label_key = raw_input.strip().lower()
        except Exception as e:
            
            print(f"Erro ao ler entrada do teclado: {e}")
            return 'q' 

        if label_key in LABEL_MAPPING:
            if label_key == 'q':
                return 'q' 
            return LABEL_MAPPING[label_key]
        else:
            print(f"Entrada inválida. Por favor, digite uma das opções: {', '.join(LABEL_MAPPING.keys())}")

async def main():
    global current_window_data, is_collecting

    print("🔍 Procurando dispositivos BLE...")
    dispositivos = await BleakScanner.discover()

    target = None
    for d in dispositivos:
        if d.name and NOME_DISPOSITIVO in d.name:
            target = d
            break

    if not target:
        print(f"Dispositivo '{NOME_DISPOSITIVO}' não encontrado!")
        return

    print(f"Conectando a {target.name} ({target.address})...")

    os.makedirs(CSV_DIR, exist_ok=True)

    client = None
    try:
        async with BleakClient(target.address) as client:
            print("Conectado! Ativando notificação...")
            await client.start_notify(UUID_IMU, notification_handler)

            print(f"\nInicie a coleta de dados e prepare-se para rotular a cada {WINDOW_DURATION_SECONDS} segundos.")

            while True:
                current_window_data = []
                is_collecting = True

                print(f"\n Coletando dados por {WINDOW_DURATION_SECONDS} segundos")
                await asyncio.sleep(WINDOW_DURATION_SECONDS)

                is_collecting = False

                if not current_window_data:
                    print("Nenhum dado foi coletado neste período.")
                    await asyncio.sleep(2)
                    continue

                label = await get_label_input()

                if label == 'q':
                    print("Saindo da coleta...")
                    break

                timestamp_coleta = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = os.path.join(CSV_DIR, f"dados_imu_{label}_{timestamp_coleta}.csv")

                with open(csv_filename, mode='w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'label'])
                    for row in current_window_data:
                        writer.writerow(row + [label])
                print(f"📝 Dados de '{label}' salvos em '{csv_filename}' ({len(current_window_data)} amostras).")

                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nEncerrando o script.")
    except Exception as e:
        print(f"Erro na conexão: {e}")
    finally:
        if client and client.is_connected:
            await client.stop_notify(UUID_IMU)
            print("Notificações encerradas.")
        print("Programa finalizado.")

if __name__ == "__main__":
    asyncio.run(main())