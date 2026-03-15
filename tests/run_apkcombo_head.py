from sites.apkcombo import get_versions
from bs4 import BeautifulSoup
import requests
from constants import HEADERS

candidates = [
    "https://apkcombo.com/com.twitter.android/",
    "https://apkcombo.com/x-corp-twitter/",
]

for url in candidates:
    print('\nTesting URL:', url)
    try:
        versions = get_versions(url)
        print('Found versions:', versions)
        if not versions:
            continue

        v = versions[0]
        print('Using version:', v)

        # reimplement download_apk logic but only HEAD the final link
        resp = requests.get(v.link, headers=HEADERS, verify=False)
        if resp.status_code != 200:
            print('Failed to fetch version page', resp.status_code)
            continue

        bs4 = BeautifulSoup(resp.text, 'html.parser')
        download_link = bs4.find('a', attrs={'class': 'variant'})
        if download_link is None:
            print('No variant link found')
            continue

        link = download_link.get('href')
        checkin = requests.get('https://apkcombo.com/checkin', headers=HEADERS, verify=False)
        if checkin.status_code != 200:
            print('Failed to fetch checkin', checkin.status_code)
            continue

        package_name = v.link.split('/')[4]
        direct_link = f"https://apkcombo.com{link}&{checkin.text}&package_name={package_name}"
        print('Direct link (HEAD only):', direct_link)

        # HEAD to get content-length and avoid downloading
        head = requests.head(direct_link, headers=HEADERS, verify=False, allow_redirects=True)
        print('HEAD status:', head.status_code)
        for k in ('Content-Length', 'Content-Type', 'Content-Disposition'):
            if k in head.headers:
                print(f"{k}: {head.headers[k]}")

    except Exception as e:
        print('Error:', e)
