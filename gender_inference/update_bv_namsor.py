"""
Use "/home/hongbo/wocgender/data/name2gender.json" to complete bv_names and bv_geo_manual
"""
import openapi_client
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
bv_namsor = Table("bv_namsor_gender_geo_manual_first_last_2_0_10", metadata, autoload=True)
connection = engine.connect()
print('Tables loaded and engine connected...')

# Create second engine and session and load table
url2 = "mysql+mysqlconnector://" + username + ":" + pwd + "@localhost/zihe?charset=utf8"
print('Set up params...')
engine2 = create_engine(url2, pool_recycle = pool_recycle_time)
metadata2 = MetaData(bind=engine2)
DbSession2 = sessionmaker(bind=engine2)
session2 = DbSession2()
print('Second engine and session created...')
bv_names = Table("bv_names", metadata2, autoload=True)
connection2 = engine2.connect()
print('Second table loaded and engine connected...')

# Configure API key authorization: api_key
configuration = openapi_client.Configuration()
configuration.api_key['X-API-KEY'] = os.environ["NAMSOR_API"]
print('API configured')

large_batch_start_id = 4000001
large_batch_size = 80000
small_batch_size = 5000
max_id = 13398326

all_new_geos = []
gender_dict = pickle.load(open(export_dir+"woc_name_gender", "rb"))

def add_geo(id):
  try:
    name_entry = session2.query(bv_names).filter(bv_names.c.id == id).first()
    if name_entry is None:
      return
    name = name_entry.name
    first_name = name_entry.first_name
    last_name = name_entry.last_name

    geo = session.query(bv_namsor).filter(bv_namsor.c.name_id == id).first()
    if geo is not None:
      return [id, geo.likely_gender, geo.gender_scale, geo.score, geo.probability_calibrated]

    # Use WOC gender if we can find
    if name in gender_dict:
      gender = gender_dict[name]
      return [id, "male" if gender == -1 else "female", 2, 0.0, 1.1]

    # create an instance of the API class
    api_instance = openapi_client.PersonalApi(openapi_client.ApiClient(configuration))
    # Run Namsor if cannot find WOC gender
    # 1) get origin
    origin = "IE"
    try:
      result = api_instance.origin(first_name, last_name)
      origin = result.country_origin
    except:
      # print("Reset at origin: " + str(id) + " " + name)
      # time.sleep(5)
      api_instance = openapi_client.PersonalApi(openapi_client.ApiClient(configuration))
      try:
        result = api_instance.origin(first_name, last_name)
        origin = result.country_origin
      except:
        logger.warning("No origin: " + name)

    # 2) get gender
    try:
      result = api_instance.gender_geo(first_name, last_name, origin)
    except:
      # print("Reset at origin: " + str(id) + " " + name + " " + origin)
      # time.sleep(5)
      api_instance = openapi_client.PersonalApi(openapi_client.ApiClient(configuration))
      try:
        result = api_instance.gender_geo(first_name, last_name, origin)
      except:
        logger.warning("No gender: " + name + ", Origin: " + origin)
        #print("No gender: " + name + " " + origin)
        return

    return [id, result.likely_gender, result.score, result.gender_scale, result.probability_calibrated]
  except:
    print("Result error: " + str(id))
    return

def process_large_batch(start_id):
  end_id = min(start_id + large_batch_size, max_id)
  batch_number = int(end_id / large_batch_size) - 1
  print("Processing Batch {}. Processed bv_names id from {} to {}".format(
      batch_number, start_id, end_id-1))
  pool = Pool(num_proc)

  new_geos = [id for id in pool.map(
      func=add_geo, 
      iterable=list(range(start_id, end_id)), 
      chunksize=small_batch_size
      ) if id is not None]
  pool.close()
  pool.join()

  new_geos = pd.DataFrame(new_geos, columns = ["name_id", "likely_gender", "gender_scale", "score", "probability_calibrated"])
  new_geos.to_csv(export_dir+"new_geo_backup/"+str(batch_number) + '.csv', index = False, encoding = "utf-8")
  return end_id

# Chunk large batch
while large_batch_start_id < max_id:
  large_batch_start_id = process_large_batch(large_batch_start_id)

# Export results
all_new_geos = pd.DataFrame(all_new_geos, columns = ["name_id", "likely_gender", "gender_scale", "score", "probability_calibrated"])
all_new_geos.to_csv(export_dir+"update_geos.csv", index = False, encoding = "utf-8")