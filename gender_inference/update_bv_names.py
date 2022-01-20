"""
Use "/home/hongbo/wocgender/data/name2gender.json" to complete bv_names and bv_geo_manual
"""
import json
import os
import pandas as pd
import pickle
from multiprocessing import Pool
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import logging

# Setup parameters
export_dir = "../data/OSS-census/"
name_dir = "../data/OSS-census/woc_name.list"
logging.basicConfig(filename=export_dir+"update_name_and_namsor.log", level=logging.WARNING)
logger=logging.getLogger()
num_proc = 30
pool_recycle_time = 3 * 60 * 60
username = "zihe"
pwd = os.environ["SQLPW"]
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/ghtorrent-2019-06?charset=utf8"
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
bv_namsor = Table("bv_namsor_gender_geo_manual_first_last_2_0_10", metadata, autoload=True)
bv_names = Table("bv_names", metadata, autoload=True)
connection = engine.connect()
print('Tables loaded and engine connected...')

large_batch_start_id = 1
large_batch_size = 1000000
small_batch_size = 5000
max_id = 11394083
bv_processed = []

def fix_name_prefix(id, name):
  try:
    name = name.strip()
    name = name.replace("\\", "")
    name = name.replace("  ", " ")
    if name[:2].lower == "a ":
      name = name[2:].strip()
      return fix_name_prefix(id, name)
    if (name[:3].lower() == "mr." or name[:3].lower() == "mr "or 
      name[:3].lower() == "ms." or name[:3].lower() == "ms " or 
      name[:3].lower() == "dr." or name[:3].lower() == "dr " or
      name[:3].lower() == "md." or name[:3].lower() == "md "):
      name = name[3:].strip()
      return fix_name_prefix(id, name)
    if name[:4].lower == "miss" or name[:4].lower() == "mrs." or name[:4].lower() == "the " or name[:4].lower() == "mrs ":
      name = name[4:].strip()
      return fix_name_prefix(id, name)
    if name[-2:] == " -":
      name = name[:-2].strip()
      return fix_name_prefix(id, name)
    if "," in name:
      reverse_name = name.split(",")
      if len(reverse_name) > 2:
        return
      name = reverse_name[1].strip() + " " + reverse_name[0].strip()
      return fix_name_prefix(id, name)

    name_parts = name.strip().split(" ")
    if len(name_parts) < 2 or len(name_parts) > 4:
      return
    last_name = ""
    for part in name_parts[1:]:
      last_name += " " + part
    
    if len(name_parts[0]) == 1 or (len(name_parts[0]) == 2 and name_parts[0][:-1] == "."):
      return

    # id, name, first, last, name parts
    return [id, name, name_parts[0], last_name.strip(), len(name_parts)]
  except:
    return

# Clean invalid bv names and process names
def check_bv(id):
  name_entry = session.query(bv_names).filter(bv_names.c.id == id).first()
  if name_entry is None:
    return
  return fix_name_prefix(id, name_entry.name)

def process_large_batch(start_id):
  end_id = min(start_id + large_batch_size, max_id)
  batch_number = int(end_id / large_batch_size) - 1
  print("Processing Batch {}. Processed bv_names id from {} to {}".format(
      batch_number, start_id, end_id-1))
  pool = Pool(num_proc)

  valid_bvs = [id for id in pool.map(
      func=check_bv, 
      iterable=list(range(start_id, end_id)), 
      chunksize=small_batch_size
      ) if id is not None]
  pool.close()
  pool.join()

  bv_processed.extend(valid_bvs)
  # Export backup results
  valid_bvs = pd.DataFrame(valid_bvs, columns = ["id", "name", "first_name", "last_name", "num_parts"])
  valid_bvs.to_csv(export_dir+"bv_processed/"+str(batch_number) + '.csv', index = False, encoding = "utf-8")
  return end_id

# Chunk large batch
while large_batch_start_id < max_id:
  large_batch_start_id = process_large_batch(large_batch_start_id)
# Export results
bv_processed = pd.DataFrame(bv_processed, columns = ["id", "name", "first_name", "last_name", "num_parts"])
bv_processed.to_csv(export_dir+"bv_processed.csv", index = False, encoding = "utf-8") # Got 4,479,371 names

os.system("mysql -uzihe -p"+ os.environ["SQLPW"] +" --local-infile zihe -e \"LOAD DATA LOCAL INFILE '../data/OSS-census/bv_processed.csv'  INTO TABLE bv_names  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' ignore 1 lines\"")

# load json file into json
f = open("/home/hongbo/wocgender/data/name2gender.json")
data = json.load(f)
f.close()
exclude = 0
names = open(name_dir, "w+")
for woc_name in data:
  names.write(woc_name+"\n")
names.close()
print("Name list loaded...")

def add_bv(name):

  gender = 0
  try:
    if data[name]=="male":
      gender = -1
    elif data[name]=="female":
      gender = 1
  except:
    pass
  
  name = fix_name_prefix(0, name)
  if name is None:
    return
  check_in_bv_name = session.query(bv_names).filter(bv_names.c.name == name[1]).first()
  if check_in_bv_name is None:
    return [name, gender]

  return 

name_lst = open(name_dir)
names = [name.strip() for name in name_lst.readlines()]
name_lst.close()
p = Pool(num_proc)
results = [r for r in p.map(add_bv, names) if r is not None]
p.close()
p.join()

gender_dict = {}
bv_name = []
start_id = 11394083 + 1
for result in results:
  result[0][0] = start_id
  bv_name.append(result[0])
  start_id += 1
  if result[1] != 0:
    gender_dict.update({result[0][0]:result[1]}) # dictionary: {bv_name_id : gender}

pickle.dump(gender_dict, open(export_dir+"woc_name_gender", "wb"))
print(len(gender_dict))

bv_name = pd.DataFrame(bv_name, columns = ["id", "name", "first_name", "last_name", "num_parts"])
bv_name.to_csv(export_dir+"update_bv_name.csv", index = False, encoding = "utf-8")
print("Finish bv namsor") # Got 2,004,242

os.system("mysql -uzihe -p"+ os.environ["SQLPW"] +" --local-infile zihe -e \"LOAD DATA LOCAL INFILE '../data/OSS-census/update_bv_name.csv'  INTO TABLE bv_names  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' ignore 1 lines\"")
# 6483613 intotal