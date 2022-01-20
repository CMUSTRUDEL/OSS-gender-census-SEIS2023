'''
Select all projects of a specific language.
'''
from multiprocessing import Pool
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os
from os import path, mkdir
print('Libraries imported...')

# Setup parameters
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
projects = Table("projects", metadata, autoload=True)
print('Tables loaded')

# Build connection
connnection = engine.connect()
print('Engine connected and session created...')

# All languages that requires process
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]
output_path = "../data/census/proj_lists_raw/"
num_proc = 15

if not path.isdir(output_path):
  mkdir(output_path)

# Build list
def build_list(lang):

  export_dir = output_path+lang+".list"
  if path.isfile(export_dir):
    print('Finished processing language: ', lang)
    return
  
  if lang=="Jupyter":
    lang = "Jupyter Notebook"

  ght_projs = session.query(projects).filter(
    projects.c.language == lang).filter(projects.c.forked_from.is_(None))
  
  if lang=="Jupyter Notebook":
    lang = "Jupyter"
  
  all_projs_list = []

  for ght_proj in ght_projs:
    all_projs_list.append(str(ght_proj.id))

  open(export_dir, "w+").write(
    "\n".join(item for item in all_projs_list))
  
  print('Finished processing language: ', lang)

pool = Pool(num_proc)
pool.map(build_list, langs)
pool.close()
pool.join()

print('finish')