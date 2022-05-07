'''
Change contributor by window dictionary to csv
'''
import pandas as pd
from multiprocessing import Pool
import os
import math
import pickle
from os.path import isdir
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData

num_proc = 20
proj_lst_path = "../data/census/proj_lists/"
core_path = "../data/census/dict_contrib/" # for each lang, each pid, {win:{uid:[isCore, gender]}}
output_path = "../data/census/final_gender_contrib/"
langs = ["NPM", "Packagist", "Go", "Pypi", "Rubygems", "NuGet", "Maven", 
          "Bower", "CocoaPods", "Cargo", "Clojars", "Atom", "CPAN", "Meteor", "Hackage",
          "Hex", "Pub", "CRAN", "Puppet", "PlatformIO"]
          
if not isdir(output_path):
    os.mkdir(output_path)

# Create engine and session and load table
pool_recycle_time = 3 * 60 * 60
username = "zihe"
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/zihe?charset=utf8"
print('Set up params...')
engine = create_engine(url, pool_recycle = pool_recycle_time)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()
print('Engine and session created...')
namsor = Table("namsor_gender_table", metadata, autoload=True)
connection = engine.connect()
print('Table loaded and engine connected...')

if not isdir(output_path):
    os.mkdir(output_path)

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2021, 12)
start_window = cal_win(2008, 1)


def contributor_census(lang):
    print("Processing "+lang)

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()

    core_dict = {} # {win : dict(core_uid:gender)}
    all_dict = {} # {win : dict(all_uid:gender)}
    total_proj = 0
    total_contrib_dict = {} #{contrib_count : set(pid)}

    for pid in projs:
        #log.write(str(pid)+"\n")
        try:
            read_dict = pickle.load(open(core_path+lang+"/"+pid, "rb")) # for each lang, each pid, {win:{uid:[isCore, gender]}}
            uid_set = set()
            for win in read_dict:
                uid_dict = read_dict[win]
                if win not in all_dict:
                    all_dict.update({win:{}})

                for uid in uid_dict:
                    uid_set.add(uid)
                    all_dict[win].update({uid:uid_dict[uid][1]})

            if len(uid_set) not in total_contrib_dict:
                total_contrib_dict.update({len(uid_set):set()})
            total_contrib_dict[len(uid_set)].add(pid)
            total_proj += 1
        except:
            continue
    #log.close()

    # Only count core for projects with top 10% contributor numbers
    total_included = 0
    count_lst = list(total_contrib_dict.keys())
    count_lst.sort(reverse=True)

    for count in count_lst:
        pids = total_contrib_dict[count]
        total_included += len(pids)
        for pid in pids:
            try:
                read_dict = pickle.load(open(core_path+lang+"/"+pid, "rb"))
                for win in read_dict:
                    uid_dict = read_dict[win]
                    for uid in uid_dict:                       
                        if uid_dict[uid]: # is core
                            if win not in core_dict:
                                core_dict.update({win:{}})
                            core_dict[win].update({uid:uid_dict[uid][1]})
            except:
                continue
        if total_included >= total_proj * 0.1:
            break


    print(lang+" finish creating dict")

    dat = []
    for i in range(start_window,end_window+1):
        # win, all_contrib, core_contrib
        all_contrib = 0 if i not in all_dict else len(all_dict[i])
        core_contrib = 0 if i not in core_dict else len(core_dict[i])
        male_all = 0
        female_all = 0
        unknown_all = 0
        male_likely_all = 0
        female_likely_all = 0
        if i in all_dict:
            for uid in all_dict[i]:
                gender = all_dict[i][uid]
                if gender == 0:
                    unknown_all += 1
                elif gender == 1:
                    female_all += 1
                elif gender == 0.5:
                    female_likely_all += 1
                elif gender == -1:
                    male_all += 1
                elif gender == -0.5:
                    male_likely_all += 1
        male_core = 0
        female_core = 0
        unknown_core = 0
        female_likely_core = 0
        male_likely_core = 0
        if i in core_dict:
            for uid in core_dict[i]:
                gender = core_dict[i][uid]
                if gender == 0:
                    unknown_core += 1
                elif gender == 1:
                    female_core += 1
                elif gender == 0.5:
                    female_likely_core += 1
                elif gender == -1:
                    male_core += 1
                elif gender == -0.5:
                    male_likely_core += 1
        dat.append([i, male_all, male_likely_all, female_all, female_likely_all, 
            unknown_all, all_contrib, male_core, male_likely_core, female_core, female_likely_core, unknown_core, core_contrib]) 
    
    print(lang+" finish finding gender")
    pickle.dump(all_dict, open(output_path+lang+"_all", "wb"))
    pickle.dump(core_dict, open(output_path+lang+"_core", "wb"))

    dat = pd.DataFrame(dat, 
            columns = ["win", "male_all", "male_likely_all", "female_all", "female_likely_all", 
            "unknown_all", "all_all", "male_core", "male_likely_core", "female_core", "female_likely_core", "unknown_core", "all_core"])
    dat.to_csv(output_path+lang+".csv", index = False, encoding = "utf-8")

