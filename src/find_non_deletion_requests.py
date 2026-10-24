import csv
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Search for keywords related to access, correction, export, marketing opt-out, etc.
patterns = [
    r'export', r'download', r'access', r'correct', r'update', r'marketing',
    r'unsubscribe', r'rectif', r'accès', r'télécharger', r'portab',
    r'newsletter', r'opt-out', r'opt out'
]

non_deletion = []
with open('dataset/deletion_requests.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        text = row['request_text']
        # check if it does NOT ask to delete/erase/remove/close account
        has_delete = any(w in text.lower() for w in [
            'delete', 'erased', 'erase', 'remove', 'close', 'closed', 'suppression',
            'supprimer', 'eliminar', 'eliminación', '削除', 'löschen', 'cancellare'
        ])
        
        # let's look at requests without explicit deletion keywords, or specifically asking for export/access only
        if not has_delete:
            non_deletion.append((row['case_id'], row['email'], text))

print(f"Total requests without obvious deletion keywords: {len(non_deletion)}")
for c_id, email, txt in non_deletion[:25]:
    print(f"{c_id} | {txt}")
