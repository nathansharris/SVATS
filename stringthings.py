#!/bin/python3

import re
import sys
import pandas as pd
from fuzzywuzzy import fuzz

def parse_args(args_list):
    #set pretty much all defaults to False and overide them if needed. 
    dd = output = exact = multi = syns = filelist = False
    
    if "--a" not in args_list or "--" in args_list[args_list.index("--a")+1]:
        print(f'Missing file a')
        quit()
    else:
        fname1 = args_list[args_list.index("--a") + 1]
    if "--b" not in args_list or "--" in args_list[args_list.index("--b")+1]:
        print(f'Missing file b')
        quit()
    else:
        fname2 = args_list[args_list.index("--b") + 1]
    if "--delim" in args_list:
        delim = args_list[args_list.index("--delim") + 1]
    else:
        delim = ","
    if "--drop-duplicates" in args_list:
        dd = True 
    if "--exact" in args_list:
        exact = True
    if "--output" in args_list:
        output = True
    if "--multi" in args_list:
        multi = True
        arginds = [i for i,j in enumerate(args_list) if "--" in j]+[len(args_list)]
        filelist = args_list[args_list.index("--multi")+1:arginds[arginds.index(args_list.index("--multi"))+1]]
    if "--synonyms" in args_list:
        syn = args_list.index("--synonyms") + 1
        with open(args_list[syn]) as f:
            syns = f.readlines()
            syns = [re.sub(delim + " *", ",", syn).strip().split(",") for syn in syns]
            syns = {syn[0]:syn[1:] for syn in syns}
            syns = { v: k for k, l in syns.items() for v in l }
    return fname1,fname2,dd,exact,syns,output,multi,filelist,delim
    
def syntrim(x,y,syns):
    if syns != False:
        orig_x = x
        orig_y = y
    x = [syns[i] if i in syns.keys() else i for i in x]
    y = [syns[i] if i in syns.keys() else i for i in y]
    
    if len(x) != len(set(x)):
        print(f"Duplicate names found in file {fname1} after collapsing synonyms")
    if len(y) != len(set(y)):
        print(f"Duplicate names found in file {fname2} after collapsing synonyms")
    # Put line here to check for losing terms to synonym collapse. 
    x_map = {i:j for i,j in zip(x,orig_x)}
    y_map = {i:j for i,j in zip(y,orig_y)}
    return x,x_map,y,y_map
        
if __name__ == "__main__":
    fname1,fname2,dd,exact,syns,output,multi,filelist,delim = parse_args(sys.argv[1:])
    #args = ["--multi", "foo.txt","bar.txt","cat.txt","--synonyms", "syn.txt"]
    # Strip lagging spaces after a delimiter
    
    with open(fname1) as f:
        x = f.readline().strip()
        x = re.sub(delim + " *", ",", x).split(",")
        file1_num = len(x)
    with open(fname2) as f:
        y = f.readline().strip()
        y = re.sub(delim + " *", ",", y).split(",")
    if dd:
        x = list(set(x))
        y = list(set(y))
    
    # Swap out synonyms before the search
    x,x_map,y,y_map = syntrim(x,y,syns)
    
    # Let us find exsiting exact matches first. 
    exacts = [i for i in x if i in y]
    if exact and not output:
        print("\n"+"-"*80)
        print(f'Exact matches:')
        for i in exacts:
            print(i)

    x = [i for i in x if i not in exacts]
    y = [i for i in y if i not in exacts]
    
    scores = pd.DataFrame(0, index = x, columns = y)
    for(col,throw) in scores.iteritems():
        diffs = [fuzz.token_set_ratio(col,string) for string in scores.index]
        scores[col] = diffs
    # Sort by the maxes in each row
    scores = scores.reindex(scores.max(1).sort_values(ascending=False).index)
    
    dis = pd.DataFrame(scores.idxmax(axis=1))
    dis = dis.rename(columns={0:"Top match"})
    
    dis["score"] = [fuzz.token_set_ratio(i,j) for i,j in zip(dis.index, dis.iloc[:,0])]
    
    if 'x_map' in globals() and 'y_map' in globals():
        dis.index = [x_map[i] for i in dis.index]
        dis.iloc[:,0] = [y_map[i] for i in dis.iloc[:,0]]

    if output:
        if exact:
            print(','.join(exacts))
        else:
            print(','.join(dis.index))
    else:
        print(f'\nNames in {fname1} are checked against names in {fname2}')
        print("-"*80)
        print(f'{len(exacts)} of {file1_num} entries from {fname1} ({round(len(exacts)/file1_num, 3)}) found an exact match in {fname2}\n')
        print(f'Remaining entries and their closest match from {fname2} are \nshown below with their fuzzy scores.')
        print("-"*80)
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            print(dis)
        print("-"*80)
        print(f'Scores are generated using the token_set_ratio methods from package fuzzywuzzy.')