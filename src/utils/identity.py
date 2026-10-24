from ..data import loader
from datetime import timezone

class IdentityResolver:
    def __init__(self, data):
        self.identities = data['identities']
        self.audit = data['audit']
        # build indexes
        self.by_email = {}
        self.by_user = {}
        self.by_phone = {}
        self.by_hash = {}
        for row in self.identities:
            uid = row['user_id']
            self.by_user[uid] = row
            em = loader.norm_email(row.get('email',''))
            if em:
                self.by_email[em] = row
            ph = (row.get('phone') or '').strip()
            if ph:
                self.by_phone[ph] = row
            h = (row.get('email_hash') or '').strip()
            if h:
                self.by_hash[h] = row
        # audit by user
        self.audit_by_user = {}
        for row in self.audit:
            uid = row['user_id']
            self.audit_by_user.setdefault(uid, []).append(row)
        for uid in self.audit_by_user:
            self.audit_by_user[uid].sort(key=lambda x: loader.parse_ts(x['event_time']) or loader.parse_ts('1900-01-01T00:00:00Z'))

    def resolve(self, email):
        em = loader.norm_email(email)
        matches = []
        # current match
        if em in self.by_email:
            matches.append(self.by_email[em])
        # search audit logs for old/new values matching email
        for uid, rows in self.audit_by_user.items():
            for r in rows:
                ov = loader.norm_email(r.get('old_value',''))
                nv = loader.norm_email(r.get('new_value',''))
                if ov == em or nv == em:
                    if uid in self.by_user and self.by_user[uid] not in matches:
                        matches.append(self.by_user[uid])
                    break  # found user for this email
        # also search any audit old/new by direct string contains email
        if not matches:
            for uid, rows in self.audit_by_user.items():
                for r in rows:
                    if em and em in str(r.get('old_value','')).lower():
                        if uid in self.by_user and self.by_user[uid] not in matches:
                            matches.append(self.by_user[uid])
                        break
                    if em and em in str(r.get('new_value','')).lower():
                        if uid in self.by_user and self.by_user[uid] not in matches:
                            matches.append(self.by_user[uid])
                        break
        return matches

    def get_identifiers(self, user_row):
        ids = set()
        if not user_row:
            return ids
        uid = user_row['user_id']
        # current
        if user_row.get('email'):
            ids.add(loader.norm_email(user_row['email']))
        if user_row.get('phone'):
            ids.add(user_row['phone'].strip())
        if user_row.get('email_hash'):
            ids.add(user_row['email_hash'].strip())
        ids.add(uid)
        # historical
        for r in self.audit_by_user.get(uid, []):
            for key in ['old_value','new_value']:
                v = r.get(key)
                if not v:
                    continue
                v2 = str(v).strip()
                # try as email
                ve = loader.norm_email(v2)
                if '@' in ve:
                    ids.add(ve)
                else:
                    ids.add(v2)
            # also add field name context not needed
        return ids
