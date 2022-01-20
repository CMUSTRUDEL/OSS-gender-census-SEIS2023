'''
Change commit by window dictionary to csv
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

num_proc = 16
proj_lst_path = "../data/census/proj_lists_final/"
commit_path = "../data/census/dict_commit/" # for each lang, each pid, {win:{uid:commits}}
output_path = "../data/census/final_gender_commit/"
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
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
end_window = cal_win(2019, 6)
start_window = cal_win(2008, 1)


def commit_census(lang):
    print("Processing "+lang)

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()

    commit_dict = {} # {win:[female_commit, male_commit, all_commit]}
    log = open(output_path + lang +".log", "w+")
    for pid in projs:
        log.write(str(pid)+"\n")
        uid_gender = {} # {uid:gender}
        try:
            commits = pickle.load(open(commit_path+lang+"/"+pid, "rb"))
            for win in commits:
                uid_dict = commits[win] # {uid:commits}
                if win not in commit_dict:
                    commit_dict.update({win:[0,0,0]})

                for uid in uid_dict:
                    if uid not in uid_gender:
                        gender = session.query(namsor).filter(namsor.c.uid == uid).first()
                        if gender is None:
                            uid_gender.update({uid:0})
                        elif gender.probability >= 0.8:
                            uid_gender.update({uid:gender.gender})
                        else:
                            uid_gender.update({uid:0})
                    gender = uid_gender[uid]
                    commit_dict[win][2] += uid_dict[uid]
                    if gender == 1:
                        commit_dict[win][0] += uid_dict[uid]
                    elif gender == -1:
                        commit_dict[win][1] += uid_dict[uid]
        except:
            continue
    log.close()
    print(lang+" finish creating dict")

    dat = []
    for i in range(start_window,end_window+1):
        # win, female_commit, male_commit, all_commit
        if i not in commit_dict:
            dat.append([i, 0, 0, 0])
        else:
            dat.append([i, commit_dict[i][0], commit_dict[i][1], commit_dict[i][2]]) 
    print(lang+" finish finding gender")
    pickle.dump(commit_dict, open(output_path+lang, "wb"))

    dat = pd.DataFrame(dat, 
            columns = ["win", "female_commit", "male_commit", "all_commit"])
    dat.to_csv(output_path+lang+".csv", index = False, encoding = "utf-8")

p = Pool(num_proc)
p.map(commit_census, langs)
p.close()
p.join()

all_dict = {} # {win : [f_commits, m_commits, all_commits]}
for win in range(start_window,end_window+1): 
    all_dict.update({win:[0,0,0]})

for lang in langs:
    read_dict = pickle.load(open(output_path+lang, "rb"))
    for win in range(start_window,end_window+1):
        try:
            all_dict[win][0] += read_dict[win][0]
            all_dict[win][1] += read_dict[win][1]
            all_dict[win][2] += read_dict[win][2]
        except:
            print(lang)
            print(win)
print("All finish creating dict")

dat = []
for i in range(start_window,end_window+1):
    dat.append([i, all_dict[i][0], all_dict[i][1], all_dict[i][2]])

dat = pd.DataFrame(dat, 
        columns = ["win", "female_commit", "male_commit", "all_commit"])
dat.to_csv(output_path+"All.csv", index = False, encoding = "utf-8")
print("finish")