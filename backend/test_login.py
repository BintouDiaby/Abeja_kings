import requests
from urllib.parse import urljoin

BASE = 'http://127.0.0.1:8000'
LOGIN = urljoin(BASE, '/accounts/login/')
HOME = urljoin(BASE, '/')

s = requests.Session()
print('GET login page...')
resp = s.get(LOGIN)
print('GET status:', resp.status_code)
# Try to get csrf token from cookies or hidden input
csrftoken = s.cookies.get('csrftoken')
if not csrftoken:
    # try to parse from form
    import re
    m = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"]([0-9a-zA-Z:-]+)['\"]", resp.text)
    if m:
        csrftoken = m.group(1)

print('CSRF token:', bool(csrftoken))

creds = {'username':'admin@abeja.kings','password':'admin123','next':'/'}
headers = {'Referer': LOGIN}
if csrftoken:
    headers['X-CSRFToken'] = csrftoken

print('POST login...')
post = s.post(LOGIN, data=creds, headers=headers)
print('POST status:', post.status_code)
# Follow to home
r = s.get(HOME)
print('HOME status:', r.status_code)
if 'Se déconnecter' in r.text or 'Déconnexion' in r.text:
    print('Logout visible on dashboard ✅')
else:
    print('Logout NOT found on dashboard ❌')

# Print small snippet around user-actions
idx = r.text.find('user-actions')
if idx!=-1:
    print(r.text[idx:idx+400])
else:
    print('user-actions block not found in HTML')
