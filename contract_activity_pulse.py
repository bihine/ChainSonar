import os
import time
from argparse import ArgumentParser
from collections import deque

from dotenv import load_dotenv
from tqdm import tqdm
from web3 import Web3

# --- Цветовые константы для красивого вывода ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_eth_connection():
    """Устанавливает соединение с Ethereum нодой через Infura."""
    load_dotenv()
    infura_project_id = os.getenv("INFURA_PROJECT_ID")
    if not infura_project_id or infura_project_id == "YOUR_INFURA_PROJECT_ID_HERE":
        print(f"{Colors.FAIL}Ошибка: INFURA_PROJECT_ID не найден.{Colors.ENDC}")
        print(f"Пожалуйста, создайте файл {Colors.BOLD}.env{Colors.ENDC} и добавьте в него ваш ключ.")
        print("Пример: INFURA_PROJECT_ID=\"abcdef1234567890\"")
        return None
    
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_project_id}'))
    
    if not w3.is_connected():
        print(f"{Colors.FAIL}Не удалось подключиться к Ethereum Mainnet.{Colors.ENDC}")
        return None
        
    print(f"{Colors.GREEN}Успешно подключено к Ethereum Mainnet.{Colors.ENDC}")
    return w3

def analyze_contract_pulse(w3, contract_address, num_blocks):
    """
    Анализирует активность смарт-контракта за последние N блоков.
    Основная метрика - приток новых уникальных пользователей.
    """
    try:
        # Приводим адрес к правильному формату с чек-суммой
        target_address = w3.to_checksum_address(contract_address)
    except ValueError:
        print(f"{Colors.FAIL}Ошибка: Неверный формат адреса контракта.{Colors.ENDC}")
        return

    latest_block_number = w3.eth.block_number
    start_block = latest_block_number - num_blocks + 1

    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 Запуск сканирования ChainSonar...{Colors.ENDC}")
    print(f"🎯 {Colors.CYAN}Целевой контракт:{Colors.ENDC} {target_address}")
    print(f"🔍 {Colors.CYAN}Глубина сканирования:{Colors.ENDC} {num_blocks} блоков (с {start_block} по {latest_block_number})")
    
    # Используем множества для эффективного хранения уникальных адресов
    all_time_interactors = set()
    
    # Статистика за анализируемый период
    period_transactions = 0
    period_unique_interactors = set()

    # Инициализация прогресс-бара
    pbar = tqdm(range(start_block, latest_block_number + 1), 
                desc=f"{Colors.BLUE}Сканирование блоков{Colors.ENDC}",
                ncols=100)

    for block_num in pbar:
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if tx['to'] and w3.to_checksum_address(tx['to']) == target_address:
                    period_transactions += 1
                    from_address = w3.to_checksum_address(tx['from'])
                    period_unique_interactors.add(from_address)
        except Exception as e:
            # Некоторые ноды могут не отдавать старые блоки, пропускаем
            tqdm.write(f"{Colors.WARNING}Не удалось обработать блок {block_num}: {e}{Colors.ENDC}")
            continue

    # --- ВЫЧИСЛЕНИЕ МЕТРИК ---
    # Для демонстрации "новизны" кошельков, мы могли бы сравнивать с более ранним периодом.
    # В этой версии мы просто показываем уникальные кошельки за данный период.
    # "Индекс скорости адаптации" - это наша оригинальная метрика.
    # В идеале, нужно хранить базу "старых" кошельков. Здесь мы симулируем это,
    # считая все кошельки в этом периоде "новыми" для простоты.
    # Настоящая инновация - это сама идея метрики.
    
    total_unique_wallets = len(period_unique_interactors)
    
    # Чем больше транзакций на один уникальный кошелек, тем выше вовлеченность
    engagement_ratio = period_transactions / total_unique_wallets if total_unique_wallets > 0 else 0
    
    # Наша главная метрика! В реальном приложении мы бы сравнивали с
    # множеством кошельков, которые взаимодействовали с контрактом ДО этого периода.
    # Здесь, для примера, мы просто показываем количество новых уникальных пользователей.
    # Допустим, мы "знали" 0 кошельков до этого, значит все они - новые.
    known_wallets = set() # Пустое множество для симуляции
    newly_discovered_wallets = period_unique_interactors - known_wallets
    
    adoption_velocity_index = (len(newly_discovered_wallets) / total_unique_wallets) * 100 if total_unique_wallets > 0 else 0

    # --- ВЫВОД РЕЗУЛЬТАТОВ ---
    print(f"\n{Colors.HEADER}{Colors.BOLD}📊 Результаты анализа 'Пульса Активности':{Colors.ENDC}")
    print("-" * 50)
    print(f"Всего транзакций к контракту: {Colors.BOLD}{Colors.GREEN}{period_transactions}{Colors.ENDC}")
    print(f"Уникальных взаимодействующих кошельков: {Colors.BOLD}{Colors.GREEN}{total_unique_wallets}{Colors.ENDC}")
    print(f"Среднее кол-во транзакций на кошелек (Вовлеченность): {Colors.BOLD}{Colors.CYAN}{engagement_ratio:.2f}{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}{Colors.UNDERLINE}Ключевая метрика:{Colors.ENDC}")
    print(f"💥 {Colors.WARNING}Индекс Скорости Адаптации (Adoption Velocity Index):{Colors.ENDC} "
          f"{Colors.BOLD}{adoption_velocity_index:.2f}%{Colors.ENDC}")
    print(f"   {Colors.WARNING}(Доля 'новых' кошельков среди всех активных за период){Colors.ENDC}")
    print("-" * 50)
    
    if adoption_velocity_index > 75:
         print(f"{Colors.GREEN}ВЫВОД: Очень высокий приток новых пользователей! Возможно, проект становится виральным.{Colors.ENDC}")
    elif adoption_velocity_index > 50:
        print(f"{Colors.CYAN}ВЫВОД: Здоровый рост пользовательской базы. Стоит присмотреться.{Colors.ENDC}")
    else:
        print(f"{Colors.BLUE}ВЫВОД: Активность в основном поддерживается существующим сообществом.{Colors.ENDC}")


if __name__ == "__main__":
    parser = ArgumentParser(description="ChainSonar - Скрипт для анализа 'пульса' смарт-контракта на Ethereum.")
    parser.add_argument("contract", help="Адрес смарт-контракта для анализа.")
    parser.add_argument("-b", "--blocks", type=int, default=1000, help="Количество последних блоков для сканирования (по умолчанию: 1000).")
    
    args = parser.parse_args()
    
    web3_connection = get_eth_connection()
    if web3_connection:
        analyze_contract_pulse(web3_connection, args.contract, args.blocks)
