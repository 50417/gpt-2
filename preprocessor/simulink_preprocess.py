from typing import List
from utils import get_tokens
def remove_graphic_component(text: str) -> List:
    lines = []
    remove_list = ["Position","ZOrder","SID","Points"]
    for line in text.split("\n"):
        line = line.lstrip()
        if line.startswith(tuple(remove_list)) or len(line)==0:
            continue
        lines.append(line)
    return lines


def keep_minimum_component_in_block(text: str) -> List:
    lines = []
    add_block_comp_list = ["BlockType","Name","Ports","SourceBlock","SourceType"]
    brace_count = 0
    for line in text.split("\n"):
        line = line.strip()
        if len(line) == 0:
            continue
        tok = get_tokens(line)
        if "Block" in tok and "{" in tok:
            brace_count = 1
            lines.append(line)
        elif "}" in tok:
            brace_count = max(0, brace_count - 1)
            if brace_count != 0:
                lines.append(line)
        if brace_count == 0:
            lines.append(line)

        else:
            if line.startswith(tuple(add_block_comp_list)):
                lines.append(line)


    return lines
# import os
# directory = '/home/sls6964xx/Documents/GPT2/gpt-2/preprocessor/output'
# count = 1
# if not os.path.exists("Minimum"):
#     os.mkdir("Minimum")
# for files in os.listdir(directory):
#      count +=1
#      print(count, " : ", files)
#      with open(directory + "/" + files,"r") as file:
#          output = keep_minimum_component_in_block(file.read())
#      tmp_path = os.path.join("Minimum", files)
#      with open(tmp_path, 'w') as r:
#          r.write("\n".join(output))
