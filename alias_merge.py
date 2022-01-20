import os
import re
fakeusr_rex = re.compile(r'\A[A-Z]{8}$')

from alias import Alias
from collections import Counter
from itertools import combinations, product

USR_FAKE = 'FAKE'
USR_REAL = 'REAL'

EMAIL               = 'EMAIL'
COMP_EMAIL_PREFIX   = 'COMP_EMAIL_PREFIX'
SIMPLE_EMAIL_PREFIX = 'SIMPLE_EMAIL_PREFIX'
PREFIX_LOGIN        = 'PREFIX_LOGIN'
PREFIX_NAME         = 'PREFIX_NAME'
LOGIN_NAME          = 'LOGIN_NAME'
FULL_NAME           = 'FULL_NAME'
SIMPLE_NAME         = 'SIMPLE_NAME'
NAME_PARTS          = 'NAME_PARTS'
NAME_APPENDED       = 'NAME_APPENDED'
DOMAIN              = 'EMAIL_DOMAIN'
TWO                 = 'TWO_OR_MORE_RULES'

THR_MIN = 1
THR_MAX = 20


def resolve_aliases(inputs):
    print_flag = 0

    unmask = {}
    aliases = {}

    # Helper structures
    d_email_uid = {}
    d_uid_email = {}

    d_prefix_uid = {}
    d_uid_prefix = {}

    d_comp_prefix_uid = {}
    d_uid_comp_prefix = {}

    d_uid_domain = {}
    d_domain_uid = {}

    d_name_uid = {}
    d_uid_name = {}
    
    d_name_parts_uid = {}
    d_uid_name_parts = {}

    d_name_app_uid = {}
    d_uid_app_parts = {}

    d_login_uid = {}
    d_uid_login = {}

    d_uid_type = {}
    #d_type_usr = {}

    uid = 0

    for ind, row in inputs.iterrows():
        
        uid = row["uid"]
        name = row["name"]
        email = row["email"]
        login = row["login"]
        
        unmask[uid] = uid

        if not row["fake"]:
          record_type = USR_REAL
        else:
          record_type = USR_FAKE
        
        a = Alias(record_type, uid, login, name, email)
        aliases[uid] = a

        # - email
        d_uid_email[a.uid] = a.email
        if a.email is not None:
            d_email_uid.setdefault(a.email, set([a.uid]))
            d_email_uid[a.email].add(a.uid)
            
        # - prefix
        d_uid_prefix[a.uid] = a.email_prefix
        d_uid_comp_prefix[a.uid] = a.email_prefix
        if a.email_prefix is not None:
            if len(a.email_prefix.split('.')) > 1 or len(a.email_prefix.split('_')) > 1:
                d_comp_prefix_uid.setdefault(a.email_prefix, set([a.uid]))
                d_comp_prefix_uid[a.email_prefix].add(a.uid)
            else:
                d_prefix_uid.setdefault(a.email_prefix, set([a.uid]))
                d_prefix_uid[a.email_prefix].add(a.uid)
            
        # - domain
        d_uid_domain[a.uid] = a.email_domain
        if a.email_domain is not None:
            d_domain_uid.setdefault(a.email_domain, set([a.uid]))
            d_domain_uid[a.email_domain].add(a.uid)
        
        # - login
        d_uid_login[a.uid] = a.login
        if a.login is not None:
            d_login_uid.setdefault(a.login, set([a.uid]))
            d_login_uid[a.login].add(a.uid)
            
            if a.record_type == USR_REAL:
                d_login_uid.setdefault(a.login.lower(), set([a.uid]))
                d_login_uid[a.login.lower()].add(a.uid)
        
        # - name
        d_uid_name[a.uid] = a.name
        if a.name is not None and len(a.name):
            d_name_uid.setdefault(a.name, set([a.uid]))
            d_name_uid[a.name].add(a.uid)
            
            if len(a.name.split(' ')) == 1:
                d_name_uid.setdefault(a.name.lower(), set([a.uid]))
                d_name_uid[a.name.lower()].add(a.uid)

                # janejohnson -> janejohnson
                # we need this for matching
                d_name_app_uid.setdefault(a.name.lower(), set([a.uid]))
                d_name_app_uid[a.name.lower()].add(a.uid)

            # jane johnson -> janejohnson
            d_name_app_uid.setdefault("".join(a.name.split(" ")).lower(), set([a.uid]))
            d_name_app_uid["".join(a.name.split(" ")).lower()].add(a.uid)
            
            if "@" in a.name: # otherwise it will make "gmail", "com" as names
                name_subpart = a.name.split("@")[0]
                d_name_parts_uid.setdefault(name_subpart.lower(), set([a.uid]))
                d_name_parts_uid[name_subpart.lower()].add(a.uid)
            else: 
                # xiyi ji -> ji xiyi
                name_parts_split = a.name.lower().replace(",", " ").replace(".", " ").split(' ')
                if len(name_parts_split) != 2:
                    continue
                new_name_parts = name_parts_split[-1] + " " + name_parts_split[0]
                d_name_parts_uid.setdefault(new_name_parts, set([a.uid]))
                d_name_parts_uid[new_name_parts].add(a.uid)

    # print 'Done: helpers'

    clues = {}

    for email, set_uid in d_email_uid.items():
        if len(set_uid) > THR_MIN:
            for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(EMAIL)
    #                print a,b,EMAIL
                
    # print 'Done: email'
                
    for prefix, set_uid in d_comp_prefix_uid.items():
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            if len(prefix) >= 3:
                for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(COMP_EMAIL_PREFIX)
    #                    print a,b,COMP_EMAIL_PREFIX

    # print 'Done: comp email prefix'                

    for prefix, set_uid in d_prefix_uid.items():
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            if len(prefix) >= 3:
                for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(SIMPLE_EMAIL_PREFIX)
    #                    print a,b,SIMPLE_EMAIL_PREFIX

    # print 'Done: email prefix'
                    
    for prefix in set(d_prefix_uid.keys()).intersection(set(d_login_uid.keys())):
        if len(d_prefix_uid[prefix]) < THR_MAX:
            for a,b in product(sorted(d_login_uid[prefix], key=lambda uid:int(uid)), sorted(d_prefix_uid[prefix], key=lambda uid:int(uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if not SIMPLE_EMAIL_PREFIX in clues[(a, b)]:
                        clues[(a, b)].append(PREFIX_LOGIN)
    #                    print a,b,PREFIX_LOGIN
                    
    # print 'Done: prefix=login'

    for prefix in set(d_prefix_uid.keys()).intersection(set(d_name_uid.keys())):
        if len(d_prefix_uid[prefix]) < THR_MAX and len(d_name_uid[prefix]) < THR_MAX:
            for a,b in product(sorted(d_name_uid[prefix], key=lambda uid:int(uid)), sorted(d_prefix_uid[prefix], key=lambda uid:int(uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if not SIMPLE_EMAIL_PREFIX in clues[(a, b)]:
                        clues[(a, b)].append(PREFIX_NAME)

    # print 'Done: prefix=name'

    for prefix in set(d_login_uid.keys()).intersection(set(d_name_uid.keys())):
        if len(d_name_uid[prefix]) < THR_MAX:
            for a,b in product(sorted(d_name_uid[prefix], key=lambda uid:int(uid)), sorted(d_login_uid[prefix], key=lambda uid:int(uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if not SIMPLE_EMAIL_PREFIX in clues[(a, b)]:
                        clues[(a, b)].append(LOGIN_NAME)

    # print 'Done: login=name'
                    
    for name, set_uid in d_name_uid.items():
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            if len(name.split(' ')) > 1:
                for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(FULL_NAME)
            else:
                for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(SIMPLE_NAME)
                        
    # print 'Done: full/simple name'

    for name, set_uid in d_name_parts_uid.items():
        #out.write(name + "," + str(set_uid) + "\n")
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(NAME_PARTS)

    #out.write("\n")
                        
    # print 'Done: name parts'

    for name, set_uid in d_name_app_uid.items():
        #out.write(name + "," + str(set_uid))
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(NAME_APPENDED)
                        
    # print 'Done: name parts appended'

    for domain, set_uid in d_domain_uid.items():
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            for a,b in combinations(sorted(set_uid, key=lambda uid:int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(DOMAIN)
                    
    # print 'Done: email domain'


    d_alias_map = {}
    clusters = {}
    labels = {}

    def merge(a,b,rule):
        # Contract: a < b 
        assert a<b, "A must be less than B"
        if a in d_alias_map:
            if b in d_alias_map:
                if d_alias_map[a] == d_alias_map[b]:
                    labels[d_alias_map[a]].append(rule)
                else:
                    lowest = min(d_alias_map[a], d_alias_map[b])
                    highest = max(d_alias_map[a], d_alias_map[b])
                    labels[lowest].extend(labels[highest])
                    labels[lowest].append(rule)
                    clusters[lowest].update(clusters[highest])
                    for x in clusters[highest]: d_alias_map[x] = lowest
                    del labels[highest]
                    del clusters[highest]
                    d_alias_map[a] = lowest
                    d_alias_map[b] = lowest
                
            else:
                # a is an alias; first time I see b
                d_alias_map[b] = d_alias_map[a]
                clusters[d_alias_map[a]].add(b)
                labels[d_alias_map[a]].append(rule)
        else:
            if b in d_alias_map:
                #b_src = d_alias_map[b] # b_src < a by construction
                d_alias_map[a] = d_alias_map[b]
                clusters[d_alias_map[b]].add(a)
                labels[d_alias_map[b]].append(rule)
            else:
                # First time I see this pair (guaranteed sorted)
                d_alias_map[a] = a
                d_alias_map[b] = a
                clusters[a] = set([a,b])
                labels[a] = [rule]
    
    
    for (a,b), list_clues in sorted(clues.items(), key=lambda e:(int(e[0][0]),int(e[0][1]))):
        if print_flag:
            print (((a,b), list_clues))
        aa = aliases[a]
        ab = aliases[b]
        
        if EMAIL in list_clues:
            merge(a,b,EMAIL)
        elif len(set(list_clues)) >= 2:
            for clue in set(list_clues):
                merge(a,b,clue)
        elif FULL_NAME in list_clues:
            merge(a,b,FULL_NAME)
        elif NAME_APPENDED in list_clues:
            merge(a, b, NAME_APPENDED)
        elif NAME_PARTS in list_clues:
            merge(a, b, NAME_PARTS)
        elif COMP_EMAIL_PREFIX in list_clues:
            merge(a,b,COMP_EMAIL_PREFIX)
        elif SIMPLE_NAME in list_clues:
            merge(a,b,SIMPLE_NAME)
        elif PREFIX_NAME in list_clues:
            merge(a,b,PREFIX_NAME)
        

    # print 'Done: clusters'
            
    for uid, member_uids in clusters.items():
        # print ((uid, member_uids))
        members = [aliases[m] for m in member_uids]

        # Count fake/real
        c = Counter([m.record_type for m in members])
        real = [m for m in members if m.record_type==USR_REAL]
        fake = [m for m in members if m.record_type==USR_FAKE]

        # Count rules that fired
        cl = Counter(labels[uid])
        if print_flag:
            print (cl)

        is_valid = False

        # If all have the same email there is no doubt
        if cl.get(EMAIL,0) >= (len(members)-1):
            is_valid = True
        # If all the REALs have the same email, assume all the FAKEs are this REAL
        elif len(Counter([m.email for m in real]).keys()) == 1:
            is_valid = True
        # If there is at most one real, at least two rules fired, and each rule applied to each pair
        elif len(cl.keys()) > 1 and min(cl.values()) >= (len(members)-1):
            is_valid = True
        # At most one real, the only rule that fired is COMP_EMAIL_PREFIX or FULL_NAME
        elif len(cl.keys()) == 1 and \
                (cl.get(COMP_EMAIL_PREFIX,0) or cl.get(FULL_NAME,0) or \
                 cl.get(NAME_PARTS,0) or cl.get(NAME_APPENDED,0)):
            is_valid = True 
        # All with same full name and same full name and email domain
        elif cl.get(FULL_NAME,0) >= (len(members)-1) and \
                cl.get(DOMAIN,0) >= (len(members)-1):
            is_valid = True
        # All same composite email prefix / same full name
        elif (cl.get(COMP_EMAIL_PREFIX,0) >= (len(members)-1) or cl.get(FULL_NAME,0) >= (len(members)-1)):
            is_valid = True
        elif cl.get(NAME_APPENDED,0) >= (len(members)-1):
            is_valid = True
        elif cl.get(FULL_NAME,0) >= (len(members)-1):
            is_valid = True
        # The only two rules that fired are full name and email, in some combination
        elif len(cl.keys()) == 2 and cl.get(FULL_NAME,0) > 0 and cl.get(EMAIL,0) > 0:
            is_valid = True
        elif len(cl.keys()) == 3 and cl.get(FULL_NAME,0) > 0 and cl.get(EMAIL,0) > 0 and cl.get(SIMPLE_NAME,0) > 0:
            is_valid = True
        elif len(cl.keys()) == 2 and cl.get(EMAIL,0) > 0 and cl.get(SIMPLE_NAME,0) > 0:
            is_valid = True
        elif cl.get(PREFIX_NAME,0) > 0:
            is_valid = True
        elif cl.get(SIMPLE_NAME,0) > 0 and cl.get(FULL_NAME,0) > 0 \
            and cl.get(SIMPLE_EMAIL_PREFIX,0) > 0 and cl.get(EMAIL,0) > 0:
            is_valid = True
        elif cl.get(SIMPLE_NAME,0) > 0:
            is_valid = True
        elif cl.get(NAME_PARTS,0) >= (len(members)-1):
            is_valid = True
        else:
            # is_valid = True
            # continue
            # Split by email address if at least 2 share one
            if cl.get(EMAIL,0):
                ce = [e for e,c in Counter([m.email for m in members]).items() if c > 1]
                for e in ce:
                    extra_members = [m for m in members if m.email==e]
                    extra_real = [m for m in extra_members if m.record_type==USR_REAL]

                    if len(extra_real):
                        rep = sorted(extra_real, key=lambda m:int(m.uid))[0]
                    else:
                        rep = sorted(extra_members, key=lambda m:int(m.uid))[0]

                    for a in extra_members:
                        if a.uid != rep.uid:
                            unmask[a.uid] = rep.uid

            if print_flag:
                print (str(cl.items()))
                for m in members:
                    print ([m.uid, m.name, m.email])
        

        if is_valid:
            # Determine group representative
            if len(real):
                rep = sorted(real, key=lambda m:int(m.uid))[0]
            else:
                rep = sorted(members, key=lambda m:int(m.uid))[0]

            for a in members:
                if a.uid != rep.uid:
                    unmask[a.uid] = rep.uid
                    if print_flag:
                        print ('Mapped:' + str((a.uid, rep.uid)))

    return unmask

