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
with open('/var/cohd-rare/db/mondo/concepts_mondo.txt','w') as f:

    for current_class in ontology_classes:
        # only keep gard or ordo terms.
        subset = set([str(rare_set) for rare_set in current_class.inSubset])

        if  subset & rare_set:
            mondo_id = current_class.name.replace('_', ':')
            mondo_name = current_class.label[0]
            # to omop
            concept_id = mondo2omop(mondo_id,salt = '8')
            concept_name = mondo_name
            standard_concept = 'S'
            concept_code = mondo_id
            rows.append('\t'.join([concept_id,concept_name,domain_id,vocabulary_id,concept_class_id,standard_concept,concept_code,valid_start_date,valid_end_date,invalid_reason]))
        # id_index = 0
        # for syns in current_class.hasExactSynonym:
        #     id_index += 1
        #     concept_id = hpo2omop(hp_id,salt = str(id_index) + '9')
        #     concept_name = syns
        #     standard_concept = ''
        #     rows.append('\t'.join([concept_id,concept_name,domain_id,vocabulary_id,concept_class_id,standard_concept,concept_code,valid_start_date,valid_end_date,invalid_reason]))
    content = '\n'.join(rows)
    f.write(content)