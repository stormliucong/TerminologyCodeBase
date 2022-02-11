def build_ancestor_dict_from_owl(owl = "/home/cl3720/projects/ADDC/hp.owl"):
    '''
    load owl file
    output a dictionary hpo_id_1|hpo_id_2
    '''
    from lxml import etree
    import re
    import pandas as pd
    # build the parents dicts.
    parents_dict = {}
    tree = etree.parse(owl)
    root = tree.getroot()
    id = ''
    label = ''
    synonym = ''
    i = 0
    for ele1 in root.findall('owl:Class', root.nsmap):
        abouts = ele1.attrib.values()
        for a in abouts:
            m = re.match('.+?(HP_\d+)$', a)
            if m:
                id = m.group(1).replace("_",":")
                parents_dict[id] = []
                for ele3 in ele1.findall('rdfs:subClassOf', root.nsmap):
                    parents = ele3.attrib.values()
                    for p in parents:
                        m = re.match('.+?(HP_\d+)$', p)
                        if m:
                            p = m.group(1)
                            pid = p.replace("_",":")
                            parents_dict[id].append(pid)
            else:
                next

    # some HP is deprecated. Therefore they are isolated HPs
    iso_set = []
    for k,v in parents_dict.items():
        if parents_dict[k] == []:
            iso_set.append(k)

    # build root dicts
    root_dict = {}
    class_set = ['HP:0000118','HP:0012823','HP:0031797','HP:0000005','HP:0040279']
    for query_id in parents_dict.keys():
        tmp_id = query_id
        while True:
            if tmp_id == 'HP:0000001':
                break
            if tmp_id in class_set:
                break
            if tmp_id in iso_set:
                break
            try:
                tmp_id = parents_dict[tmp_id][0]
            except:
                print(tmp_id)
        root_dict[query_id] = tmp_id

    # collect 'HP:0000118' only nodes
    abn_phenotypes_nodes = set()
    for i in root_dict.keys():
        if root_dict[i] == 'HP:0000118':
            abn_phenotypes_nodes.add(i)

    # find abn_phenotypes_nodes only ancestor
    def get_parents(node):
        if node == 'HP:0000118':
            return None
        # maintain a global one for recursive search.
        for parent in parents_dict[node]:
            if parent in abn_phenotypes_nodes:
                ancestor_set.add(parent)
                get_parents(parent)

    ancestor_set = set()
    ancestor_dict = {}
    for query_id in parents_dict.keys():
        if query_id in abn_phenotypes_nodes:
            ancestor_set = set()
            get_parents(query_id)
            ancestor_dict[query_id] = ancestor_set

    # build an ancestor DF
    d = []
    for node1 in ancestor_dict.keys():
        d.append({'hpo_id_1': node1, 'hpo_id_2': node1})
        for node2 in ancestor_dict[node1]:
            d.append({'hpo_id_1': node1, 'hpo_id_2': node2})
    anestor_df = pd.DataFrame(d)
    return anestor_df

anestor_df = build_ancestor_dict_from_owl(owl="/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/hpo/hp.owl")
# import pickle
# ancestry_file = open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/hp_2021_02_23_ancestry.pkl','wb')
# pickle.dump(anestor_df,ancestry_file)
# ancestry_file.close()
