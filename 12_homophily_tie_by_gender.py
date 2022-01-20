'''
Count number of ties
'''
import pandas as pd
from multiprocessing import Pool
import math
import pickle
import logging

logging.basicConfig(filename="../data/census/get_tie_count.log", level=logging.WARNING)
logger=logging.getLogger()
num_proc = 16
proj_lst_path = "../data/census/proj_lists_final/"
core_path = "../data/census/dict_contrib/" # for each lang, each pid, {win:{uid:isCore}}
dict_path = "../data/census/contributor_by_win/" # for each lang, {win : dict(all_uid:gender)}
output_path = "../data/network/tie_count_by_win/"
langs = ["JavaScript", "Python", "Java", "Go", "Ruby", "C++", "TypeScript", 
          "PHP", "C#", "C", "HTML", "CSS", "Jupyter", "Shell", "Objective-C"]

def cal_win(year, month):
    return int(math.floor((month-1)/3+1) + (year-2008)*4)
end_window = cal_win(2019, 6)
start_window = cal_win(2008, 1)

def contributor_census(lang):

    proj_list = open(proj_lst_path+lang+".list")
    projs = [proj_repo.strip() for proj_repo in proj_list.readlines()]
    proj_list.close()
    gender_dict = pickle.load(open(dict_path+lang+"_all", "rb"))

    ties = [] # [[win,0,0,0,0]]
    for win in range(start_window, end_window+1):
        ties.append([win,0,0,0,0])

    for pid in projs:
        try:
            core_dict = pickle.load(open(core_path+lang+"/"+pid, "rb"))
            for win in core_dict:
                uids = core_dict[win]
                male = set()
                female = set()
                for uid in uids:
                    try:
                        gender = gender_dict[win][uid]
                    except:
                        gender = 0
                    if gender == -1:
                        male.add(uid)
                    if gender == 1:
                        female.add(uid)
                if (len(male) * (len(male) - 1) / 2) > 100000:
                    logger.warning(lang + " " + str(pid) + " " + str(win) + " " + str(len(male) * (len(male) - 1) / 2))
                ties[win-1][1] += len(male) * (len(male) - 1) / 2
                ties[win-1][2] += len(male) * len(female)
                ties[win-1][3] += len(female) * (len(female) - 1) / 2
                ties[win-1][4] += len(uids) * (len(uids) - 1) / 2
        except:
            pass

    ties = pd.DataFrame(ties, columns = ["win", "m_m", "f_m", "f_f", "all"])
    ties.to_csv(output_path+lang+".csv", index = False, encoding = "utf-8")
    print(lang+" finish")

p = Pool(num_proc)
p.map(contributor_census, langs)
p.close()
p.join()
