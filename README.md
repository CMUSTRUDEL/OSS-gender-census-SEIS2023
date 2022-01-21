# MSR2022-Census
Code and figures of MSR 2022 submission


## Code: Gender Inference
Files in gender_inference.

1. `update_bv_names`: get valid names with fixed prefix and filtered length.
2. `update_bv_namsor`: get namsor gender.
3. `connect_namsor_ght`: get mapping between ghtorrent user and their inferred gender.


## Code: Census
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

## Figure: Results
### Contributor distribution in 15 ecosystems and all
![All_contributor](https://user-images.githubusercontent.com/40445229/150443478-c2635d54-b12a-4b8b-94cf-a4a9f64150a2.png)
![C#_contributor](https://user-images.githubusercontent.com/40445229/150443480-74ac52fe-d5dc-4457-8e27-18091ab937ab.png)
![C_contributor](https://user-images.githubusercontent.com/40445229/150443482-255ec6d1-1b20-4e4a-a71f-6fbfe3357d45.png)
![C++_contributor](https://user-images.githubusercontent.com/40445229/150443483-dd16515b-ba9e-42cb-811e-fe36d5628c2e.png)
![CSS_contributor](https://user-images.githubusercontent.com/40445229/150443484-357a6a12-5533-4a3f-bf9d-f04aefb2a111.png)
![Go_contributor](https://user-images.githubusercontent.com/40445229/150443485-f608a302-6527-40ef-b386-6aeaa436409d.png)
![HTML_contributor](https://user-images.githubusercontent.com/40445229/150443486-6e923268-35b0-4e37-9f10-08bc539c8b59.png)
![Java_contributor](https://user-images.githubusercontent.com/40445229/150443487-cd0b552b-c68d-4762-8616-f94c73ef79ea.png)
![JavaScript_contributor](https://user-images.githubusercontent.com/40445229/150443488-3166f06c-707b-4ca3-8848-afc25324b0cd.png)
![Jupyter_contributor](https://user-images.githubusercontent.com/40445229/150443489-4a3f432b-54f6-4b36-9b75-9dc58ece342e.png)
![Objective-C_contributor](https://user-images.githubusercontent.com/40445229/150443490-612cb8d1-626f-48ad-b509-8ac2bba77309.png)
![PHP_contributor](https://user-images.githubusercontent.com/40445229/150443492-21d69a94-af14-4a73-a602-5fcd419d06ae.png)
![Python_contributor](https://user-images.githubusercontent.com/40445229/150443494-61551009-f48c-47f8-b4b1-0754144c5452.png)
![Ruby_contributor](https://user-images.githubusercontent.com/40445229/150443496-ea0e220e-66ff-4fea-8429-d9353f68330d.png)
![Shell_contributor](https://user-images.githubusercontent.com/40445229/150443497-3943f8a8-10a0-4b2b-9fa0-58caa5b99171.png)
![TypeScript_contributor](https://user-images.githubusercontent.com/40445229/150443498-043d0f74-e62f-447a-9257-7ca724b8b27c.png)


### Commit distribution in 15 ecosystems and all
![All_commit](https://user-images.githubusercontent.com/40445229/150443420-1f89a1e6-27ab-4e4a-84e5-eb2abf1a27f9.png)
![C#_commit](https://user-images.githubusercontent.com/40445229/150443423-4d6df715-ea86-43fe-a32a-97bbd8b8358f.png)
![C_commit](https://user-images.githubusercontent.com/40445229/150443424-17e2a707-9556-461c-9d88-b9ddf0751e6c.png)
![C++_commit](https://user-images.githubusercontent.com/40445229/150443425-86fc8ffb-e243-4b63-a1d3-7f6b8c05883a.png)
![CSS_commit](https://user-images.githubusercontent.com/40445229/150443426-2143033a-1140-4bd7-90b6-8fe6631a682f.png)
![Go_commit](https://user-images.githubusercontent.com/40445229/150443428-8994c362-27ea-49a7-9aae-9dfbf136c4a9.png)
![HTML_commit](https://user-images.githubusercontent.com/40445229/150443429-076f8da6-a6a4-4c69-b4a0-5c08706d9a69.png)
![Java_commit](https://user-images.githubusercontent.com/40445229/150443431-434c485c-b915-4c47-9a6a-870dbb14cf7f.png)
![JavaScript_commit](https://user-images.githubusercontent.com/40445229/150443433-fee8de4f-f3d3-4122-a9ad-b0ef5c636850.png)
![Jupyter_commit](https://user-images.githubusercontent.com/40445229/150443435-0adf45af-a03d-4c9b-ac68-513885762760.png)
![Objective-C_commit](https://user-images.githubusercontent.com/40445229/150443437-d7d2b35a-41a2-4b54-a0b2-891ce912b2f0.png)
![PHP_commit](https://user-images.githubusercontent.com/40445229/150443438-0a311984-875c-4853-a2d2-4decd7eecd81.png)
![Python_commit](https://user-images.githubusercontent.com/40445229/150443439-704f0b6d-a7ef-4338-9f68-7f136f95eb58.png)
![Ruby_commit](https://user-images.githubusercontent.com/40445229/150443441-54aad43b-25a7-4ee8-a657-b584bbb6fffe.png)
![Shell_commit](https://user-images.githubusercontent.com/40445229/150443442-7bfb0e19-7082-4e71-bac4-171d8627002f.png)
![TypeScript_commit](https://user-images.githubusercontent.com/40445229/150443443-02aa76a1-7d7f-44df-add9-08bfb350279d.png)


### Number of projects and female-participated projects in 15 ecosystems and all
![All_project](https://user-images.githubusercontent.com/40445229/150443572-c97d3310-cb47-40d0-88ab-833a5aa51db2.png)
![C#_project](https://user-images.githubusercontent.com/40445229/150443574-e9c54e00-3899-4d0b-a04a-4ade734dfc68.png)
![C_project](https://user-images.githubusercontent.com/40445229/150443575-c93701c9-d09b-422e-828e-fc2038b14c85.png)
![C++_project](https://user-images.githubusercontent.com/40445229/150443576-e085fcee-51d8-4bb2-b842-84cba475fb1f.png)
![CSS_project](https://user-images.githubusercontent.com/40445229/150443577-f1e1bdb3-f47f-4ec7-ba6e-26cec48c017b.png)
![Go_project](https://user-images.githubusercontent.com/40445229/150443578-83f18482-17f8-4d10-9524-b2d5168c8cbb.png)
![HTML_project](https://user-images.githubusercontent.com/40445229/150443580-0a501cf0-846a-4e0d-8e87-dd25afc2bebd.png)
![Java_project](https://user-images.githubusercontent.com/40445229/150443581-c4c18896-ed32-436f-ba93-c26c685235d4.png)
![JavaScript_project](https://user-images.githubusercontent.com/40445229/150443583-1419aa0b-2770-4801-b46b-8284cbc100c3.png)
![Jupyter_project](https://user-images.githubusercontent.com/40445229/150443584-ee772a1c-1123-4275-b20d-0112b4b6bb8f.png)
![Objective-C_project](https://user-images.githubusercontent.com/40445229/150443586-f95e0b6b-d922-4523-8b77-e08392649e42.png)
![PHP_project](https://user-images.githubusercontent.com/40445229/150443587-db84aa03-28be-44d8-a8c6-d21ed9e0c2e2.png)
![Python_project](https://user-images.githubusercontent.com/40445229/150443588-f8c3abee-9823-49f2-aa4b-13d5f5c2b93c.png)
![Ruby_project](https://user-images.githubusercontent.com/40445229/150443589-c497e24c-c46b-41c7-a516-e7e984011c78.png)
![Shell_project](https://user-images.githubusercontent.com/40445229/150443591-68cd7d73-1075-4c78-b7a1-138e2c954e0b.png)
![TypeScript_project](https://user-images.githubusercontent.com/40445229/150443592-f691cd6b-825d-4401-abf1-d108d60dc7b7.png)
![All_New_Created_Project_Log](https://user-images.githubusercontent.com/40445229/150443593-2f82125b-bbc5-4fdc-a85f-0a4a3d84df5b.png)
![All_New_Created_Project_Orig](https://user-images.githubusercontent.com/40445229/150443594-5274ee3c-ac11-4b8d-b09b-faae2109ae4d.png)


### Most popular names for female and male contributors on GHTorrent
![male_name](https://user-images.githubusercontent.com/40445229/150443662-86bf54bc-d4f5-43b0-b1d4-815c599305dd.png) ![female_name](https://user-images.githubusercontent.com/40445229/150443663-a0f748b7-e360-498e-bcb5-a641675397e1.png)
