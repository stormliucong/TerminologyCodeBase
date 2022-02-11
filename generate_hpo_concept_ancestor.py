from owlready2 import *
import re
from queue import Queue
from GraphUtils import *


def hpo2omop(hp_id,salt = '9'):
    # current max concept id - 46369944
    # 9 for standard name
    # 8 for synonym
    hp_id = hp_id.replace('_', ':')
    omop_id = salt + hp_id.split(':')[1]
    return(omop_id)

onto = get_ontology("http://purl.obolibrary.org/obo/hp.owl").load()
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
ontology_classes = obo.HP_0000001.descendants()

rows = []
ancestor_concept_id = ''
descendant_concept_id = ''
min_levels_of_seperation = ''
max_levels_of_seperation = ''


# kid_dict = {7:[2,3,4,6],6:[1],5:[2],4:[2],3:[1,2],2:[],1:[2]}
# parent_dict = {1:[3,6],2:[1,3,4,5,7],3:[7],4:[7],5:[7],6:[7],7:[]}
# dist_dict = bfs(parent_dict,kid_dict,leaves)
# print(dist_dict)
    

kid_dict = {}
parent_dict ={}
with open('/var/cohd-rare/db/hpo/concepts_ancestor_hpo.txt','w') as f:
    for current_class in ontology_classes:
        hp_id = current_class.name
        concept_id = hpo2omop(hp_id)
        kid_dict[concept_id] = []
        if concept_id not in parent_dict.keys():
            parent_dict[concept_id] = []
        # hp_id = current_class.descendants()
        descendant_concept_ids = [hpo2omop(i.name) for i in current_class.subclasses()]
        for k_id in descendant_concept_ids:
            kid_dict[concept_id].append(k_id)
            if k_id not in parent_dict.keys():
                parent_dict[k_id] = []
            parent_dict[k_id].append(concept_id)
    
    leaves = [keys for keys in kid_dict if len(kid_dict[keys])==0]
    dist_dict = bfs(parent_dict,kid_dict,leaves)
    
    for ancestor_concept_id in dist_dict:
        for descendant_concept_id in dist_dict[ancestor_concept_id]:
            min_levels_of_seperation =  dist_dict[ancestor_concept_id][descendant_concept_id][0]
            max_levels_of_seperation =  dist_dict[ancestor_concept_id][descendant_concept_id][1]
            rows.append('\t'.join([str(ancestor_concept_id),str(descendant_concept_id),str(min_levels_of_seperation),str(max_levels_of_seperation)]))
    content = '\n'.join(rows)
    f.write(content)

        
       



