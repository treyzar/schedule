import os
import json
import re
import getpass
import requests
from bs4 import BeautifulSoup
from typing import Any, Dict

def get_csrf_token(session, base_url):
    print(f"Fetching CSRF token from {base_url}/login...")
    response = session.get(f"{base_url}/login", timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrfToken"})
    if not csrf_input:
        raise Exception("CSRF token not found on login page")
    return csrf_input.get("value")

def login(email, password):
    id_url = "https://id.skyeng.ru"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
    })

    csrf_token = get_csrf_token(session, id_url)
    
    print("Submitting login form...")
    login_data = {
        "username": email,
        "password": password,
        "csrfToken": csrf_token,
    }
    
    headers = {
        'X-CSRF-Token': csrf_token,
        'Referer': f"{id_url}/login",
    }
    
    response = session.post(f"{id_url}/frame/login-submit", data=login_data, headers=headers, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    if not result.get("success"):
        raise Exception(f"Login failed: {result.get('message', 'Unknown error')}")
    
    if result.get("redirect"):
        print("Following SSO redirect...")
        session.get(result["redirect"], timeout=10)
    
    return session

def get_structure(data: Any, indent: int = 0) -> str:
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

def parse_endpoints(file_path: str) -> Dict[str, str]:
    endpoints = {}
    if not os.path.exists(file_path):
        return endpoints
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    matches = re.findall(r'\*\*([^*]+)\*\*:\s*[\n\s]*-?\s*(https?://[^\s\n]+)', content)
    for label, url in matches:
        endpoints[label.strip()] = url.strip()
    return endpoints

def main():
    print("\n=== SKYENG LITE INSPECTOR ===")
    md_file = "500$.md"
    endpoints = parse_endpoints(md_file)
    
    if not endpoints:
        print("No endpoints found in 500$.md. Using fallbacks.")
        endpoints = {"Physics": "https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics"}

    email = input("Email: ")
    password = getpass.getpass("Password: ")

    try:
        session = login(email, password)
        print("Login successful!\n")
        
        results = {}
        for label, url in endpoints.items():
            print(f"Fetching {label}...", end=" ", flush=True)
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code == 200:
                    structure = get_structure(resp.json())
                    results[label] = {"url": url, "structure": structure}
                    print("OK")
                else:
                    print(f"FAIL (HTTP {resp.status_code})")
            except Exception as e:
                print(f"ERROR: {e}")

        with open("SKYENG_STRUCTURE_REPORT.txt", "w", encoding="utf-8") as f:
            for label, info in results.items():
                f.write(f"--- {label} ---\nURL: {info['url']}\nStructure:\n{info['structure']}\n{'='*50}\n\n")
        
        print("\nReport saved to SKYENG_STRUCTURE_REPORT.txt")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
