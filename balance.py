from web3 import Web3
from eth_account import Account
import csv
import os

# RPC
RPC_URL = "https://api.mainnet.abs.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def get_address_from_private_key(private_key: str) -> str:
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    account = Account.from_key(private_key)
    return account.address

def check_balance(private_key: str) -> tuple:
    """
    Проверяет баланс адреса
    
    :return: (адрес, баланс в ETH)
    """
    try:
        address = get_address_from_private_key(private_key)
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return address, float(balance_eth)
    except Exception as e:
        print(f"Ошибка при проверке баланса: {str(e)}")
        return None, None

def check_balances_from_csv(filename: str):
    """
    Проверяет балансы всех адресов из CSV файла
    """
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден")
        return
    
    print("\nПроверка балансов...")
    print("=" * 100)
    print(f"{'Адрес':42} | {'Тип':12} | {'Баланс ETH':15}")
    print("=" * 100)
    
    # Словари для хранения уникальных адресов и их балансов
    unique_addresses = {}
    address_types = {}
    
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            
            for row in reader:
                if len(row) >= 2:
                    # Проверяем отправителей
                    from_address, from_balance = check_balance(row[0].strip())
                    if from_address and from_balance is not None:
                        unique_addresses[from_address] = from_balance
                        address_types[from_address] = "Отправитель"
                    
                    # Проверяем получателей
                    to_address, to_balance = check_balance(row[1].strip())
                    if to_address and to_balance is not None:
                        unique_addresses[to_address] = to_balance
                        # Если адрес уже является отправителем, добавляем информацию
                        if to_address in address_types:
                            address_types[to_address] = "Отпр/Получ"
                        else:
                            address_types[to_address] = "Получатель"
        
        # Выводим уникальные адреса
        total_balance = 0
        for address, balance in unique_addresses.items():
            addr_type = address_types[address]
            print(f"{address} | {addr_type:12} | {balance:15.6f}")
            total_balance += balance
        
        print("=" * 100)
        print(f"Общий баланс всех уникальных кошельков: {total_balance:.6f} ETH")
        print(f"Всего уникальных адресов: {len(unique_addresses)}")
        
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Путь к CSV файлу
    csv_file = "wallets.csv"
    
    # Запуск проверки балансов
    check_balances_from_csv(csv_file) 