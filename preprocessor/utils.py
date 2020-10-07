import re
def get_tokens(line):
    '''
    This functions returns key value pair of Simulink separated by first whitespace
    '''
    line = remove_extra_white_spaces(line)
    return line.split(" ",1)

def remove_extra_white_spaces(line):
    '''
    removes extra white spaces
    '''
    line = line.strip()
    line = re.sub('\t', ' ', line)
    line = re.sub(' +', ' ', line)
    return line



def blk_name_check(name= '"Complexko\"'):
    '''
        blk name can be multiline with quotes in their name.
        TODO: Doesnot handle the case when there is \" in the name.
    '''
    stack = []
    prev = ''
    #print(repr(name).encode('unicode_escape'))
    #print(name)

    for char in name:
        #print(char)
        if char == '"':
            #print(prev)
            if len(stack)==0 or prev == '\\':
                stack.append('"')
            else:
                stack.pop()
        prev = char
    #print(stack)
    if len(stack) == 0:
        return True
    else:
        return False

#print(blk_name_check())