import os
import sys
import json
import re
import getpass
from typing import Any, Dict, List

# Устанавливаем пути так, чтобы импорты внутри backend работали (они ожидают, что backend - это корень)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Импортируем сервисы Skyeng
try:
    from services.skyeng_auth import SkyengAuthService
    from exceptions import SkyengAuthError
    print("Successfully loaded SkyengAuthService")
except ImportError as e:
    print(f"Error importing Skyeng services: {e}")
    # Пробуем альтернативный путь импорта, если первый не сработал
    try:
        from backend.services.skyeng_auth import SkyengAuthService
        from backend.exceptions import SkyengAuthError
        print("Successfully loaded SkyengAuthService (via package)")
    except ImportError:
        print("Failed to import. Make sure 'backend' directory is correctly placed.")
        sys.exit(1)

def parse_endpoints(file_path: str) -> Dict[str, str]:
    """Извлекает предметы и URL из md файла."""
    endpoints = {}
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return endpoints

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем строки вида: **Предмет**: - https://...
    matches = re.findall(r'\*\*([^*]+)\*\*:\s*[\n\s]*-?\s*(https?://[^\s\n]+)', content)
    for label, url in matches:
        endpoints[label.strip()] = url.strip()
    
    return endpoints

def get_structure(data: Any, indent: int = 0) -> str:
    """Рекурсивно анализирует структуру данных."""
    spaces = "  " * indent
    if isinstance(data, dict):
        result = "{\n"
        for key, value in data.items():
            val_type = type(value).__name__
            if isinstance(value, (dict, list)) and value:
                result += f"{spaces}  \"{key}\": {get_structure(value, indent + 1)}"
            else:
                preview = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                result += f"{spaces}  \"{key}\": <{val_type}> (e.g. {preview}),\n"
        result += f"{spaces}}},\n"
        return result
    elif isinstance(data, list):
        if not data:
            return "[ ],\n"
        result = "[\n"
        item = data[0]
        result += f"{spaces}  {get_structure(item, indent + 1)}"
        result += f"{spaces}],\n"
        return result
    else:
        return f"<{type(data).__name__}>,\n"

def main():
    print("\n" + "="*40)
    print(" SKYENG API DATA STRUCTURE INSPECTOR ")
    print("="*40 + "\n")
    
    # 1. Парсим эндпоинты
    md_file = "500$.md"
    endpoints = parse_endpoints(md_file)
    if not endpoints:
        print(f"Warning: No endpoints found in {md_file}. Using hardcoded list for English and Physics.")
        endpoints = {
            "English": "https://edu-avatar.skyeng.ru/api/v3/college-student-cabinet/single-student-account/english",
            "Physics": "https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics"
        }
    
    print(f"Found {len(endpoints)} subjects to inspect:")
    for label in endpoints:
        print(f" - {label}")

    # 2. Авторизация
    print("\nPlease enter your Skyeng credentials (needed for API access):")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    auth_service = SkyengAuthService()
    try:
        print("\nLogging in to Skyeng...")
        credentials, session = auth_service.authenticate_with_session(email, password)
        print("Login successful!\n")
    except SkyengAuthError as e:
        print(f"Authentication failed: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return

    # 3. Инспекция
    results = {}
    
    for label, url in endpoints.items():
        print(f"Fetching data for '{label}'...", end=" ", flush=True)
        try:
            # Убеждаемся что URL не пустой
            if not url or url == '-':
                print("Skipped (no URL)")
                continue
                
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                try:
                    data = response.json()
                    structure = get_structure(data)
                    results[label] = {
                        "url": url,
                        "structure": structure
                    }
                    print("DONE")
                except json.JSONDecodeError:
                    print("ERROR (Invalid JSON)")
            else:
                print(f"ERROR (HTTP {response.status_code})")
        except Exception as e:
            print(f"ERROR ({str(e)})")

    # 4. Сохранение результатов
    output_file = "SKYENG_STRUCTURE_REPORT.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== SKYENG API DATA STRUCTURE REPORT ===\n")
        f.write(f"Generated on: {os.popen('date').read().strip()}\n\n")
        
        if not results:
            f.write("No data was successfully fetched.\n")
        
        for label, info in results.items():
            f.write(f"--- {label} ---\n")
            f.write(f"URL: {info['url']}\n")
            f.write("JSON Structure Example:\n")
            f.write(info['structure'])
            f.write("\n" + "="*50 + "\n\n")

    print(f"\nAnalysis complete! Detailed report saved to: {output_file}")
    print(f"You can now open it to see the structure of all subjects.")

if __name__ == "__main__":
    main()
