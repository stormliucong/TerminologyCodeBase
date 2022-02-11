from owlready2 import *

onto = get_ontology("http://purl.obolibrary.org/obo/hp.owl").load()
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
ontology_classes = obo.HP_0000001.descendants()
rows = []
with open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/cui/hpo2cui.txt','w') as f:
    for current_class in ontology_classes:
        iri = current_class.iri
        hp_id = current_class.name.replace('_', ':')
        hp_name = current_class.label[0]
        cross_ref = current_class.hasDbXref
        for c in cross_ref:
            if c.startswith('UMLS:'):
                cui = c.split(":")[1]
                rows.append('\t'.join([hp_id,cui]))
    content = '\n'.join(rows)
    f.write(content)
    
onto = get_ontology("http://purl.obolibrary.org/obo/mondo.owl").load()
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
ontology_classes = obo.MONDO_0000001.descendants()
rare_set = set(['mondo.ordo_group_of_disorders', 'mondo.gard_rare', 'mondo.ordo_disease'])

rows = []
with open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/cui/mondo2cui.txt','w') as f:

    for current_class in ontology_classes:
        subset = set([str(rare_set) for rare_set in current_class.inSubset])
        if  subset & rare_set:
            mondo_id = current_class.name.replace('_', ':')
            cross_ref = current_class.hasDbXref
            for c in cross_ref:
                if c.startswith('UMLS:'):
                    cui = c.split(":")[1]
                    rows.append('\t'.join([mondo_id,cui]))
    content = '\n'.join(rows)
    f.write(content)