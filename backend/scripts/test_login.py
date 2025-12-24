import requests
from bs4 import BeautifulSoup

BASE = 'http://127.0.0.1:8000'
LOGIN = BASE + '/accounts/login/'

cases = [
    ('ouvrier', 'password123'),
    ('ouvrier@abeja.kings', 'password123'),
    ('ouvrier_test', 'test1234'),
]

s = requests.Session()

for user, pwd in cases:
    print('\n--- Testing', user)
    # GET login page to get csrftoken cookie or form token
    r = s.get(LOGIN)
    print('GET', r.status_code)
    token = s.cookies.get('csrftoken')
    if not token:
        # try parse from form
        soup = BeautifulSoup(r.text, 'html.parser')
        inp = soup.find('input', {'name':'csrfmiddlewaretoken'})
        token = inp['value'] if inp else None
    print('csrftoken:', bool(token))
    payload = {
        'username': user,
        'password': pwd,
        'csrfmiddlewaretoken': token,
        'next': '/post-login/'
    }
    headers = {'Referer': LOGIN}
    r2 = s.post(LOGIN, data=payload, headers=headers, allow_redirects=True)
    print('POST', r2.status_code)
    print('Final URL:', r2.url)
    print('History:', [h.status_code for h in r2.history])
    # detect common failure hints
    if 'invalid' in r2.text.lower() or 'erreur' in r2.text.lower():
        print('Page contains error-like text')
    if r2.url.endswith('/accounts/login/'):
        print('Stayed on login page → login likely failed')
    else:
        print('Redirected to', r2.url)

print('\nDone')
