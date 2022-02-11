from owlready2 import *


def mondo2omop(id,salt = '8'):
    # current max concept id - 46369944
    # 8 for standard name
    # 81 for synonym
    if salt == '8':
        omop_id = salt + id.split(':')[1]
    else:
        omop_id = salt + id.split(':')[1][1:]
    return(omop_id)

onto = get_ontology("http://purl.obolibrary.org/obo/mondo.owl").load()
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
ontology_classes = obo.MONDO_0000001.descendants()
# ontology_classes_2 = obo.MONDO_0042489.descendants()


rows = []
domain_id = 'diseases'
vocabulary_id = 'mondo'
concept_class_id = 'MONDO'
valid_start_date = '2011-01-01'
valid_end_date = '2099-12-31'
invalid_reason = ''

rare_set = set(['mondo.ordo_group_of_disorders', 'mondo.gard_rare', 'mondo.ordo_disease'])
with open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/mondo/synonym_mondo.txt','w') as f:
    for current_class in ontology_classes:
        # only keep gard or ordo terms.
        subset = set([str(rare_set) for rare_set in current_class.inSubset])

        if  subset & rare_set:
            mondo_id = current_class.name.replace('_', ':')
            mondo_name = current_class.label[0]
            mondo_synonym = current_class.hasExactSynonym + current_class.hasRelatedSynonym + [mondo_name]

            # to omop
            concept_id = mondo2omop(mondo_id,salt = '8')
            concept_name = mondo_name
            standard_concept = 'S'
            concept_code = mondo_id
            for i in mondo_synonym:
                rows.append('\t'.join([concept_id,concept_code,i]))
    content = '\n'.join(rows)
    f.write(content)

