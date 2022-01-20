'''
Use the list to find all commits to the project id.
Stores sha, uid, window from table commits.
Also leaves room for bvid, gender, and login for next script.
'''
import os
import pandas as pd
from multiprocessing import Pool
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os
from os import path, mkdir
import math
print('Libraries imported...')

# Setup parameters
num_proc = 30
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
commits = Table("commits", metadata, autoload=True)
users = Table("users", metadata, autoload=True)
users_private = Table("users_private", metadata, autoload=True)
print('Tables loaded')

# Build connection
connnection = engine.connect()
print('Engine connected and session created...')

langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
proj_path = "../data/census/proj_lists_raw/"
output_path = "../data/census/commits_complete/"

if not path.isdir(output_path):
    mkdir(output_path)

def cal_win(year, month):
  return int(math.floor((month-1)/3+1) + (year-2008)*4)
max_win = cal_win(2021, 12)
min_win = cal_win(2008, 1)

def handle_commits(all_commits): # Helper for get_commits
    result = []
    uid_dict = {}

    for a_commit in all_commits:
        try:
            win = cal_win(a_commit.created_at.year, a_commit.created_at.month)
            if win > max_win or win < min_win:
                continue

            uid = a_commit.author_id
            if uid_dict.get(uid) == -1:
                continue

            if not uid in uid_dict:
                try:
                    user = session.query(users).filter(users.c.id == uid).first()
                    if not user:
                        uid_dict.update({uid:["", "", "", 1]})
                    if user.type != 'USR':
                        raise Exception()
                    else:
                        login = user.login
                        fake = user.fake
                        info = session.query(users_private).filter(users_private.c.login == login).first()
                        email = info.email if info.email is not None else ""
                        name = info.name if info.name is not None else ""
                        uid_dict.update({uid:[login, email, name, fake]})
                except:
                    uid_dict.update({uid:-1})
                    continue
            
            # sha, win, uid, login, email, name, fake
            result.append([a_commit.sha, win, uid, 
                            uid_dict.get(uid)[0], uid_dict.get(uid)[1], 
                            uid_dict.get(uid)[2], uid_dict.get(uid)[3]])
        except:
            continue
    
    return result

def get_commit(proj):
    pid = proj[0]
    lang = proj[1]
    out_path = output_path+lang+"/"+pid+".csv"

    if path.isfile(out_path):
        return None

    result = []

    forkeds = session.query(projects).filter(projects.c.forked_from == int(pid))
    for forked in forkeds:
        first_commits = session.query(commits).filter(commits.c.project_id == forked.id)
        result.extend(handle_commits(first_commits))
    
    all_commits = session.query(commits).filter(commits.c.project_id == int(pid))
    result.extend(handle_commits(all_commits))

    result = pd.DataFrame(result, 
            columns = ["sha", "win", "uid", "login", "email", "name", "fake"])
    result.to_csv(out_path, index = False, encoding = "utf-8")


def process_all(lang):
    print('Processing language: ', lang)
    if not path.isdir(output_path+lang):
        os.mkdir(output_path+lang)

    proj_list = open(proj_path+lang+".list")
    proj_repos = [[proj_repo.strip(), lang] for proj_repo in proj_list.readlines()]
    proj_list.close()
    
    p = Pool(num_proc)
    p.map(get_commit, proj_repos)
    p.close()
    p.join()


for lang in langs:
    process_all(lang)

print('finish')
