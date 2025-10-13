import requests
import time

time.sleep(2)
response = requests.get('http://127.0.0.1:8000/locations/', timeout=5, allow_redirects=False)
print(f'Status: {response.status_code}')
print(f'URL: {response.headers.get("Location", "Direct access")}')

# Also test the sites list page still works
response2 = requests.get('http://127.0.0.1:8000/locations/sites/', timeout=5, allow_redirects=False)
print(f'Site List Status: {response2.status_code}')




