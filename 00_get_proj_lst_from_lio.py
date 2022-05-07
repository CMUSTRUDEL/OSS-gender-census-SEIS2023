'''
Get all OSS project id from libraries.io
'''
import datetime
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import pandas as pd
import os
import logging

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

proj_lio = pd.read_csv("/data3/sophie/libraries.io/libraries-1.6.0-2020-01-12/projects-1.6.0-2020-01-12.csv",
   error_bad_lines=False, warn_bad_lines=False, index_col=False)
count_all = 0
count_github = 0
for i, row in proj_lio.iterrows():
    count_all += 1
    try:
        if "github" in row["Repository URL"]:
            count_github += 1
        else:
            print(row)
    except:
        count_all -= 1

print(count_all)
print(count_github)

data_dir = "/data2/zihe/data/"
projs = []
unfound_projs = []
proj_lio = pd.read_csv(data_dir+"lio_unfound_proj_list.csv",
    error_bad_lines=False, warn_bad_lines=False, index_col=False)

print("start reading")

# if language in both lio & ghtorrent is NULL -> discard

for i, row in proj_lio.iterrows():
    try:
        # id_lio = int(row["ID"])
        # url = row["Repository URL"]
        # language = row["Language"]
        # manager = row["Platform"]
        # name = row["Name"]
        # time = row["Created Timestamp"][:-4]
        id_lio = int(row["id_lio"])
        url = row["url"]
        language = row["language"]
        manager = row["manager"]
        name = row["name"]
        time = row["created_time"]
        forked = 0

        # get rid of first kind of url
        slug = url.replace("https://github.com/", "")
        # get rid of second kind of url
        slug = slug.replace("https://raw.github.com/", "")
        # get rid of third kind of url
        slug = slug.replace("https://raw.githubusercontent.com/", "")

        if "/blob/master/" in slug:
            slug = slug[:slug.index("/blob/master/")]
        if "/master/" in slug:
            slug = slug[:slug.index("/master/")]
        if slug.endswith(".git"):
            slug = slug[:-4]
        if slug.endswith("/"):
            slug = slug[:-1]
        if slug.startswith("/"):
            slug = slug[1:]

        gh_id = session.query(projects).filter(projects.c.url == "https://api.github.com/repos/" + slug).first()

        if (gh_id is None):
            gh_id = session.query(projects).filter(
                projects.c.name == name).filter(
                projects.c.created_at == datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S')).first()

        if (gh_id is None and "github" in url):
            unfound_projs.append([id_lio, language, time, manager, name, url, slug])
        else:
            forked = forked if gh_id.forked_from is None else gh_id.forked_from
            if len(language) == 0:
                language = gh_id.language
            projs.append([id_lio, gh_id.id, forked, language, time, manager, name, "https://github.com/" + slug, slug])
    except:
        continue

projs = pd.DataFrame(projs, columns = ["id_lio", "id_gh", "forked_from", "language", "created_time", "manager", "name", "url", "slug"])
projs.to_csv(data_dir+"lio_proj_list_2.csv", index = False, encoding = "utf-8")

unfound_projs = pd.DataFrame(unfound_projs, columns = ["id_lio", "language", "created_time", "manager", "name", "url", "slug"])
unfound_projs.to_csv(data_dir+"lio_unfound_proj_list.csv", index = False, encoding = "utf-8")

os.system("mysql -uzihe -p"+ os.environ["SQLPW"] +" --local-infile zihe -e \"LOAD DATA LOCAL INFILE '/data2/zihe/data/lio_proj_list_2.csv'  INTO TABLE oss_projects  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' ignore 1 lines\"")