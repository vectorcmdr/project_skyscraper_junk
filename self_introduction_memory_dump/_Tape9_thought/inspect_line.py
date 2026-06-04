with open(r'C:\stack\arg\tapes_man_2\analysis_master.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[342]  # 0-indexed, line 343
print(repr(line))
for i,ch in enumerate(line):
    if ch in '()':
        print(i, ch)
