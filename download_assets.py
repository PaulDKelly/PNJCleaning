import urllib.request
import os

# Ensure directories exist
base_dir = "laravel/public/vendor"
os.makedirs(base_dir, exist_ok=True)

assets = [
    ("https://cdn.jsdelivr.net/npm/daisyui@3.1.0/dist/full.css", "daisyui.css"),
    ("https://cdn.tailwindcss.com", "tailwind.js"), # This is the Play CDN script
    ("https://unpkg.com/htmx.org@1.9.2", "htmx.js"),
    ("https://unpkg.com/hyperscript.org@0.9.9", "hyperscript.js")
]

for url, filename in assets:
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(os.path.join(base_dir, filename), 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
