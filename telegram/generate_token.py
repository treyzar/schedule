# generate_token.py

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# --- НАСТРОЙКИ ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_PATH = Path('token.json')
CLIENT_SECRET_PATH = Path('client_secrets.json')
# --- ГЛАВНОЕ ИЗМЕНЕНИЕ: УКАЗЫВАЕМ КОНКРЕТНЫЙ ПОРТ ---
REDIRECT_PORT = 8080 

def main():
    creds = None
    if TOKEN_PATH.exists():
        print("token.json уже существует. Если хочешь создать новый, удали старый файл.")
        return

    if not CLIENT_SECRET_PATH.exists():
        print(f"Ошибка: {CLIENT_SECRET_PATH} не найден. Пожалуйста, помести его в папку бота.")
        return

    print("Запуск процесса авторизации Google...")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), 
        SCOPES,
        # Указываем, что наш локальный сервер будет доступен по этому URI
        redirect_uri=f'http://localhost:{REDIRECT_PORT}/' 
    )
    
    # Запускаем сервер на ЗАФИКСИРОВАННОМ порту
    creds = flow.run_local_server(port=REDIRECT_PORT)

    with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
        token_file.write(creds.to_json())
    print(f"Токен успешно сохранен в {TOKEN_PATH}.")

if __name__ == '__main__':
    main()
