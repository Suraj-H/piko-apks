import requests

url = 'https://apkcombo.com/com.twitter.android/'
print('Fetching', url)
resp = requests.get(url, verify=False)
print('Status', resp.status_code)
print(resp.text[:2000])
