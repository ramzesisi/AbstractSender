from web3 import Web3
import time
from eth_account import Account
import json
import csv
import os
import sys
import io
from datetime import datetime

# RPC
RPC_URL = "https://api.mainnet.abs.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def get_address_from_private_key(private_key: str) -> str:
    
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    account = Account.from_key(private_key)
    return account.address

def send_eth(from_private_key: str, to_private_key: str, amount: float):
    try:
        # Получаем адрес получателя из приватного ключа
        to_address = get_address_from_private_key(to_private_key)
        
        if not w3.is_connected():
            raise Exception("Не удалось подключиться к RPC")

        # Создаем аккаунт отправителя
        if from_private_key.startswith('0x'):
            from_private_key = from_private_key[2:]
        account = Account.from_key(from_private_key)
        sender_address = account.address
        
        log_message(f"👤 Отправитель: {sender_address}")
        log_message(f"👥 Получатель: {to_address}")
        
        # Проверяем баланс отправителя
        balance = w3.eth.get_balance(sender_address)
        balance_eth = w3.from_wei(balance, 'ether')
        log_message(f"💰 Баланс отправителя: {balance_eth} ETH")
        
        # Проверяем, достаточно ли средств
        if balance_eth < amount:
            raise Exception(f"Недостаточно средств. Нужно {amount} ETH, доступно {balance_eth} ETH")
        
        try:
            nonce = w3.eth.get_transaction_count(sender_address)
            log_message("📝 Подготовка транзакции...")
            
            # Создаем транзакцию без газа
            transaction = {
                'nonce': nonce,
                'to': Web3.to_checksum_address(to_address),
                'value': w3.to_wei(amount, 'ether'),
                'chainId': 2741
            }
            
            # Оцениваем газ
            gas_estimate = w3.eth.estimate_gas({
                'from': sender_address,
                'to': Web3.to_checksum_address(to_address),
                'value': w3.to_wei(amount, 'ether')
            })
            
            # Добавляем параметры газа
            transaction.update({
                'gas': gas_estimate,
                'gasPrice': w3.eth.gas_price
            })
            
            log_message("✍️ Подписание транзакции...")
            # Подписываем и отправляем транзакцию
            signed = Account.sign_transaction(transaction, from_private_key)
            
            log_message("📤 Отправка транзакции...")
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            
            log_message("⏳ Ожидание подтверждения транзакции...")
            # Ждем подтверждения
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            log_message(f"✅ Успешно отправлено {amount} ETH")
            log_message(f"🔗 Хэш транзакции: {receipt['transactionHash'].hex()}")
            
            return True
            
        except Exception as e:
            log_message(f"❌ Ошибка при отправке: {str(e)}")
            return False
                
    except Exception as e:
        log_message(f"❌ Произошла ошибка: {str(e)}")
        return False

def log_message(message: str):
    """Функция для логирования с принудительным выводом"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    sys.stdout.flush()  # Принудительный вывод

def process_csv(filename: str, amount: float, start_from: int = 1):
    log_message("Начало обработки CSV файла")
    if not os.path.exists(filename):
        log_message(f"Файл {filename} не найден")
        return
    
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        rows = list(reader)
        
        log_message(f"Всего транзакций для обработки: {len(rows)}")
        
        for index, row in enumerate(rows, 1):
            if index < start_from:
                continue
            if len(row) >= 2:
                from_private_key = row[0].strip()
                to_private_key = row[1].strip()
                
                log_message(f"\n{'='*50}")
                log_message(f"Обработка транзакции {index}/{len(rows)}...")
                
                try:
                    success = send_eth(from_private_key, to_private_key, amount)
                    
                    if success:
                        log_message("✅ Транзакция успешно выполнена")
                    else:
                        log_message("❌ Ошибка при выполнении транзакции")
                    
                    delay = 5
                    log_message(f"⏳ Ожидание {delay} секунд перед следующей транзакцией...")
                    sys.stdout.flush()
                    time.sleep(delay)
                    
                except Exception as e:
                    log_message(f"❌ Критическая ошибка при обработке транзакции: {str(e)}")
                    continue

if __name__ == "__main__":
    # Настройка вывода
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)
    
    # Проверка подключения
    log_message("Проверка подключения к RPC...")
    if not w3.is_connected():
        log_message("❌ Не удалось подключиться к RPC")
        sys.exit(1)
    log_message("✅ Подключение к RPC успешно")
    
    csv_file = "wallets.csv"
    amount_to_send = 0.0031
    
    log_message(f"Запуск обработки CSV с суммой {amount_to_send} ETH на адрес")
    process_csv(csv_file, amount_to_send, start_from=1)
