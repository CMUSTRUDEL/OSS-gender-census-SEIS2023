'''
Find core contributor for each project in each window
'''
import pandas as pd
from multiprocessing import Pool
import os
import pickle
from os import mkdir
from os.path import isdir

num_proc = 30
proj_lst_path = "../data/census/proj_lists_final/"
repos_path = "../data/census/commits_merge/"
# 1->female -1->male 0->unknown 0.5->likely female -0.5->likely male
output_core = "../data/census/dict_contrib/" # for each lang, each pid, {win:{uid:[isCore, gender]}}
output_commit = "../data/census/dict_commit/" # for each lang, each pid, {win:{uid:[#commits, gender]}}
output_count = "../data/census/female_count/"
if not isdir(output_count):
    mkdir(output_count)
if not isdir(output_core):
    mkdir(output_core)
if not isdir(output_commit):
    mkdir(output_commit)

num_proc = 30
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Shell", "Jupyter", "Objective-C"]

def find_core(proj):
    pid = proj[0]
    lang = proj[1]

    commit_dict = {} # {win:{uid:[#commits, gender]}}
    core_dict = {} # {win:{uid:[isCore, gender]}}
    user_dict = {} # {uid:gender}
    
    try:
        dat = pd.read_csv(repos_path+lang+"/"+pid+".csv", error_bad_lines=False, warn_bad_lines=False, index_col=False)
        dat = dat[dat['bot']==0]
    except:
        return

    for i, row in dat.iterrows():
        try:
            uid = int(row['census_id'])
            win = int(row['win'])

            if not uid: # make sure we don't have uid = 0
                continue

            if win not in commit_dict:
                commit_dict.update({win:{}})
            
            if uid not in user_dict:
                confidence = row['confidence']
                if confidence < 0.63:
                    confidence = 0
                elif confidence < 0.8:
                    confidence = 0.5
                else:
                    confidence = 1
                gender = int(row['gender']) * confidence
                user_dict.update({uid:gender})

            if uid not in commit_dict[win]:
                commit_dict[win].update({uid:[0, user_dict[uid]]})
            
            commit_dict[win][uid][0] += 1
            #commit_dict[win].update({uid:[commit_dict[win].get(uid)+1]})
        except:
            continue

    for win in commit_dict:
        if win not in core_dict:
            core_dict.update({win:{}})
        win_dict = commit_dict[win]
        total = 0
        for uid in win_dict:
            total += win_dict[uid][0]

        for uid in win_dict:
            percentage = win_dict[uid][0] / total
            if percentage >= 0.10:
                core_dict.get(win).update({uid:[1, user_dict[uid]]})
            else:
                core_dict.get(win).update({uid:[0, user_dict[uid]]})
    
    pickle.dump(core_dict, open(output_core+lang+"/"+pid, "wb"))
    pickle.dump(commit_dict, open(output_commit+lang+"/"+pid, "wb"))
    
    female_count = 0
    for uid in user_dict:
        if user_dict[uid] == 1:
            female_count += 1
    
    return [pid, female_count]


def process_all(lang):
    
    if not isdir(output_core+lang+"/"):
        os.mkdir(output_core+lang+"/")
    
    if not isdir(output_commit+lang+"/"):
        os.mkdir(output_commit+lang+"/")

    proj_list = open(proj_lst_path+lang+".list")
    proj_repos = [[proj_repo.strip(), lang] for proj_repo in proj_list.readlines()]
    proj_list.close()
    print('Processing language: ', lang)

    p = Pool(num_proc)
    female_counts = [count for count in p.map(find_core, proj_repos) if count is not None]
    p.close()
    p.join()

    female_counts = pd.DataFrame(female_counts, columns = ["pid", "female_count"])
    female_counts = female_counts.nlargest(100, 'female_count')
    female_counts.to_csv(output_count + lang + ".csv", index=False, encoding="utf-8")


for lang in langs:
  process_all(lang)

print('finish')