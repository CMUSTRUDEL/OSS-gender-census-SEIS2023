'''
Change contributor by window dictionary to csv
'''
import pandas as pd
import os
import math
import pickle
from os.path import isdir
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData

num_proc = 20
proj_lst_path = "../data/census/proj_lists/"
core_path = "../data/census/dict_commit/"
output_path = "../data/census/final_contrib_info/"
langs = ["NPM", "Packagist", "Go", "Pypi", "Rubygems", "NuGet", "Maven", 
          "Bower", "CocoaPods", "Cargo", "Clojars", "Atom", "CPAN", "Meteor", "Hackage",
          "Hex", "Pub", "CRAN", "Puppet", "PlatformIO"]

if not isdir(output_path):
    os.mkdir(output_path)

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2021, 12)
start_window = cal_win(2008, 1)

pool_recycle_time = 60 * 60
username = "zihe"
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"
print('Set up params...')

# Create engine and session
engine = create_engine(url, pool_recycle = pool_recycle_time)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()

# Load tables
projects = Table("projects", metadata, autoload=True)
users = Table("users", metadata, autoload=True)
print('Tables loaded')

def contributor(lang):
    print("Processing "+lang)

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()

    user_dict = {} # {uid : [{win:[#commit, #proj]}, gender, first_win, last_win, create_win, is_project_owner]}

    for pid in projs:
        try:
            read_dict = pickle.load(open(core_path+lang+"/"+pid, "rb")) # for each lang, each pid, {win:{uid:[#commits, gender]}}
            owner = session.query(projects).filter(projects.c.id == int(pid)).first().owner_id
        except:
            continue
        
        try:
            for win in read_dict:
                uid_dict = read_dict[win]

                for uid in uid_dict:
                    if uid_dict[uid][1] == 0:
                        continue
                    if uid not in user_dict:
                        create = session.query(users).filter(users.c.id == int(uid)).first().created_at
                        create = cal_win(create.year, create.month)
                        user_dict.update({uid:[{}, uid_dict[uid][1], 60, -1, create, 0]})
                    if uid == owner:
                        user_dict[uid][5] = 1
                    if win < user_dict[uid][2]:
                        user_dict[uid][2] = win
                    if win > user_dict[uid][3]:
                        user_dict[uid][3] = win
                    if win not in user_dict[uid][0]:
                        user_dict[uid][0].update({win:[0, 0]})
                    user_dict[uid][0][win][0] += uid_dict[uid][0]
                    user_dict[uid][0][win][1] += 1
        except:
            print(lang, pid)

    dat = []
    for uid in user_dict:
        for win in user_dict[uid][0]:
            dat.append([uid, win, user_dict[uid][0][win][0], user_dict[uid][0][win][1], user_dict[uid][1], user_dict[uid][2], user_dict[uid][3], user_dict[uid][4], user_dict[uid][5]]) 

    dat = pd.DataFrame(dat, 
            columns = ["uid", "win", "commits", "projects", "gender", "first_commit", "last_commit", "create_at", "proj_owner"])
    dat.to_csv(output_path+lang+".csv", index = False, encoding = "utf-8")

for lang in langs:
    contributor(lang)