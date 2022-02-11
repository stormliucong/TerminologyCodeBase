from lxml import etree
import re
import pandas as pd
import pickle

with open('/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/ORPHAnomenclature_en_2021_02_23.names','w') as f:
    xml_path = '/phi_home/cl3720/phi/EHR-based-HPO-freq-resource/03-data/raw/ORPHAnomenclature_en_2021_02_23.xml'
    tree = etree.parse(xml_path)
    root = tree.getroot()
    for disorderlist in root.findall('DisorderList'):
        for disorder in disorderlist:
            orphaCode = 'ORPHA:' + disorder.find('OrphaCode').text
            name = disorder.find('Name')
            f.write(orphaCode + '\t' + name.text + '\n')
            synonymList = disorder.find('SynonymList')
            for syn in synonymList.findall('Synonym'):
                f.write(orphaCode + '\t' + syn.text + '\n')
