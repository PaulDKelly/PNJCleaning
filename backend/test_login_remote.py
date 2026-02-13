import requests

url = "https://pnj-cleaning-test.redbeach-d7680450.uksouth.azurecontainerapps.io/login"
data = {"username": "admin", "password": "admin123"}

try:
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Cookies: {response.cookies.get_dict()}")
    if response.status_code == 200 and "access_token" in response.cookies:
        print("Login SUCCESS")
    else:
        print("Login FAILED")
        print(response.text[:200])
except Exception as e:
    print(f"Error: {e}")
