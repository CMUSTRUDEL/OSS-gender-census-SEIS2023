'''
Filter out projects with more than 1000000 commits and projects with less than 3 contributors after merging.
'''
import pandas as pd
from multiprocessing import Pool
from os import remove
import math
print('Libraries imported...')

# Setup parameters
num_proc = 30
print('Set up params...')

# Specify paths
repo_path = "../data/census/commits_clean/"
log_path = "../data/census/scale.log"
proj_path = "../data/census/proj_lists_raw/"
proj_path = "../data/OSS-census/proj_lists_final/"

langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
        "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2021, 12)
start_window = cal_win(2008, 1)

def process_proj(proj):
    pid = proj[0]
    lang = proj[1]
    file_path = repo_path+lang+"/"+pid+".csv"
    
    try:
        dat = pd.read_csv(file_path, error_bad_lines=False, warn_bad_lines=False, index_col=False)
        dat = dat.loc[dat["bot"] == 0]
    except:
        return
    
    if len(dat["census_id"].unique()) <= 3:
        remove(file_path)
    
    if dat.shape[0] > 1000000:
        open(log_path, "a+").write("{} {} {}\n".format(lang, pid, dat.shape[0]))

def process_all(lang):    
    proj_list = open(proj_path+lang+".list")
    proj_repos = [[proj_repo.strip(), lang] for proj_repo in proj_list.readlines()]
    proj_list.close()
    print('Processing language: ', lang)

    p = Pool(num_proc)
    p.map(process_proj, proj_repos)
    print("Finish language: ", lang)
    p.close()
    p.join()


for lang in langs:
    process_all(lang)

print('finish')