import csv
import os
from typing import Dict, Optional, Set
from src.models import UserIdentity

class IdentityResolver:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.identities_by_id: Dict[str, UserIdentity] = {}
        self.email_to_user_id: Dict[str, str] = {}
        self._load_identities()
        self._load_audit_log()

    def _load_identities(self):
        path = os.path.join(self.dataset_dir, 'user_identities.csv')
        with open(path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                uid = row['user_id'].strip()
                name = row['name'].strip()
                email = row['email'].strip().lower()
                phone = row['phone'].strip()
                email_hash = row['email_hash'].strip().lower()

                ident = UserIdentity(
                    user_id=uid,
                    name=name,
                    emails={email} if email else set(),
                    phones={phone} if phone else set(),
                    email_hashes={email_hash} if email_hash else set(),
                    names={name} if name else set(),
                )
                self.identities_by_id[uid] = ident
                if email:
                    self.email_to_user_id[email] = uid

    def _load_audit_log(self):
        path = os.path.join(self.dataset_dir, 'user_audit_log.csv')
        if not os.path.exists(path):
            return
        with open(path, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                uid = row['user_id'].strip()
                field = row['field_name'].strip()
                old_val = row['old_value'].strip()
                new_val = row['new_value'].strip()

                if uid not in self.identities_by_id:
                    continue

                ident = self.identities_by_id[uid]
                if field == 'email':
                    if old_val:
                        ident.emails.add(old_val.lower())
                        self.email_to_user_id.setdefault(old_val.lower(), uid)
                    if new_val:
                        ident.emails.add(new_val.lower())
                        self.email_to_user_id.setdefault(new_val.lower(), uid)
                elif field == 'phone':
                    if old_val:
                        ident.phones.add(old_val)
                    if new_val:
                        ident.phones.add(new_val)
                elif field == 'email_hash':
                    if old_val:
                        ident.email_hashes.add(old_val.lower())
                    if new_val:
                        ident.email_hashes.add(new_val.lower())
                elif field == 'name':
                    if old_val:
                        ident.names.add(old_val)
                    if new_val:
                        ident.names.add(new_val)

    def resolve_by_email(self, email: str) -> Optional[UserIdentity]:
        e_clean = email.strip().lower()
        uid = self.email_to_user_id.get(e_clean)
        if uid:
            return self.identities_by_id.get(uid)
        return None

    def resolve_by_user_id(self, user_id: str) -> Optional[UserIdentity]:
        return self.identities_by_id.get(user_id.strip())
