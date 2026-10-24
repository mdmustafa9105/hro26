t = "I\u2019m deleting my account."
t2 = t.replace('\u2019', "'")
print('delete' in t2.lower())
