import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        print(f"{row['case_id']} | {row['email']} | {row['request_text']}")
