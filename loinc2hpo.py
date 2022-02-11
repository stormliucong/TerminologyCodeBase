# query hpo and retrieval results by using LOINC results

import requests
import pandas as pd
from Utils import *


myOhdsi = OhdsiManager()

url = 'https://raw.githubusercontent.com/TheJacksonLaboratory/loinc2hpoAnnotation/master/loinc2hpo-annotations.tsv'
loinc2hpoAnnotationDf = pd.read_csv(url,sep='\t')
loinc2hpoAnnotationDf.to_sql('hpo_loinc_annotation', con=myOhdsi.engine, index=False, if_exists='replace')

sql = '''
select distinct concept_id, 'POS' as outcome,concept_name from concept c where domain_id like '%Meas Value%' and standard_concept = 'S' and vocabulary_id = 'LOINC'
and (concept_name like '%positive%')
union 
select distinct concept_id, 'NEG' as outcome,concept_name from concept c where domain_id like '%Meas Value%' and standard_concept = 'S' and vocabulary_id = 'LOINC'
and (concept_name like '%negative%')
union 
select distinct concept_id, 'N' as outcome,concept_name from concept c where domain_id like '%Meas Value%' and standard_concept = 'S' and vocabulary_id = 'LOINC'
and (concept_name like '%normal%' and concept_name not like '%abnormal%')
union 
select distinct concept_id, 'L' as outcome, concept_name from concept c where domain_id like '%Meas Value%' and standard_concept = 'S' and vocabulary_id = 'LOINC'
and (concept_name like '%reduce%' or concept_name like '%decrease%' or concept_name like 'low')
union 
select distinct concept_id, 'H' as outcome, concept_name from concept c where domain_id like '%Meas Value%' and standard_concept = 'S' and vocabulary_id = 'LOINC'
and (concept_name like '%elevate%' or concept_name like '%increase%' or concept_name like 'low')
'''
loincOutcomeConceptDf = pd.read_sql(sql,myOhdsi.cnxn)
loincOutcomeConceptDf.to_sql('hpo_loinc_outcome_concept', con=myOhdsi.engine, index=False, if_exists='replace')


sql = '''
IF object_id('hpo_loinc_occurrence', 'U') is not null
    drop table hpo_loinc_occurrence
CREATE TABLE hpo_loinc_occurrence (
    person_id bigint not null,
    hpo_id varchar(50),
    outcome varchar(50),
);

INSERT INTO hpo_loinc_occurrence
select distinct person_id,hpoTermId as hpo_id, ha.outcome
from ohdsi_cumc_2021q3r1.dbo.measurement m
inner join ohdsi_cumc_2021q3r1.dbo.concept c1 on
m.measurement_concept_id = c1.concept_id
inner join ohdsi_cumc_2021q3r1.dbo.hpo_loinc_outcome_concept hc on
m.value_as_concept_id = hc.concept_id
inner join ohdsi_cumc_2021q3r1.dbo.hpo_loinc_annotation ha on
ha.outcome = hc.outcome and ha.loincId = c1.concept_code
'''
myOhdsi.cursor.execute(sql)
myOhdsi.cursor.commit()