"""
Check the completion of namsor geo table by account create time.
"""
#import logging
import numpy as np
import math
import os
import pandas as pd
from multiprocessing import Pool
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os
from sqlalchemy import func
print('Libraries imported...')

# Setup parameters
export_dir = "../data/census/merge_bv/"
pool_size_num = 30
pool_recycle_time = 3 * 60 * 60
username = "zihe"
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"
large_batch_size = 500000
small_batch_size = 5000
max_id = 68024322
print('Set up params...')

# Create engine and session
engine = create_engine(url, pool_recycle = pool_recycle_time)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()
print('Engine and session created...')

# Load tables
projects = Table("projects", metadata, autoload=True)
commits = Table("commits", metadata, autoload=True)
users = Table("users", metadata, autoload=True)
users_private = Table("users_private", metadata, autoload=True)
print('Tables loaded')

# Create second engine and session and load table
url2 = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/zihe?charset=utf8"
print('Set up params...')
engine2 = create_engine(url2, pool_recycle = pool_recycle_time)
metadata2 = MetaData(bind=engine2)
DbSession2 = sessionmaker(bind=engine2)
session2 = DbSession2()
print('Second engine and session created...')
bv_names = Table("bv_names", metadata2, autoload=True)
bv_namsor = Table("bv_namsor", metadata2, autoload=True)
connection2 = engine2.connect()
print('Second table loaded and engine connected...')

# Build connection
connection = engine.connect()
print('Engine connected...')

def cal_win(year, month):
  return int(math.floor((month-1)/3+1) + (year-2008)*4)

def fix_name_prefix(name):
  try:
    name = name.strip()
    name = name.replace("\\", "")
    name = name.replace("  ", " ")
    if name[:2].lower == "a ":
      name = name[2:].strip()
      return fix_name_prefix(name)
    if (name[:3].lower() == "mr." or name[:3].lower() == "mr "or 
      name[:3].lower() == "ms." or name[:3].lower() == "ms " or 
      name[:3].lower() == "dr." or name[:3].lower() == "dr " or
      name[:3].lower() == "md." or name[:3].lower() == "md "):
      name = name[3:].strip()
      return fix_name_prefix(name)
    if name[:4].lower == "miss" or name[:4].lower() == "mrs." or name[:4].lower() == "the " or name[:4].lower() == "mrs ":
      name = name[4:].strip()
      return fix_name_prefix(name)
    if name[-2:] == " -":
      name = name[:-2].strip()
      return fix_name_prefix(name)
    if "," in name:
      reverse_name = name.split(",")
      if len(reverse_name) > 2:
        return
      name = reverse_name[1].strip() + " " + reverse_name[0].strip()
      return fix_name_prefix(name)

    name_parts = name.strip().split(" ")
    if len(name_parts) < 2 or len(name_parts) > 4:
      return
    last_name = ""
    for part in name_parts[1:]:
      last_name += " " + part
    
    if len(name_parts[0]) == 1 or (len(name_parts[0]) == 2 and name_parts[0][:-1] == "."):
      return

    # name, first, last, name parts
    return [name, name_parts[0], last_name.strip(), len(name_parts)]
  except:
    return

# Get the github id of a user using the namsor name_id
def get_git_id(uid):
    user = session.query(users).filter(users.c.id == uid).first()
    
    # Not user account in users
    if not user or user.type != 'USR':
        return None
    login = user.login
    
    try:
      win = cal_win(user.created_at.year, user.created_at.month)
    except:
      win = 0

    # If cannot get valid name, no way to find gender. Exclude.
    name = session.query(users_private).filter(users_private.c.login == func.binary(login)).first()
    if not name or not name.name:
        return None

    name_result = fix_name_prefix(name.name)
    if name_result is None:
        return None

    # If cannot get valid name in bv_names, label it
    bv_name_id = session2.query(bv_names).filter(bv_names.c.name == name_result[0]).first()
    if not bv_name_id:
        return

    bv_name_id = bv_name_id.id

    bv_id = session2.query(bv_namsor).filter(bv_namsor.c.name_id == bv_name_id).first()
    if not bv_id:
        return
     
    gender = 1 if bv_id.likely_gender == "female" else -1
    # uid, namsor_id, name, first, last, parts gender, login, create_window, probability
    return [uid, bv_name_id, name_result[0], gender, login, win, bv_id.probability_calibrated, name_result[1], name_result[2], name_result[3]]


# Process user data in parallel. Every $large_batch_size id is a large batch,
# every $small_batch_size ids in which is a small batch. 
# Small batches are processed in parallel, large are sequential
def process_large_batch(start_id):
    end_id = min(start_id + large_batch_size, max_id)
    file_number = int(end_id / large_batch_size) - 1
    print("Processing Batch {}. Processed bv_names id from {} to {}".format(
        file_number, start_id, end_id-1))
    pool = Pool(pool_size_num)

    git_ids = [id for id in pool.map(
        func=get_git_id, 
        iterable=list(range(start_id, end_id)), 
        chunksize=small_batch_size
        ) if id is not None]
    pool.close()
    pool.join()
   
    # Export results
    file_name = str(file_number) + '.csv'
    git_ids = pd.DataFrame(git_ids, 
                columns = ["uid", "namsor_id", "name", "gender", "login", "create_window", "probability", "first_name", "last_name", "name_parts"])
    git_ids.to_csv(export_dir+file_name, index = False, encoding = "utf-8")

    os.system("mysql -uzihe -p"+ os.environ["SQLPW"] +" --local-infile zihe -e \"LOAD DATA LOCAL INFILE '"+export_dir+file_name+"'  INTO TABLE namsor_gender_table FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' ignore 1 lines\"")

    return end_id

# Chunk large batch
large_batch_start_id = 1
while large_batch_start_id < max_id:
    large_batch_start_id = process_large_batch(large_batch_start_id)

print("finish")