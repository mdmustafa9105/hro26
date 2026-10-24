import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check if details or other fields contain user identifiers
user_ids_found = 0
emails_found = 0
total = 0

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        d = row['details']
        if 'user_' in d:
            user_ids_found += 1
        if '@' in d:
            emails_found += 1

print(f"Total rows: {total}")
print(f"Rows with 'user_': {user_ids_found}")
print(f"Rows with '@': {emails_found}")
