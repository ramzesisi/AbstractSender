from web3 import Web3
import time
from eth_account import Account
import json
import csv
import os
import sys
import io
from datetime import datetime

def log_message(message: str):
    """Функция для логирования с принудительным выводом"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    sys.stdout.flush()

# RPC
RPC_URL = "https://api.mainnet.abs.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Адреса контрактов
NFT_ADDRESS = Web3.to_checksum_address("0xa6c46c07f7f1966d772e29049175ebba26262513")

# Загружаем ABI
with open('abi.json', 'r') as file:
    NFT_ABI = json.load(file)

# Инициализация контракта
nft_contract = w3.eth.contract(address=NFT_ADDRESS, abi=NFT_ABI)

def get_address_from_private_key(private_key: str) -> str:
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    account = Account.from_key(private_key)
    return account.address

def transfer_nft(from_private_key: str, to_address: str):
    try:
        if from_private_key.startswith('0x'):
            from_private_key = from_private_key[2:]
        account = Account.from_key(from_private_key)
        sender_address = account.address
        
        log_message(f"👤 Проверка NFT на адресе: {sender_address}")
        
        # Проверяем баланс NFT
        balance = nft_contract.functions.balanceOf(sender_address).call()
        
        if balance <= 0:
            log_message(f"⚠️ Пропуск: нет NFT на адресе")
            return False
            
        log_message(f"💰 Найдено NFT: {balance}")
        
        try:
            # Получаем список токенов через tokensOfOwner
            token_ids = nft_contract.functions.tokensOfOwner(sender_address).call()
            
            if not token_ids:
                log_message("❌ Не удалось найти NFT")
                return False
                
            log_message(f"✅ Найдено NFT: {len(token_ids)}")
            
            for token_id in token_ids:
                # Сначала делаем approve
                nonce = w3.eth.get_transaction_count(sender_address)
                
                approve_tx = nft_contract.functions.approve(
                    Web3.to_checksum_address(to_address),
                    token_id
                ).build_transaction({
                    'chainId': 2741,
                    'gas': 0,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce,
                })
                
                # Оцениваем газ для approve
                gas_estimate = w3.eth.estimate_gas({
                    'from': sender_address,
                    'to': NFT_ADDRESS,
                    'data': approve_tx['data']
                })
                
                approve_tx.update({'gas': gas_estimate})
                
                log_message(f"✍️ Подписание разрешения для NFT #{token_id}...")
                signed = Account.sign_transaction(approve_tx, from_private_key)
                
                log_message("📤 Отправка разрешения...")
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                
                log_message("⏳ Ожидание подтверждения разрешения...")
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                log_message("✅ Разрешение получено")
                time.sleep(0.1)
                
                # Теперь делаем transferFrom
                nonce = w3.eth.get_transaction_count(sender_address)
                
                transfer_tx = nft_contract.functions.transferFrom(
                    sender_address,
                    Web3.to_checksum_address(to_address),
                    token_id
                ).build_transaction({
                    'chainId': 2741,
                    'gas': 0,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce,
                })
                
                # Оцениваем газ
                gas_estimate = w3.eth.estimate_gas({
                    'from': sender_address,
                    'to': NFT_ADDRESS,
                    'data': transfer_tx['data']
                })
                
                transfer_tx.update({'gas': gas_estimate})
                
                log_message(f"✍️ Подписание транзакции для NFT #{token_id}...")
                signed = Account.sign_transaction(transfer_tx, from_private_key)
                
                log_message("📤 Отправка транзакции...")
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                
                log_message("⏳ Ожидание подтверждения...")
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                log_message(f"✅ Успешно переведен NFT #{token_id}")
                log_message(f"🔗 Хэш транзакции: {receipt['transactionHash'].hex()}")
                
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            log_message(f"❌ Ошибка при отправке: {str(e)}")
            return False
                
    except Exception as e:
        log_message(f"❌ Ошибка: {str(e)}")
        return False

def collect_nfts_from_csv(filename: str, destination_address: str):
    """Собирает все NFT со всех приватных ключей из CSV"""
    log_message("🔄 Начало сбора NFT")
    
    if not os.path.exists(filename):
        log_message(f"❌ Файл {filename} не найден")
        return
    
    successful_transactions = 0
    
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            rows = list(reader)
            
            log_message(f"📋 Найдено кошельков для проверки: {len(rows) * 2}")
            
            processed_keys = set()
            
            for row in rows:
                for private_key in row[:2]:
                    private_key = private_key.strip()
                    
                    if private_key in processed_keys:
                        continue
                    
                    processed_keys.add(private_key)
                    
                    log_message(f"\n{'='*50}")
                    success = transfer_nft(private_key, destination_address)
                    
                    if success:
                        successful_transactions += 1
                    
                    time.sleep(0.2)
            
            log_message(f"\n{'='*50}")
            log_message(f"✨ Сбор NFT завершен")
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
    
    # Адрес для сбора NFT
    destination_address = "ВАШ АДРЕС"
    
    # Запуск сбора NFT
    collect_nfts_from_csv("wallets.csv", destination_address) 