p = Pool(num_proc)
p.map(contributor_census, langs)
p.close()
p.join()

all_dict = {}
core_dict = {}
print("Processing all")
for win in range(start_window,end_window+1): 
    all_dict.update({win:{}})
    core_dict.update({win:{}})

for lang in langs:
    core_lang = pickle.load(open(output_path+lang+"_core", "rb"))
    all_lang = pickle.load(open(output_path+lang+"_all", "rb"))
    for win in range(start_window,end_window+1): 
        if win in all_lang:
            all_dict.get(win).update(all_lang.get(win))
        if win in core_lang:
            core_dict.get(win).update(core_lang.get(win))
print("All finish creating dict")

dat = []
for i in range(start_window,end_window+1):
    # win, all_contrib, core_contrib
    all_contrib = 0 if i not in all_dict else len(all_dict[i])
    core_contrib = 0 if i not in core_dict else len(core_dict[i])
    male_all = 0
    male_likely_all = 0
    female_all = 0
    female_likely_all = 0
    unknown_all = 0
    if i in all_dict:
        for uid in all_dict[i]:
            gender = all_dict[i][uid]
            if gender is None or gender == 0:
                unknown_all += 1
            elif gender == 1:
                female_all += 1
                all_dict[i].update({uid:1})
            elif gender == -1:
                male_all += 1
                all_dict[i].update({uid:-1})
            elif gender == 0.5:
                female_likely_all += 1
                all_dict[i].update({uid:0.5})
            elif gender == -0.5:
                male_likely_all += 1
                all_dict[i].update({uid:-0.5})
    male_core = 0
    female_core = 0
    unknown_core = 0
    female_likely_core = 0
    male_likely_core = 0
    if i in core_dict:
        for uid in core_dict[i]:
            gender = core_dict[i][uid]
            if gender == 0:
                unknown_core += 1
            elif gender == 1:
                female_core += 1
                core_dict[i].update({uid:1})
            elif gender == -1:
                male_core += 1
                core_dict[i].update({uid:-1})
            elif gender == -0.5:
                male_likely_core += 1
            elif gender == 0.5:
                female_likely_core += 1
    dat.append([i, male_all, male_likely_all, female_all, female_likely_all, unknown_all, all_contrib, male_core, male_likely_core, female_core, female_likely_core, unknown_core, core_contrib]) 

print("all finish finding gender")
pickle.dump(all_dict, open(output_path+"All_all", "wb"))
pickle.dump(core_dict, open(output_path+"All_core", "wb"))

dat = pd.DataFrame(dat, 
        columns=["win", "male_all", "male_likely_all", "female_all", "female_likely_all", 
            "unknown_all", "all_all", "male_core", "male_likely_core", "female_core", "female_likely_core", "unknown_core", "all_core"])
dat.to_csv(output_path+"All.csv", index = False, encoding = "utf-8")

print("finish")