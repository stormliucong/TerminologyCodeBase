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
ontology_classes = obo.HP_0000118.descendants()

rows = []
domain_id = 'phenotypes'
vocabulary_id = 'hpo'
concept_class_id = 'HPO'
valid_start_date = '2011-01-01'
valid_end_date = '2099-12-31'
invalid_reason = ''

with open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/hpo/synonym_hpo.txt','w') as f:
    for current_class in ontology_classes:
        iri = current_class.iri
        hp_id = current_class.name.replace('_', ':')
        hp_name = current_class.label[0]
        # to omop
        concept_id = hpo2omop(hp_id,salt = '9')
        concept_name = hp_name
        hpo_synonym = current_class.hasExactSynonym + current_class.hasRelatedSynonym + [concept_name]
        standard_concept = 'S'
        concept_code = hp_id
        for i in hpo_synonym:
            rows.append('\t'.join([concept_id,concept_code,i]))
    content = '\n'.join(rows)
    f.write(content)

