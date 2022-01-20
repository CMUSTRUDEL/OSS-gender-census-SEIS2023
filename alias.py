import re

REX_FAKEUSR = re.compile(r'\A[A-Z]{8}$')
REX_EMAIL = re.compile(r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?")

class Alias:

    def __init__(self, record_type=None, uid=None, login=None, name=None, email=None, gender=None):
        
        self.record_type = record_type 
        self.uid = uid
        self.login = str(login)
        self.name = str(name).strip()
        
        # Handle email
        email = str(email).strip().lower()
        if email == 'none' or not len(email):
            email = None
        if " at " in email:
            email = email.replace(" at ", "@")
        if "[at]" in email:
            email = email.replace("[at]", "@")
        if " dot " in email:
            email = email.replace(" dot ", ".")
        if "(dot)" in email:
            email = email.replace("(dot)", ".")
        if "~dot~" in email:
            email = email.replace("~dot~", ".")
        if email is not None:
            me = REX_EMAIL.search(email)
            if me is None:
                if not email.endswith('.(none)'): # http://stackoverflow.com/a/897611/1285620
                    email = None
        if email is not None:
            if email.endswith('@server.fake') or \
                    email.endswith('@server.com') or \
                    email.endswith('@example.com') or \
                    email.endswith('@email.com'):
                email = None
            
        self.email = email
        
        prefix = None
        domain = None
        if email is not None:
            email_parts = email.split('@')
            if len(email_parts) > 1:
                prefix = email_parts[0]
                if not len(prefix):
                    prefix = None
                domain = email_parts[-1]
                if not len(domain):
                    domain = None
                if domain == 'users.noreply.github.com':
                    domain = None
        self.email_prefix = prefix
        self.email_domain = domain        
        self.gender = gender