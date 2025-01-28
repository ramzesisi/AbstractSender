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

def log_message(message: str):
    """Функция для логирования с принудительным выводом"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    sys.stdout.flush()

def get_address_from_private_key(private_key: str) -> str:
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    account = Account.from_key(private_key)
    return account.address

def collect_eth(from_private_key: str, to_address: str):
    """Собирает все ETH с адреса"""
    try:
        # Создаем аккаунт отправителя
        if from_private_key.startswith('0x'):
            from_private_key = from_private_key[2:]
        account = Account.from_key(from_private_key)
        sender_address = account.address
        
        log_message(f"👤 Проверка баланса: {sender_address}")
        
        # Проверяем баланс
        balance = w3.eth.get_balance(sender_address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        if balance_eth <= 0:
            log_message(f"⚠️ Пропуск: нулевой баланс")
            return False
            
        log_message(f"💰 Найдено: {balance_eth} ETH")
        
        try:
            nonce = w3.eth.get_transaction_count(sender_address)
            
            # Создаем транзакцию без газа
            transaction = {
                'nonce': nonce,
                'to': Web3.to_checksum_address(to_address),
                'value': w3.to_wei(balance_eth, 'ether'),  # Пока отправляем весь баланс
                'chainId': 2741
            }
            
            # Оцениваем газ
            gas_estimate = w3.eth.estimate_gas({
                'from': sender_address,
                'to': Web3.to_checksum_address(to_address),
                'value': w3.to_wei(balance_eth, 'ether')
            })
            
            # Получаем цену газа
            gas_price = w3.eth.gas_price
            
            # Вычисляем стоимость газа
            gas_cost = w3.from_wei(gas_price * gas_estimate, 'ether')
            
            # Корректируем сумму для отправки
            amount_to_send = balance_eth - gas_cost
            
            if amount_to_send <= 0:
                log_message(f"⚠️ Пропуск: недостаточно средств для оплаты газа")
                return False
                
            # Обновляем сумму в транзакции
            transaction['value'] = w3.to_wei(amount_to_send, 'ether')
            
            # Добавляем параметры газа
            transaction.update({
                'gas': gas_estimate,
                'gasPrice': gas_price
            })
            
            log_message("✍️ Подписание транзакции...")
            signed = Account.sign_transaction(transaction, from_private_key)
            
            log_message("📤 Отправка транзакции...")
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            
            log_message("⏳ Ожидание подтверждения...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            log_message(f"✅ Успешно собрано {amount_to_send} ETH")
            log_message(f"🔗 Хэш транзакции: {receipt['transactionHash'].hex()}")
            
            return True
            
        except Exception as e:
            log_message(f"❌ Ошибка при отправке: {str(e)}")
            return False
                
    except Exception as e:
        log_message(f"❌ Ошибка: {str(e)}")
        return False

def collect_from_csv(filename: str, destination_address: str):
    """Собирает ETH со всех приватных ключей из CSV"""
    log_message("🔄 Начало сбора средств")
    
    if not os.path.exists(filename):
        log_message(f"❌ Файл {filename} не найден")
        return
    
    total_collected = 0
    successful_transactions = 0
    
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            rows = list(reader)
            
            log_message(f"📋 Найдено кошельков для проверки: {len(rows) * 2}")  # *2 так как проверяем оба столбца
            
            # Создаем множество для хранения уникальных ключей
            processed_keys = set()
            
            # Обрабатываем оба столбца
            for row in rows:
                for private_key in row[:2]:  # Берем первые два столбца
                    private_key = private_key.strip()
                    
                    # Пропускаем уже обработанные ключи
                    if private_key in processed_keys:
                        continue
                    
                    processed_keys.add(private_key)
                    
                    log_message(f"\n{'='*50}")
                    success = collect_eth(private_key, destination_address)
                    
                    if success:
                        successful_transactions += 1
                    
                    time.sleep(5)  # Задержка между транзакциями
            
            log_message(f"\n{'='*50}")
            log_message(f"✨ Сбор средств завершен")
            log_message(f"📊 Успешных транзакций: {successful_transactions}")
            
    except Exception as e:
        log_message(f"❌ Ошибка при чтении файла: {str(e)}")

if __name__ == "__main__":
    # Настройка вывода
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)
    
    # Проверка подключения
    log_message("🌐 Проверка подключения к RPC...")
    if not w3.is_connected():
        log_message("❌ Не удалось подключиться к RPC")
        sys.exit(1)
    log_message("✅ Подключение успешно")
    
    # Адрес для сбора средств (замените на нужный)
    destination_address = "ВАШ АДРЕС"
    
    # Запуск сбора средств
    collect_from_csv("wallets.csv", destination_address) 