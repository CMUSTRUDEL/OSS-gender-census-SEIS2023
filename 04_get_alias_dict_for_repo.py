# Merge aliases and get dictionary
from multiprocessing import Pool
from alias_merge import resolve_aliases
import os
from os import path, mkdir
from os.path import isfile
import pandas as pd
import pickle

num_proc = 20
list_path = "../data/census/proj_lists/"
repo_path = "../data/census/commits_complete/"
output_path = "../data/census/alias_dicts/"
langs = ["NPM", "Packagist", "Go", "Pypi", "Rubygems", "NuGet", "Maven", 
          "Bower", "CocoaPods", "Cargo", "Clojars", "Atom", "CPAN", "Meteor", "Hackage",
          "Hex", "Pub", "CRAN", "Puppet", "PlatformIO"]

if not path.isdir(output_path):
    mkdir(output_path)

def call_resolve_alias(f):
  pid = f[0]
  lang = f[1]

  if isfile(output_path+lang+"/"+pid):
    return

  try:
    dat = pd.read_csv(repo_path+lang+"/"+pid+".csv", error_bad_lines=False, warn_bad_lines=False)
    unmask = resolve_aliases(dat)
    num_diff = sum([k != unmask[k] for k in unmask])
  except:
    return

  if num_diff > 0:
    pickle.dump(unmask, open(output_path+lang+"/"+pid, "wb"))

  return


def process_projs(lang):

  if not path.isdir(output_path+lang+"/"):
    mkdir(output_path+lang+"/")
  
  proj_list = open(list_path+lang+".list")
  proj_repos = [[proj_repo.strip(),lang] for proj_repo in proj_list.readlines()]
  proj_list.close()
  print("Processing projects:", lang)

  p = Pool(num_proc)
  p.map(call_resolve_alias, proj_repos)
  p.close()
  p.join()


for lang in langs:
  process_projs(lang)