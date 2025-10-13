import requests
import time

time.sleep(2)
response = requests.get('http://127.0.0.1:8000/locations/sites/', timeout=5)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    content = response.text.lower()
    print(f'Contains tab navigation: {"nav-tabs" in content}')
    print(f'Contains breadcrumb: {"breadcrumb" in content}')
    print(f'Contains sites list: {"site" in content}')
    if 'error' in content:
        print('ERROR: Found error in content')
    else:
        print('SUCCESS: Sites page appears to be working')
else:
    print(f'Non-200 status: {response.status_code}')




