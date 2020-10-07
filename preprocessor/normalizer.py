from string import ascii_lowercase as asc_l
from math import floor
def get_normalize_block_name(idx) -> str:
    # returns upto two character names
    # idx starts from 1
    #TODO assert check idx > 0

    if idx <= 26:
        return '"'+asc_l[idx-1]+'"'
    elif idx <= 26*26:
        return '"'+asc_l[floor(idx/26)-1] + asc_l[idx%26-1]+'"'
    else:
        pass #TODO throw error or handle other ways

# lst = []
# st = set()
# for i in range(1,26*26):
#     a =get_normalize_block_name(i)
#     if a == '"z"':
#         print(i)
#     if a in lst:
#         print(a,i)
#     lst.append(a)
#     st.add(a)
# print(len(lst))
# print(len(st))
# print(26*26)
