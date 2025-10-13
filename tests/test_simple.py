import requests
import time

time.sleep(2)
try:
    response = requests.get('http://127.0.0.1:8000/locations/', timeout=5)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        content = response.text
        if 'dashboard' in content.lower():
            print('Dashboard content found')
        elif 'error' in content.lower():
            print('Error found in content')
        else:
            print('Unexpected content')
    else:
        print(f'Non-200 status: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')




