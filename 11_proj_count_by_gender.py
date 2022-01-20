'''
Change commit by window dictionary to csv
'''
import pandas as pd
from multiprocessing import Pool
import os
import math
import pickle
from os.path import isdir

num_proc = 16
proj_lst_path = "../data/census/proj_lists_final/"
commit_path = "../data/census/dict_commit/" # for each lang, each pid, {win:{uid:commits}}
user_path = "../data/census/final_gender_contrib/" # {win : dict(all_uid:gender)}
output_path = "../data/census/final_proj_by_win/"
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
if not isdir(output_path):
    os.mkdir(output_path)

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2019, 6)
start_window = cal_win(2008, 1)

def active_proj(lang):
    print("Processing "+lang)

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()
    users = pickle.load(open(user_path+lang+"_all", "rb"))

    proj_dict = {} # {win:proj_num}
    for win in range(start_window,end_window+1): 
        proj_dict.update({win:[0,0]})
    
    for pid in projs:
        try:
            commits = pickle.load(open(commit_path+lang+"/"+pid, "rb"))
            for win in commits:
                proj_dict[win][0] += 1
                for uid in commits[win]:
                    if users[win][uid] == 1:
                        proj_dict[win][1] += 1
        except:
            continue
    print(lang+" finish creating dict")

    return [lang, proj_dict]

p = Pool(num_proc)
dicts = p.map(active_proj, langs)
p.close()
p.join()

all_dict = {} # {win:{lang:proj_num}}
for win in range(start_window,end_window+1): 
    all_dict.update({win:{"All":[0,0]}})

for adict in dicts:
    for win in range(start_window,end_window+1): 
        all_dict[win]["All"][0] += adict[1][win][0]
        all_dict[win]["All"][1] += adict[1][win][1]
        all_dict[win].update({adict[0]:adict[1][win]})
print("All finish creating dict")

dat = []
for i in range(start_window,end_window+1):
    result = [i, all_dict[i]["All"][0], all_dict[i]["All"][1]]
    for lang in langs:
        result.append(all_dict[i][lang][0])
        result.append(all_dict[i][lang][1])
    dat.append(result)
cols = ["win", "All_all", "All_fem"]
for lang in langs:
    cols.append(lang+"_all")
    cols.append(lang+"_fem")

dat = pd.DataFrame(dat, columns = cols)
dat.to_csv(output_path+"full.csv", index = False, encoding = "utf-8")
print("finish")