'''
Get rid of projs with no commit
'''
import os
from os import path
from os.path import isdir
from multiprocessing import Pool

all_dir = '../data/census/'
list_dir = '../data/census/proj_lists_clean/'
clean_list_dir = '../data/census/proj_lists_final/'
commit_dir = '../data/census/commits_merge/'
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
proc_num = 16

if not isdir(clean_list_dir):
    os.mkdir(clean_list_dir)

# Get clean list
def check_repo_valid(proj_repo):
    proj_id = proj_repo[0]
    if path.isfile(commit_dir+proj_repo[1]+"/"+proj_id+".csv"):
        return proj_id
    return None


def clean_list(lang):
    print("Processing list: ", lang)
    export_dir = clean_list_dir+lang+".list"
    if path.isfile(export_dir):
        return

    # Get clean list
    proj_list = open(list_dir+lang+".list")
    proj_repos = [[proj_repo.strip(),lang] for proj_repo in proj_list.readlines()]
    proj_list.close()

    pool = Pool(proc_num)
    valid_repos= [id for id in pool.map(check_repo_valid, proj_repos) if id is not None]
    pool.close()
    pool.join()

    open(export_dir, "w+").write("\n".join(item for item in valid_repos))

for lang in langs:
    clean_list(lang)