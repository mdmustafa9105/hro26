t = "I\u2019m deleting my account."
t2 = t.replace(chr(0x2019), "'")
print('delete' in t2.lower())
