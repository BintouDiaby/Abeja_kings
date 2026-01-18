from pathlib import Path
import re
p=Path('backend/core/templates/core/dashboard.html')
s=p.read_text(encoding='utf-8')
pattern=re.compile(r"({%\s*(endwith|endfor|endblock|endif|elif|else|if|with|for)\b[^%]*%})")
stack=[]
for m in pattern.finditer(s):
    full=m.group(1)
    tag=m.group(2)
    line=s.count('\n',0,m.start())+1
    print(f'{line:04d}: {full.strip()}')
    if tag in ('if','for','with'):
        stack.append((tag,line))
        print('  push',stack[-1])
    elif tag in ('else','elif'):
        print('  else/elif, top=', stack[-1] if stack else None)
    else:
        if not stack:
            print('  UNMATCHED', tag)
        else:
            opener=stack.pop()
            print('  pop',opener)
print('FINAL STACK:',stack)
