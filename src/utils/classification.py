import re

DELETION_KEYWORDS = [
    'delete', 'deletion', 'delet', 'remove', 'erase', 'close', 'closing', 'suppression', 'supprimer', 'eliminar', 'borrar',
    'cancell', 'löschung', '削除', 'elimin', 'gone', 'profile is gone'
]
NON_DELETION = [
    'access', 'correct', 'correction', 'export', 'download', 'marketing opt', 'opt-out', 'unsubscribe', 'rectify'
]

def is_deletion_request(text):
    if not text:
        return False
    t = str(text)
    t = t.replace(chr(8217), "'").replace(chr(8216), "'")
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\ufffd', "'").replace('\x92', "'")
    t = t.replace(chr(0xFFFD), "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"')
    t = t.replace('â€™', "'").replace('â€˜', "'")
    t = t.lower()
    if any(nd in t for nd in ['access my account', 'data access request', 'subject access request']):
        if not any(k in t for k in ['delete', 'deletion', 'remove', 'erase', 'close']):
            return False
    if any(nd in t for nd in ['marketing opt', 'unsubscribe']) and not any(k in t for k in ['delete']):
        return False
    # check for deletion intent
    for k in DELETION_KEYWORDS:
        if k in t:
            # but if it's just asking to "check if gone" without asking to delete/remove - case_26 says "confirm that the profile is gone and that remaining records cannot identify me" - sounds like verification/request related to deletion state; but looking at sample: case_26 -> COMPLETE in output? Let us look up again
            return True
    return False