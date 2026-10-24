import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

deletion_keywords = [
    'delet', 'eras', 'remov', 'clos', 'supprim', 'suppression',
    'elimina', 'exclus', '삭제', '削除', 'lösch', 'cancell',
    'forget', 'olvid', 'oublie', 'esquec'
]

non_deletion = []
deletion = []

with open('dataset/deletion_requests.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        txt = row['request_text'].lower()
        is_del = any(k in txt for k in deletion_keywords)
        if not is_del:
            non_deletion.append((row['case_id'], row['email'], row['request_text']))
        else:
            deletion.append((row['case_id'], row['email'], row['request_text']))

print(f"Total deletion: {len(deletion)}")
print(f"Total non-deletion: {len(non_deletion)}")
print("\nNon-deletion requests:")
for c_id, email, txt in non_deletion:
    print(f"{c_id} | {txt}")
