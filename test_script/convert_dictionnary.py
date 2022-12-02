

import numpy as np 

dic_ptc = open("dictionnaire_LidarHD_provisoire.ptc", "r")
dic_brut = []
n=0
for l in dic_ptc :
    n+=1
    if n <10:
        dic_brut.append(l.split())
        print(dic_brut)
        print('\n')
dic_ptc.close() 