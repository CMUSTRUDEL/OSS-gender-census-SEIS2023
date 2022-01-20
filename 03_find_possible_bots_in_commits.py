'''
find the people who made the most commits/comments in a window
'''
import time
from multiprocessing import Pool
import os
from os import path, mkdir
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from sqlalchemy import func
import math

num_proc = 30
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://zihe:" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"

# Create engine and session
engine = create_engine(url, pool_recycle = 60 * 60)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()
users_private = Table("users_private", metadata, autoload=True)
print('Tables loaded and connection built')

commit_path = "../data/census/commits_complete/"
output_path = "../data/census/bot_candidates/"
proj_path = "../data/census/proj_lists_final/"
langs = ["Objective-C", "JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell"]
if not path.isdir(output_path):
    mkdir(output_path)

def cal_win(year, month):
  return int(math.floor((month-1)/3+1) + (year-2008)*4)
max_win = cal_win(2019, 1)

def find_top_contr(repos):
    try: 
        records_pd = pd.read_csv(commit_path+repos[1]+"/"+repos[0]+".csv")
        records_pd = records_pd.loc[records_pd["win"] <= max_win]
        total_commits = len(records_pd)
        contr_commits = records_pd.groupby(["login"]).count().reset_index()
        contr_commits["commit_percentage"] = contr_commits["sha"] / total_commits
        contr_commits = contr_commits.rename(columns={"sha": "count"})
        return contr_commits[["login", "count"]]
    except:
        return

def process_all(lang):
    proj_list = open(proj_path+lang+".list")
    repos = [[proj_repo.strip(), lang] for proj_repo in proj_list.readlines()]
    proj_list.close()
    print('Processing language: ', lang)
    p = Pool(num_proc)
    
    core_dict = [commits for commits in p.map(find_top_contr, repos) if commits is not None]
    core_dict = pd.concat(core_dict)
    core_dict = core_dict.groupby(["login"]).sum().reset_index()
    core_dict = core_dict.sort_values(by=["count"])
    core_dict = core_dict.loc[core_dict["count"] >= 1000]

    
    # get their names
    count = 10000
    for i, row in core_dict.iterrows():
        count -= 1
        if count == 0:
            count = 10000
            time.sleep(0.50)
        author = row["login"]
        try:
            user = session.query(users_private).filter(users_private.c.login == func.binary(author)).first()
            name = user.name
            email = user.email
        except:
            name = ""
            email = ""
                
        core_dict.loc[i, "name"] = name
        core_dict.loc[i, "email"] = email

    core_dict.to_csv(output_path+lang+".csv", index=False) 
    # then manual inspection

for lang in langs:
  process_all(lang)
