pip install -r requirements.txt в терминале


В wallets.csv в формате
from_private_key,to_private_key


Сумма для отправки в main.py amount_to_send = 0.0031 меняете на любую свою


В token_collector и collector снизу ваш адрес вставьте для сбора

balance.py - проверяет балик
collector.py - собирает эфир
main.py - раскидывает эфир
token_collector.py - собирает нфт

wallets.csv должен выглядеть так
from_private_key,to_private_key
приватоткуда,куда
приватоткуда,куда

Приват откуда можете вставлять одинаковый
Для сбора нфт и денег - он просто возьмет все приваты которые вставлены и отправит на destination_address = "ВАШАДРЕС" который снизу в файлах token_collector.py и collector.py
