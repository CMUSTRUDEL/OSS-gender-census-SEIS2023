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

num_proc = 16
proj_lst_path = "../data/census/proj_lists_final/"
core_path = "../data/census/dict_contrib_10/" # for each lang, each pid, {win:{uid:isCore}}
output_path = "../data/census/final_most_diver_owner/"
user_path = "../data/census/final_gender_contrib/" # {win : dict(all_uid:gender)}
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]

if not isdir(output_path):
    os.mkdir(output_path)

# Create engine and session and load table
pool_recycle_time = 3 * 60 * 60
username = "zihe"
pwd = os.environ["SQLPW"]

url2 = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"
engine2 = create_engine(url2, pool_recycle = pool_recycle_time)
metadata2 = MetaData(bind=engine2)
DbSession2 = sessionmaker(bind=engine2)
session2 = DbSession2()
projects = Table("projects", metadata2, autoload=True)
connnection2 = engine2.connect()
print('Engine connected and session created...')

if not isdir(output_path):
    os.mkdir(output_path)

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2019, 6)
start_window = cal_win(2008, 1)


def contributor_census(lang):
    print("Processing "+lang)

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()

    female_count = []
    users = pickle.load(open(user_path+lang+"_all", "rb"))
    for pid in projs:
        try:
            read_dict = pickle.load(open(core_path+lang+"/"+pid, "rb"))
            uid_set = set()
            count = 0
            for win in read_dict:
                for uid in read_dict[win]:
                    if uid not in uid_set:
                        if users[win][uid] == 1:
                            count += 1
                        uid_set.add(uid)
            female_count.append([pid, count])
        except:
            continue
 
    female_count = pd.DataFrame(female_count, columns = ["pid", "female_count"])
    female_count = female_count.astype(int).nlargest(50, 'female_count')

    output = []

    for i, row in female_count.iterrows():
        try:
            pid = int(row["pid"])
            count = int(row["female_count"])
            owner = session2.query(projects).filter(projects.c.id == pid).first()
            output.append([pid, owner.owner_id, count, owner.name, owner.url])
        except:
            print(a)
            continue

    output = pd.DataFrame(output, columns = ["pid", "owner", "count", "name", "url"])
    output.to_csv(output_path+lang+".csv", index = False, encoding = "utf-8")

p = Pool(num_proc)
p.map(contributor_census, langs)
p.close()
p.join()