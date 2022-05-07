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
url = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/zihe?charset=utf8"
print('Set up params...')

# Create engine and session
engine = create_engine(url, pool_recycle = pool_recycle_time)
metadata = MetaData(bind=engine)
DbSession = sessionmaker(bind=engine)
session = DbSession()
projects = Table("oss_projects", metadata, autoload=True)
print('Tables loaded')

# Build connection
connnection = engine.connect()
print('Engine connected and session created...')

# All languages that requires process
langs = ["NPM", "Packagist", "Go", "Pypi", "Rubygems", "NuGet", "Maven", 
          "Bower", "CocoaPods", "Cargo", "Clojars", "Atom", "CPAN", "Meteor", "Hackage",
          "Hex", "Pub", "CRAN", "Puppet", "PlatformIO"]
output_path = "../data/census/proj_lists/"

num_proc = 20

if not path.isdir(output_path):
  mkdir(output_path)

# Build list
def build_list(lang):

  export_dir = output_path+lang+".list"

  if path.isfile(export_dir):
    print('Finished processing language: ', lang)
    return

  ght_projs = session.query(projects).filter(
    projects.c.manager == lang).filter()
  
  all_projs = set()

  for ght_proj in ght_projs:
    all_projs.add(str(ght_proj.id_gh))

  open(export_dir, "a+").write(
    "\n".join(item for item in all_projs))
  
  print('Finished processing language: ', lang)

pool = Pool(num_proc)
pool.map(build_list, langs)
pool.close()
pool.join()

print('finish')