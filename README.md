# MSR2022-Census
Code and figures of MSR 2022 submission


## Gender Inference
Files in gender_inference.

1. `update_bv_names`: get valid names with fixed prefix and filtered length.
2. `update_bv_namsor`: get namsor gender.
3. `connect_namsor_ght`: get mapping between ghtorrent user and their inferred gender.


## Census
We process the 15 languages that are most popular in the ghtorrent database projects table. They are 1) JavaScript, 2) Java, 3) Python, 4) HTML, 5) Ruby, 6) PHP, 7) C++, 8) CSS, 9) C, 10) C#, 11) Jupyter Notebook, 12) Shell, 13) TypeScript, 14) Go, 15) Objective-C. For all the following scripts, we group the results by project language in the project table. For the final census, we kept projects with at least 4 unique, non-bot contributors and all commits made between 2008-01-01 and 2019-03-31.

1. `01_get_proj_lst_from_ght`: get `project_id` of all projects written in one of the 15 specified language.
2. `02_get_comits_for_proj `: get the commits for each project in the lists from step 1. Each project has a csv file containing all commit `sha`, author `id`, window of commit, author `name`, author `email`, and whether is fake. All projects have at least 1 valid commits, aka made by users with valid login and name (filtered out users that can't be found in users_private and type ORG in users).
3. `03_find_possible_bots_in_commits`: find the people who made made at least 1000 commits in a window, and then manually inspect the output to get a bot list.
4. `04_get_alias_dict_for_repo`: get all dictionaries for projects that have authors that can be merged. `alias_merge.py` contains a helper function, and `alias` defines an Alias object which is used in `alias_merge.py`.
5. `05_clean_author_for_commits`: merge alias and label bots, using results from running 4 and 5. Filter out projects with less than 3 contributors (before merging).
6. `06_filter_proj_scale`: filter out projects with 1 million+ commits (manually inspected) or less than 3 unique contributors.
7. `07_clean_proj_lst`: clean project list for faster program execution.
8. `08_build_contrib_dict`: find core contributors for each project for each window. Gives core census for each project, also 2 dictionaries, one describing core/peripheral roles of each project in each win, and the other describes commit number of each project in each win.
9. `09_contrib_gender_by_win`: get by window by gender contributor counts for all and core contributors.
10. `10_commit_gender_by_win`: get by window by gender commit counts.
11. `11_proj_count_by_gender`: get by window number of active projects and active female-participated projects.
12. `12_homophily_tie_by_gender`: calculate homophily tie between female and male.
13. `13_most_diverse_proj_owners`: find the 50 projects with the most female contributors in each ecosystem.

## Results
