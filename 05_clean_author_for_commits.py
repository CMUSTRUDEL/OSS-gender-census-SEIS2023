'''
Get the author info of each commit.
Merge aliases and identify bots. Gets bv_id and gender.
'''
import math
import pandas as pd
from multiprocessing import Pool
import os
from os import path
from os import mkdir
from os.path import isdir
import pickle
import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
print('Libraries imported...')

# Setup parameters
num_proc = 30
print('Set up params...')

# Specify paths
logging.basicConfig(filename="../data/census/05.log", level=logging.WARNING)
logger=logging.getLogger()
alias_path = "../data/census/alias_dicts/"
repo_path = "../data/census/commits_complete/"
output_path = "../data/census/commits_merge/"
bot_path = "../data/census/bot_names.list"
proj_path = "../data/census/proj_lists/"
log_path = "../data/census/large_proj.log"

langs = ["NPM", "Packagist", "Go", "Pypi", "Rubygems", "NuGet", "Maven", 
          "Bower", "CocoaPods", "Cargo", "Clojars", "Atom", "CPAN", "Meteor", "Hackage",
          "Hex", "Pub", "CRAN", "Puppet", "PlatformIO"]
          
# Create engine and session and table
pool_recycle_time = 10 * 60
username = "zihe"
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/zihe?charset=utf8"
engine = create_engine(url, pool_recycle = pool_recycle_time)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()
namsor = Table("namsor_gender_table", metadata, autoload=True)
connnection = engine.connect()

url2 = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"
engine2 = create_engine(url2, pool_recycle = pool_recycle_time)
metadata2 = MetaData(bind=engine2)
DbSession2 = sessionmaker(bind=engine2)
session2 = DbSession2()
users = Table("users", metadata2, autoload=True)
connnection2 = engine2.connect()

if not isdir(output_path):
    mkdir(output_path)

# Get bot list
f = open(bot_path)
bot_names = [l.strip() for l in f.readlines()]
bots = set()
for bot in bot_names:
    bots.add(bot)
f.close()

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)

def process_proj(proj):
    pid = proj[0]
    lang = proj[1]
    
    out_path = output_path+lang+"/"+pid+".csv"
    #if path.isfile(out_path):
        #return None
    
    try:
        dat = pd.read_csv(repo_path+lang+"/"+pid+".csv", error_bad_lines=False, warn_bad_lines=False, index_col=False)
        dat["bot"] = 0
        dat["census_id"] = 0
        dat["confidence"] = 0
        dat["gender"] = 0
        dat["create_win"] = -1
        dat = dat.loc[dat["sha"]!=""]
        if dat.shape[0] > 80000:
            open(log_path, "a+").write("{} {} {}\n".format(lang, pid, dat.shape[0]))
            return
    except:
        return

    logger.warning(lang + " " + pid)
    
    # Check bot
    contrib_dict = {} # {uid:[isBot, census_id]}
    for i, row in dat.iterrows():
        try:
            uid = int(row['uid'])
            login = row['login']
            if not uid in contrib_dict:
                contrib_dict.update({uid:[int(login in bot_names), uid]})
        except:
            continue
    
    # Merge alias
    if path.isfile(alias_path+lang+"/"+pid): # if there are alias to be merged in the project

        try:
            d = pickle.load(open(alias_path+lang+"/"+pid, "rb"))
        except:
            d = {}
        
        for this_id in d.keys():
            try:
                match_id = d[this_id]
                if match_id == this_id:
                    continue

                # MERGING BEGINS
                # If either is bot, make both bots. Else, compare probability
                if contrib_dict[this_id][0]:
                    contrib_dict[match_id] = contrib_dict[this_id]
                    continue
                if contrib_dict[match_id][0]:
                    contrib_dict[this_id] = contrib_dict[match_id]
                    continue

                contrib_dict[this_id] = contrib_dict[match_id]
            except:
                continue

    for i, row in dat.iterrows():
        try:
            uid = int(row['uid'])
            contrib_info = contrib_dict.get(uid)
            dat.iloc[i, dat.columns.get_loc("bot")] = contrib_info[0]
            dat.iloc[i, dat.columns.get_loc("census_id")] = contrib_info[1]
        except:
            continue

    if len(dat["census_id"].unique()) <= 3:
        return

    gender_dict = {} # {uid: [gender, confidence]}
    for i, row in dat.iterrows():
        uid = int(row['census_id'])
        if uid not in gender_dict:
            try:
                gender = session.query(namsor).filter(namsor.c.uid == uid).first()
                if gender is not None:
                    gender_dict.update({uid:[gender.gender, gender.probability, gender.create_window]})
                else:
                    user = session.query(users).filter(users.c.id == uid).first()
                    gender_dict.update({uid:[0, 0, cal_win(user.created_at)]})
            except:
                gender_dict.update({uid:[0, 0, -1]})
        dat.iloc[i, dat.columns.get_loc("gender")] = gender_dict[uid][0]
        dat.iloc[i, dat.columns.get_loc("confidence")] = gender_dict[uid][1]
        dat.iloc[i, dat.columns.get_loc("create_win")] = gender_dict[uid][2]
    
    dat_df = pd.DataFrame(dat)
    dat_df.to_csv(out_path, index=False, encoding="utf-8")

def process_all(lang):
    out_dir = output_path+lang+"/"
    if not isdir(out_dir):
        mkdir(out_dir)
    
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