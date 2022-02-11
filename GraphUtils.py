from collections import defaultdict

def bfs(parent_dict:dict, kid_dict: dict, leaves:list): #function for BFS
    # init the leaves.
    dist_dict = defaultdict(dict)
    ancestors = leaves
    
            
    while(len(ancestors) > 0):
        for a in ancestors:
            if a not in dist_dict[a]:
               dist_dict[a][a] = (0,0) # descendant, min, max.
        
        # add one edge for each leave in the current ancestors
        ancestors = list(set([m for a in ancestors for m in parent_dict[a]]))
        for a in ancestors:
            # go through each ancestor
            for d in kid_dict[a]:
                if d == a:
                    # skip if this is a self connect edge.
                    next
                for dd in dist_dict[d].keys():
                    # consider its sub-edge.
                    min_dist = dist_dict[d][dd][0]
                    max_dist = dist_dict[d][dd][1]
                    if dd not in dist_dict[a]:
                        # not previously connected two nodes.
                        dist_dict[a][dd] = (min_dist+1,max_dist+1)
                    else:
                        dist_dict[a][dd] = (min(min_dist+1,dist_dict[a][dd][0]),max(max_dist+1,dist_dict[a][dd][1]))
    return dist_dict

if __name__ == '__main__':
    # kid_dict = {7:[4,6],6:[2,4,5],5:[2,3],4:[1,2],1:[],2:[],3:[]}
    # parent_dict = {1:[4],2:[4,5,6],3:[5],4:[6,7],5:[6],6:[7],7:[]}
    kid_dict = {7:[2,3,4,6],6:[1],5:[2],4:[2],3:[1,2],2:[],1:[2],8:[9],9:[]}
    parent_dict = {1:[3,6],2:[1,3,4,5,7],3:[7],4:[7],5:[7],6:[7],7:[],9:[8],8:[]}
    leaves = [keys for keys in kid_dict if len(kid_dict[keys])==0]
    dist_dict = bfs(parent_dict,kid_dict,leaves)
    print(dist_dict)