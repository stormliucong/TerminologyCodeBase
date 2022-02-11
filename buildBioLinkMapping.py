import sys
sys.path.append('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/02-scripts/workflow')
from Utils import *
import pandas as pd
import json
import difflib
from collections import defaultdict
from typing import Iterable, Optional, Dict, List, Tuple
import urllib3
from bmt import Toolkit


# Static instance of the Biolink Model Toolkit
bm_toolkit = Toolkit('https://raw.githubusercontent.com/biolink/biolink-model/2.2.1/biolink-model.yaml')


def build_mappings(cur,conn) -> Tuple[str, int]:
        """ Rebuilds the mappings between OMOP and Biolink
        Returns
        -------
        Number of concepts
        """
        logging.info('Starting a new build of OMOP-Biolink mappings')

        # Map OMOP vocabulary_id to Biolink prefixes
        prefix_map = {
            'ICD10CM': 'ICD10',
            'ICD9CM': 'ICD9',
            'MedDRA': 'MEDDRA',
            'SNOMED': 'SNOMEDCT',
            'HCPCS': 'HCPCS',
            'CPT4': 'CPT'
        }

        # Get current number of mappings that weren't from string searches
        sql = 'SELECT COUNT(*) AS count FROM dbo.oard_biolink_mappings WHERE string_search = 0;'
        cur.execute(sql)
        current_count = cur.fetchall()[0][0]

        # Get current number of mappings that are from string searches
        sql = 'SELECT COUNT(*) AS count FROM dbo.oard_biolink_mappings WHERE string_search = 1;'
        cur.execute(sql)
        current_count_string = cur.fetchall()[0][0]

        # Build the SQL insert
        mapping_count = 0
        params = list()

        ########################## Conditions ##########################
        logging.info('Mapping condition concepts')

        # Get all active condition concepts
        sql = """
        SELECT DISTINCT c.concept_id, c.concept_name, c.vocabulary_id, c.concept_code,
            c.concept_class_id, c.standard_concept
        FROM dbo.[condition_occurrence] co
        LEFT JOIN dbo.concept c
        ON co.[condition_concept_id] = c.concept_id
        ORDER BY c.concept_id;
        """
        cur.execute(sql)
        condition_concepts = cur.fetchall()
        omop_concepts = {c[0]:c for c in condition_concepts}

        # Normalize with SRI Node Norm via ICD, MedDRA, and SNOMED codes
        omop_biolink = {c[0]:prefix_map[c[2]] + ':' + c[3] for c in condition_concepts if c[2] in prefix_map}
        mapped_ids = list(omop_biolink.values())
        normalized_ids = SriNodeNormalizer.get_normalized_nodes(mapped_ids)

        # Create mappings
        if len(mapped_ids) > 0:
            for omop_id in omop_biolink.keys():
                mapped_id = omop_biolink[omop_id]
                omop_label = omop_concepts[omop_id][2]
                if normalized_ids[mapped_id] is None:
                    # Use the OMOP vocabulary mapping only
                    categories = json.dumps(['biolink:DiseaseOrPhenotypicFeature'])
                    provenance = f'(OMOP:{omop_id})-[OMOP Map]-({mapped_id})'
                    distance = 1
                    string_similarity = 1
                    params.extend([omop_id, mapped_id, omop_label, categories, provenance, False, distance, string_similarity])
                else:
                    # Use the normalized node
                    biolink_norm_node = normalized_ids[mapped_id]
                    biolink_norm_id = biolink_norm_node.normalized_identifier.id
                    biolink_label = biolink_norm_node.normalized_identifier.label
                    categories = json.dumps(biolink_norm_node.categories)
                    provenance = f'(OMOP:{omop_id})-[OMOP Map]-({mapped_id})'
                    distance = 1
                    string_similarity = difflib.SequenceMatcher(None, omop_label.lower(), biolink_label.lower()).ratio()
                    if mapped_id != biolink_norm_id:
                        provenance += f'-[SRI Node Norm]-({biolink_norm_id})'
                        distance += 1
                    params.extend([omop_id, biolink_norm_id, biolink_label, categories, provenance, False, distance, string_similarity])
                mapping_count += 1

        # ########################## Drugs - non-ingredients ##########################
        # logging.info('Mapping drug concepts')

        # # Get all active RXNORM drug (non-ingredient) concepts
        # sql = """
        # SELECT c.concept_id, c.concept_name, c.vocabulary_id, c.concept_code, c.concept_class_id, standard_concept
        # FROM
        # (SELECT DISTINCT concept_id FROM concept_counts) x
        # JOIN concept c ON x.concept_id = c.concept_id
        # WHERE c.domain_id = 'drug' AND c.concept_class_id != 'ingredient' AND c.vocabulary_id = 'RxNorm'
        # ORDER BY c.concept_id;
        # """
        # cur.execute(sql)
        # drug_concepts = cur.fetchall()

        # # Use RXNORM (RXCUI) for Biolink ID
        # omop_concepts = {c['concept_id']:c for c in drug_concepts}
        # omop_biolink = {c['concept_id']:'RXCUI:' + c['concept_code'] for c in drug_concepts}

        # # Create mappings
        # for omop_id in omop_concepts:
        #     mapped_id = omop_biolink[omop_id]
        #     biolink_label = omop_concepts[omop_id]['concept_name']
        #     categories = json.dumps(['biolink:Drug'])
        #     provenance = f'(OMOP:{omop_id})-[OMOP Map]-({mapped_id})'
        #     distance = 1
        #     string_similarity = 1
        #     params.extend([omop_id, mapped_id, biolink_label, categories, provenance, False, distance, string_similarity])
        #     mapping_count += 1

        # ########################## Drug ingredients ##########################
        # logging.info('Mapping drug ingredient concepts')

        # # Get all active drug ingredients which have OMOP mappings to MESH
        # sql = """
        # SELECT c.concept_id, c.concept_name, c_mesh.concept_code AS mesh_code, c_mesh.concept_name AS mesh_name,
        #     c_mesh.invalid_reason
        # FROM
        # (SELECT DISTINCT concept_id FROM concept_counts) x
        # JOIN concept c ON x.concept_id = c.concept_id
        # JOIN concept_relationship cr ON c.concept_id = cr.concept_id_2
        # JOIN concept c_mesh ON cr.concept_id_1 = c_mesh.concept_id
        # --    AND cr.relationship_id = 'Maps to' -- only Maps to relationships in the COHD database
        # WHERE c.domain_id = 'drug' AND c.concept_class_id = 'ingredient'
        #     AND c_mesh.vocabulary_id = 'MeSH'
        # ORDER BY c.concept_id;
        # """
        # cur.execute(sql)
        # ingredient_concepts = cur.fetchall()

        # # Normalize with SRI Node Norm via MESH
        # # Note: multiple MESH concepts may map to the same standard OMOP concept
        # omop_concepts = defaultdict(dict)
        # omop_biolink = defaultdict(list)
        # mapped_ids = list()
        # for c in ingredient_concepts:
        #     mapped_id = 'MESH:' + c['mesh_code']
        #     omop_id = c['concept_id']
        #     omop_concepts[omop_id][mapped_id] = c
        #     omop_biolink[omop_id].append(mapped_id)
        #     mapped_ids.append(mapped_id)
        # normalized_ids = SriNodeNormalizer.get_normalized_nodes(mapped_ids)

        # for omop_id in omop_concepts:
        #     mapped_ids = omop_biolink[omop_id]
        #     best_mapping = None
        #     best_distance = 999
        #     best_string_sim = 0
        #     for mapped_id in mapped_ids:
        #         if normalized_ids[mapped_id] is None:
        #             continue

        #         biolink_norm_node = normalized_ids[mapped_id]
        #         biolink_norm_id = biolink_norm_node.normalized_identifier.id
        #         biolink_label = biolink_norm_node.normalized_identifier.label
        #         omop_label = omop_concepts[omop_id][mapped_id]['concept_name']
        #         invalid_reason = omop_concepts[omop_id][mapped_id]['invalid_reason']
        #         categories = json.dumps(biolink_norm_node.categories)
        #         provenance = f'(OMOP:{omop_id})-[OMOP Map]-({mapped_id})'
        #         distance = 1
        #         # Don't exclude invalid or obsolete MeSH mappings, but add 1 to their distance to de-prioritize them
        #         if invalid_reason is not None or 'obsolete' in biolink_label.lower():
        #             logging.debug(f'Invalid or obsolete mapping: {mapped_id} - {biolink_label}')
        #             distance += 1
        #         string_similarity = difflib.SequenceMatcher(None, omop_label.lower(), biolink_label.lower()).ratio()
        #         if mapped_id != biolink_norm_id:
        #             provenance += f'-[SRI Node Norm]-({biolink_norm_id})'
        #             distance += 1

        #         # Use the mapping with the best mapping distance & string similarity
        #         if distance < best_distance or (distance == best_distance and string_similarity > best_string_sim):
        #             best_mapping = [omop_id, biolink_norm_id, biolink_label, categories, provenance, False, distance, string_similarity]
        #             best_distance = distance
        #             best_string_sim = string_similarity

        #     if best_mapping is not None:
        #         params.extend(best_mapping)
        #         mapping_count += 1

        # ########################## Procedures ##########################
        # logging.info('Mapping procedure concepts')

        # # Note: Biolink doesn't list any prefixes in biolink:Procedure. Use vocabularies that are supported
        # # by Biolink in general (SNOMED, CPT4, MedDRA, HCPCS, and ICD9CM). Currently unsupported vocabularies
        # # include ICD10PCS and ICD9Proc
        # sql = """
        # SELECT c.concept_id, c.concept_name, c.vocabulary_id, c.concept_code, c.concept_class_id, standard_concept
        # FROM
        # (SELECT DISTINCT concept_id FROM concept_counts) x
        # JOIN concept c ON x.concept_id = c.concept_id
        # WHERE c.domain_id = 'procedure' AND c.vocabulary_id IN ('CPT4', 'HCPCS', 'ICD9CM', 'MedDRA', 'SNOMED')
        # ORDER BY c.concept_id;
        # """
        # cur.execute(sql)
        # procedure_concepts = cur.fetchall()

        # # Use the vocabulary concept codes as the Biolink IDs
        # omop_concepts = {c['concept_id']:c for c in procedure_concepts}
        # omop_biolink = {c['concept_id']:prefix_map[c['vocabulary_id']] + ':' + c['concept_code'] for c in procedure_concepts if c['vocabulary_id'] in prefix_map}

        # # Create the mappings
        # for omop_id in omop_concepts:
        #     mapped_id = omop_biolink[omop_id]
        #     biolink_label = omop_concepts[omop_id]['concept_name']
        #     categories = json.dumps(['biolink:Procedure'])
        #     provenance = f'(OMOP:{omop_id})-[OMOP Map]-({mapped_id})'
        #     distance = 1
        #     string_similarity = 1
        #     params.extend([omop_id, mapped_id, biolink_label, categories, provenance, False, distance, string_similarity])
        #     mapping_count += 1

        ########################## Update mappings ##########################
        # Make sure that the new mappings have at least 95% as many mappings as the existing mappings
        if mapping_count < (0.95 * current_count):
            status_message = f"""Current number of mapped mappings: {current_count}
            Current number of string mappings: {current_count_string}
            New mapped mappings: {mapping_count}
            Retained old mappings"""
            logging.info(status_message)
            return status_message, 200
        else:
            logging.info('Updating dbo.oard_biolink_mappings database')

            # Clear out old mappings
            sql = 'TRUNCATE TABLE dbo.oard_biolink_mappings;'
            cur.execute(sql)
            conn.commit()


            # Insert new mappings
            batch_count = 100
            start = 0
            end = start + 8*batch_count
            while (start != end):
                sql = """
                INSERT INTO dbo.oard_biolink_mappings (omop_id, biolink_id, biolink_label, categories, provenance, string_search, distance, string_similarity) VALUES
                """
                placeholders = ['(?, ?, ?, ?, ?, ?, ?, ?)'] * batch_count
                sql += ','.join(placeholders) + ';'
                cur.execute(sql, params[start:end])
                conn.commit()
                start = end
                end = min(start + 8*batch_count,len(params))
                batch_count = int((end - start)/8)

            # Multiple OMOP IDs may map to the same Biolink IDs. Try to find preferred mappings based on:
            # 1) mapping distance, 2) string similarity, 3) COHD counts
            # sql = """
            # WITH
            # -- First choose based off of mapping distance
            # dist AS (SELECT biolink_id, MIN(distance) AS distance
            #     FROM dbo.oard_biolink_mappings
            #     GROUP BY biolink_id),
            # -- Next, use string similarity
            # string_sim AS (SELECT m.biolink_id, m.distance, MAX(string_similarity) AS string_similarity
            #     FROM dbo.oard_biolink_mappings m
            #     JOIN dist ON m.biolink_id = dist.biolink_id AND m.distance = dist.distance
            #     GROUP BY biolink_id, distance),
            # UPDATE dbo.oard_biolink_mappings m
            # JOIN cohd.concept_counts cc ON m.omop_id = cc.concept_id
            # JOIN max_count x ON m.biolink_id = x.biolink_id
            #     AND m.distance = x.distance
            #     AND m.string_similarity = x.string_similarity
            #     AND cc.concept_count = x.concept_count
            # -- JOIN cohd.concept c ON m.omop_id = c.concept_id
            # --    AND x.standard_concept = c.standard_concept
            # SET preferred = true;
            # """
            # cur.execute(sql)
            # conn.commit()

        # ########################## Search drug ingredients by name ##########################
        # logging.info('Mapping drug ingredients by name')
        # # Get all active drug ingredients which aren't mapped yet
        # sql = """
        # SELECT c.concept_id, c.concept_name
        # FROM
        # (SELECT DISTINCT concept_id FROM concept_counts) x
        # JOIN concept c ON x.concept_id = c.concept_id
        # LEFT JOIN dbo.oard_biolink_mappings m ON x.concept_id = m.omop_id
        # WHERE c.domain_id = 'drug' AND c.concept_class_id = 'ingredient'
        #     AND m.omop_id IS NULL
        # ORDER BY c.concept_id;
        # """
        # cur.execute(sql)
        # missing_ingredient_concepts = cur.fetchall()

        # # First, collect responses from SRI Lookup service
        # total_errors = 0
        # max_total_errors = 10
        # max_tries = 2
        # omop_labels = dict()
        # lookup_responses = dict()
        # potential_curies = list()
        # for r in missing_ingredient_concepts:
        #     if total_errors >= max_total_errors:
        #         logging.error(f'Biolink Mapper Max Total Errors')
        #         break

        #     tries = 1
        #     # SRI Lookup service can be a little flakey, retry a couple times
        #     while tries <= max_tries:
        #         try:
        #             omop_id = r['concept_id']
        #             concept_name = r['concept_name']
        #             omop_labels[omop_id] = concept_name

        #             # Lookup
        #             j = SriNameResolution.name_lookup(concept_name)
        #             if j is None:
        #                 logging.error(f'Biolink Mapper SRI Lookup Error: {omop_id} - {concept_name}')
        #                 total_errors += 1
        #             else:
        #                 if len(j) > 0:
        #                     # Collect the responses
        #                     lookup_responses[omop_id] = j
        #                     potential_curies.extend(j.keys())
        #                     break
        #                 else:
        #                     logging.info(f'Biolink Mapper - No Match: {omop_id} - {concept_name}')
        #                     break
        #         except urllib3.exception.ConnectionError as e:
        #             total_errors += 1

        #         tries += 1

        # # Call SRI Node Normalizer to get categories for all potential CURIEs
        # potential_curies = list(set(potential_curies))
        # normalized_nodes = SriNodeNormalizer.get_normalized_nodes(potential_curies)

        # # For each search result, find the first result that is a biolink:ChemicalEntity and high string similarity
        # string_sim_criteria = 0.9
        # string_match_count = 0
        # params = list()
        # chemical_descendants = bm_toolkit.get_descendants('biolink:ChemicalEntity', reflexive=True, formatted=True)
        # for omop_id, lookup_response in lookup_responses.items():
        #     omop_label = omop_labels[omop_id].lower()
        #     # CURIEs are in order of best match, according to SRI, so use this order to find the first match
        #     for curie, labels in lookup_response.items():
        #         # Check if the categories of the CURIE include biolink:ChemicalEntity
        #         normalized_node = normalized_nodes.get(curie)
        #         if normalized_node is None:
        #             continue
        #         is_chemical_descendant = False
        #         categories = normalized_node.categories
        #         for category in categories:
        #             if category in chemical_descendants:
        #                 is_chemical_descendant = True
        #                 break
        #         if not is_chemical_descendant:
        #             continue

        #         # Check if any of the labels match well enough
        #         found_match = False
        #         for label in labels:
        #             string_similarity = difflib.SequenceMatcher(None, omop_label, label.lower()).ratio()
        #             if string_similarity > string_sim_criteria:
        #                 found_match = True
        #                 categories = json.dumps(categories)
        #                 provenance = f'(OMOP:{omop_id})-[SRI Name Resolution]-({curie})'
        #                 params.extend([omop_id, curie, label, categories, provenance, True, 99, string_similarity])
        #                 string_match_count += 1
        #                 break

        #         if found_match:
        #             break

        # # Insert new string-based mappings
        # sql = """
        # INSERT INTO dbo.oard_biolink_mappings (omop_id, biolink_id, biolink_label, categories, provenance, string_search, distance, string_similarity) VALUES
        # """
        # placeholders = ['(%s, %s, %s, %s, %s, %s, %s, %s)'] * string_match_count
        # sql += ','.join(placeholders) + ';'
        # cur.execute(sql, params)

        # # Choose the preferred mappings among the string-search results only based on string similarity
        # sql = """
        # WITH
        # -- First, get the biolink CURIEs that don't yet have a preferred mapping
        # preferred AS (SELECT DISTINCT biolink_id
        #     FROM dbo.oard_biolink_mappings
        #     WHERE preferred = 1),
        # not_preferred AS (SELECT DISTINCT m.biolink_id AS biolink_id
        #     FROM dbo.oard_biolink_mappings m
        #     LEFT JOIN preferred p ON m.biolink_id = p.biolink_id
        #     WHERE p.biolink_id IS NULL),
        # -- Next, use string similarity
        # string_sim AS (SELECT m.biolink_id, MAX(string_similarity) AS string_similarity
        #     FROM dbo.oard_biolink_mappings m
        #     JOIN not_preferred np ON m.biolink_id = np.biolink_id
        #     GROUP BY biolink_id),
        # -- Next, use max concept count from COHD data
        # max_count AS (SELECT m.biolink_id, m.string_similarity, MAX(cc.concept_count) AS concept_count
        #     FROM dbo.oard_biolink_mappings m
        #     JOIN string_sim s ON m.biolink_id = s.biolink_id
        #         AND m.string_similarity = s.string_similarity
        #     JOIN cohd.concept_counts cc ON m.omop_id = cc.concept_id
        #     GROUP BY m.biolink_id, m.string_similarity)
        # UPDATE dbo.oard_biolink_mappings m
        # JOIN cohd.concept_counts cc ON m.omop_id = cc.concept_id
        # JOIN max_count x ON m.biolink_id = x.biolink_id
        #     AND m.string_similarity = x.string_similarity
        #     AND cc.concept_count = x.concept_count
        # SET preferred = true;
        # """
        # cur.execute(sql)
        # conn.commit()

        # status_message = f"""Current number of mapped mappings: {current_count}
        #         Current number of string mappings: {current_count_string}
        #         New mapped mappings: {mapping_count}
        #         New string mappings: {string_match_count}
        #         Updated to new mappings.
        #         """
        # return status_message, 200

if __name__ == "__main__":

    myOhdsi = OhdsiManager()
    cur = myOhdsi.cursor
    conn = myOhdsi.cnxn
    build_mappings(cur, conn)