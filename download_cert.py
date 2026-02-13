import urllib.request
import ssl

# Bypass SSL context for the download itself if needed (meta-problem),
# but let's try standard download first.
# If this fails, we really have network issues.
url = "https://curl.se/ca/cacert.pem"
print(f"Downloading {url}...")
urllib.request.urlretrieve(url, "cacert.pem")
print("Downloaded cacert.pem")
