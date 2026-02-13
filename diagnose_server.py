import urllib.request
import urllib.error

base_url = "http://127.0.0.1:8000"

def check_url(url, description):
    print(f"Checking {description} ({url})...")
    try:
        with urllib.request.urlopen(url) as response:
            print(f"  Status: {response.status}")
            content = response.read().decode('utf-8')
            print(f"  Content Length: {len(content)}")
            return content
    except urllib.error.HTTPError as e:
        print(f"  Failed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"  Error: {e}")
    return None

# 1. Check Login Page (uses app layout)
html = check_url(f"{base_url}/login", "Login Page")
if html:
    if "daisyui.css" in html:
        print("  [SUCCESS] found 'daisyui.css' in HTML")
    else:
        print("  [FAILURE] 'daisyui.css' NOT found in HTML")
    
    if "background-color: #ffe4e6" in html:
        print("  [SUCCESS] found 'debug red background' in HTML")
    else:
        print("  [FAILURE] 'debug red background' NOT found in HTML")

# 2. Check Asset Availability
check_url(f"{base_url}/vendor/daisyui.css", "CSS File")
check_url(f"{base_url}/vendor/tailwind.js", "JS File")
