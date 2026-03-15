from sites.apkcombo import get_versions, download_apk

candidates = [
    "https://apkcombo.com/com.twitter.android/",
    "https://apkcombo.com/x-corp-twitter/",
]

for url in candidates:
    print('\nTesting URL:', url)
    try:
        versions = get_versions(url)
        print('Found versions:', versions)
        if versions:
            print('Attempting to download first version...')
            download_apk(versions[0])
    except Exception as e:
        print('Error:', e)
