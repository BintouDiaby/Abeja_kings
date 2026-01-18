from pathlib import Path
import re
p=Path('backend/core/templates/core/dashboard.html')
s=p.read_text(encoding='utf-8')
pattern=re.compile(r"{%\s*(endwith|endfor|endblock|endif|elif|else|if|with|for)\b[^%]*%}")
stack=[]
for m in pattern.finditer(s):
    tag=m.group(1)
    line=s.count('\n',0,m.start())+1
    if tag in ('if','for','with'):
        stack.append((tag,line))
    elif tag in ('else','elif'):
        if not stack or stack[-1][0] not in ('if', 'for'):
            print(f'Orphan {tag} at line {line}')
    else:
        if not stack:
            print(f'Unmatched {tag} at line {line}')
        else:
            opener=stack.pop()
            if tag=='endif' and opener[0]!='if':
                print(f'Mismatch: closed endif at line {line} but opener is {opener}')
            if tag=='endwith' and opener[0]!='with':
                print(f'Mismatch: closed endwith at line {line} but opener is {opener}')

if stack:
    print('Remaining stack:')
    for item in stack:
        print(item)
else:
    print('All tags matched')
