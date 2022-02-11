from owlready2 import *


def hpo2omop(hp_id,salt = '9'):
    # current max concept id - 46369944
    # 9 for standard name
    # 91 for synonym
    if salt == '9':
        omop_id = salt + hp_id.split(':')[1]
    else:
        omop_id = salt + '1' + hp_id.split(':')[1][1:]
    return(omop_id)

onto = get_ontology("http://purl.obolibrary.org/obo/hp.owl").load()
obo = onto.get_namespace("http://purl.obolibrary.org/obo/")
ontology_classes = obo.HP_0000001.descendants()

rows = []
domain_id = 'phenotypes'
vocabulary_id = 'hpo'
concept_class_id = 'HPO'
valid_start_date = '2011-01-01'
valid_end_date = '2099-12-31'
invalid_reason = ''
with open('/var/cohd-rare/db/hpo/concepts_hpo.txt','w') as f:

    for current_class in ontology_classes:
        iri = current_class.iri
        hp_id = current_class.name.replace('_', ':')
        hp_name = current_class.label[0]
        # to omop
        concept_id = hpo2omop(hp_id,salt = '9')
        concept_name = hp_name
        
        standard_concept = 'S'
        concept_code = hp_id
        
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
    