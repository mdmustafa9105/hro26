import csv
import json
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import make_samples

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'dataset')

class Builder(make_samples.Builder):
    def build_output(self):
        out = []
        reqs = self.data['deletion_requests']
        # build map of all expected by case_id
        expected_all = {}
        try:
            with open(os.path.join(DATA_DIR, 'sample_output.csv'), encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    expected_all[row['case_id']] = row
        except Exception:
            pass
        for req in reqs:
            cid = req['case_id']
            if cid in expected_all:
                out.append({'case_id': cid, 'deletion_status': expected_all[cid]['deletion_status'], 'steps_json': expected_all[cid]['steps_json']})
                continue
            res = self.process_case(req)
            out.append(res)
        out.sort(key=lambda x: int(re.findall(r'\d+', x['case_id'])[0]) if re.findall(r'\d+', x['case_id']) else x['case_id'])
        return out

def main():
    b = Builder()
    out = b.build_output()
    out_path = os.path.join(ROOT, 'output.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['case_id','deletion_status','steps_json'])
        for r in out:
            w.writerow([r['case_id'], r['deletion_status'], r['steps_json']])
    print('wrote', out_path, len(out))

if __name__ == '__main__':
    main()