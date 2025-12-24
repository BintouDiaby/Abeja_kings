import requests
from bs4 import BeautifulSoup

BASE = 'http://127.0.0.1:8000'
LOGIN = BASE + '/accounts/login/'

CASES = [
    ('without remember', {}),
    ('with remember', {'remember_me': 'on'})
]

# Credentials: use existing test user 'ouvrier' created earlier
USERNAME = 'ouvrier'
PASSWORD = 'password123'

s = requests.Session()

for label, extra in CASES:
    s.cookies.clear()
    # GET login form to fetch csrftoken
    r = s.get(LOGIN)
    if r.status_code != 200:
        print(f"GET login returned {r.status_code}")
        continue

    # try to extract CSRF token from cookie or form
    csrf = s.cookies.get('csrftoken') or ''
    # Prepare payload
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'next': '/post-login/',
        'csrfmiddlewaretoken': csrf,
    }
    payload.update(extra)

    # POST without following redirects to capture Set-Cookie
    r2 = s.post(LOGIN, data=payload, headers={'Referer': LOGIN}, allow_redirects=False)
    print('\nCASE:', label)
    print('Status code:', r2.status_code)
    sc = r2.headers.get('Set-Cookie')
    print('Set-Cookie header:', sc)

    # Try to detect whether the sessionid cookie has an Expires attribute
    persistent = False
    if sc:
        # Split cookie header into cookie segments by ', ' but be cautious: cookie values
        # may contain commas. Use SimpleCookie for robust parsing.
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        cookie.load(sc)
        if 'sessionid' in cookie:
            morsel = cookie['sessionid']
            # morsel['expires'] returns empty string if not present
            expires = morsel.get('expires')
            if expires:
                persistent = True

    if persistent:
        print('-> Session cookie appears persistent (Expires present for sessionid).')
    else:
        print('-> Session cookie appears session-only (no Expires for sessionid).')

print('\nDone')
