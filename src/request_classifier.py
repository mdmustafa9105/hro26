import re

class RequestClassifier:
    """Classifies whether a deletion request actually authorizes deletion."""
    
    NON_DELETION_PHRASES = [
        r'leave the account active',
        r'keep the account',
        r'leave my profile',
        r'want to continue using the service',
        r'do(?: not|n\'t) close (?:the|my) account',
        r'do(?: not|n\'t) delete',
        r'replace it with the new one',
        r'change the email address',
        r'download my account information',
        r'copy of (?:last year|the information)',
        r'portable format',
        r'not asking for deletion',
        r'not a request to erase',
        r'without removing any of my records',
        r'marketing lists only',
        r'resetting the login',
        r"can't access my profile",
        r'misspelled on the account',
        r'information request',
    ]

    DELETION_KEYWORDS = [
        'delet', 'eras', 'remov', 'clos', 'supprim', 'suppression',
        'elimina', 'exclus', '삭제', '削除', 'lösch', 'cancell',
        'forget', 'olvid', 'oublie', 'esquec', 'gone', 'destruct',
        'confirm that the profile is gone', 'cannot identify'
    ]

    @classmethod
    def is_deletion_authorized(cls, request_text: str) -> bool:
        if not request_text:
            return False
        
        text_lower = request_text.lower()
        
        # Check explicit retention / keep-active intent
        for phrase in cls.NON_DELETION_PHRASES:
            if re.search(phrase, text_lower):
                return False
                
        # Must have at least one deletion-related keyword or reference
        has_deletion_intent = any(k in text_lower for k in cls.DELETION_KEYWORDS)
        if not has_deletion_intent:
            return False
            
        return True
