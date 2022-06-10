#!/bin/python3

import re
import sys
import pandas as pd
from fuzzywuzzy import fuzz



if __name__ == "__main__":
    #fname1 = "file1.txt"
    #fname2 = "file2.txt"
    
    args = sys.argv[1:]
    print(args)
    #args = ["--synonyms", "syn.txt"]
    
    if "--a" in args:
        fname1 = args[args.index("--a") + 1]
        print(fname1)
    else:
        print(f'Missing file a')
        quit()
    if "--b" in args:
        fname2 = args[args.index("--b") + 1]
    else:
        print(f'Missing file b')
        quit()
    if "--delim" in args:
        delim = args[args.index("--delim") + 1]
    else:
        delim = ","
    
    if "--synonyms" in args:
        synonyms = True
        syn = args.index("--synonyms") + 1
        with open(args[syn]) as f:
            syns = f.readlines()
            syns = [re.sub(delim + " *", ",", syn).strip().split(",") for syn in syns]
            syns = {syn[0]:syn[1:] for syn in syns}
            syns = { v: k for k, l in syns.items() for v in l }
    else:
        synonyms = False
    
    # Strip lagging spaces after a delimiter
    with open(fname1) as f:
        x = f.readline().strip()
        x = re.sub(delim + " *", ",", x).split(",")
        file1_num = len(x)
    with open(fname2) as f:
        y = f.readline().strip()
        y = re.sub(delim + " *", ",", y).split(",")
    
    # Swap out synonyms before the search
    if synonyms:
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
    
    # Let us find exsiting exact matches first. 
    exacts = [i for i in x if i in y]
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
    if synonyms:
        dis.index = [x_map[i] for i in dis.index]
        dis.iloc[:,0] = [y_map[i] for i in dis.iloc[:,0]]

    print(f'\nNames in {fname1} are checked against names in {fname2}')
    print("-"*80)
    print(f'{len(exacts)} of {file1_num} entries from {fname1} ({round(len(exacts)/file1_num, 3)}) found an exact match in {fname2}\n')
    print(f'Remaining entries and their closest match from {fname2} are \nshown below with their fuzzy scores.')
    print("-"*80)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(dis)
    print("-"*80)
    print(f'Scores are generated using the token_set_ratio methods from package fuzzywuzzy.')