# Author: Cong Liu
# Last updated: 08-24-2021

rm(list=ls())
library(data.table)
library(ggplot2)
library(dplyr)
library(tidyr)

generaateChiStat = function(no_hits, hits,total_no_hits,total_hits){
  tableForChi = matrix(c(no_hits, hits,total_no_hits,total_hits),nrow=2)
  fisherStat = fisher.test(tableForChi)
  fisherOR = fisherStat$estimate
  fisherP = fisherStat$p.value
  fisherCI_low = fisherStat$conf.int[1]
  fisherCI_high = fisherStat$conf.int[2]
  return(data.frame(fisherOR,fisherP,fisherCI_low,fisherCI_high))
}

normFreq = function(x){
  if(!is.na(x)){
    if (str_detect(x, "[0-9]+%",negate = F)){
      return(as.numeric(sub("%", "", x))/100)
    }
    if (str_detect(x,"[0-9]+/[0-9]+",negate = F)){
      return(as.numeric(str_split(x,'/')[[1]][1])/as.numeric(str_split(x,'/')[[1]][2]))
    }
  }
  return(NA)
}
  

# hit count distribution.
hitCountDf = fread("../../03-data/hpo-query/v2/query_max_row.txt")
colnames(hitCountDf) = c('hp_id','hp_name','query_string','hit_count')
hitCountDf %>% ggplot(aes(x=hit_count)) + geom_histogram()
hitCountDf %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F,)) %>%
  ggplot(aes(y=hit_count_bin)) + geom_bar() + 
  xlab("number of HPO concepts")
quantile(hitCountDf$hit_count,probs = c(0:50)/50)
# top 20 and bottom 20 HPO concepts
hitCountDf %>% arrange(-hit_count) %>% head(n=20) %>% dplyr::select(hp_id,hp_name,hit_count)
hitCountDf %>% arrange(-hit_count) %>% tail(n=20) %>% dplyr::select(hp_id,hp_name,hit_count)

# token count v.s. hit count
tokenLenDf = fread("../../03-data/raw/hpo/hp_2021_02_23.nameLength")
colnames(tokenLenDf) = c('hp_id','hp_name','token_count')
merge(hitCountDf,tokenLenDf,by=c('hp_id','hp_name')) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F,)) %>%
  ggplot(aes(x=hit_count_bin,y=token_count)) + 
  geom_violin() 

# avg string length v.s. hit count
charLenDf = fread("../../03-data/raw/hpo/hp_2021_02_23.charLength")
colnames(charLenDf) = c('hp_id','hp_name','string_length')
merge(hitCountDf,charLenDf,by=c('hp_id','hp_name')) %>% 
  left_join(tokenLenDf) %>% 
  mutate(avg_string_length = string_length/token_count) %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F,)) %>%
  ggplot(aes(x=hit_count_bin,y=avg_string_length)) +
  geom_boxplot()

# string length v.s. hit count
charLenDf = fread("../../03-data/raw/hpo/hp_2021_02_23.charLength")
colnames(charLenDf) = c('hp_id','hp_name','string_length')
merge(hitCountDf,charLenDf,by=c('hp_id','hp_name')) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F)) %>%
  ggplot(aes(x=hit_count_bin,y=string_length)) +
  geom_boxplot()

# dist to root v.s. hit count
disToRootDf = fread("../../03-data/raw/hpo/hp_2021_02_23.distanceToRoot")
colnames(disToRootDf) = c('hp_id','hp_name','dist_to_root','sub_class')
merge(hitCountDf,disToRootDf,by=c('hp_id','hp_name')) %>% 
  filter(sub_class!='ALL') %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F)) %>%
  ggplot(aes(x=hit_count_bin,y=dist_to_root)) + 
  geom_violin()

# dist to root v.s. token count
disToRootDf %>% left_join(tokenLenDf) %>%
  ggplot(aes(x=as.factor(dist_to_root),y=token_count)) + 
  geom_violin()

# token count v.s. hit_count in each dist to root
disToRootDf %>% left_join(tokenLenDf) %>% 
  filter(sub_class!='ALL') %>%
  left_join(hitCountDf) %>% 
  filter(!is.na(hit_count)) %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>%
  ggplot(aes(x=as.factor(dist_to_root),y=token_count,color=hit_count_bin)) + 
  geom_boxplot()

# subclass v.s. hit_count
subClassName = disToRootDf[,.(sub_class)] %>% unique() %>% left_join(hitCountDf[,.(hp_id,hp_name)],by=c("sub_class"='hp_id'))
merge(hitCountDf,disToRootDf,by=c('hp_id','hp_name')) %>% left_join(subClassName,by=c("sub_class"='sub_class')) %>%
  filter(hp_name.y!='ALL') %>%
  group_by(hp_name.y) %>% summarise(no_hits = sum(hit_count == 0), 
                                     hits = sum(hit_count > 0)) %>%
  gather(class, number_of_hps, no_hits:hits, factor_key=TRUE) %>%
  ggplot(aes(fill=class,y=number_of_hps,x=hp_name.y)) +
  xlab("") +
  geom_bar(position="stack", stat="identity") + coord_flip()

# pos tag v.s. hit count.
posTagDf = fread("../../03-data/raw/hpo/hp_2021_02_23.posTag")
colnames(posTagDf) = c('hp_id','hp_name','token','pos_tag')
posTagTop = posTagDf %>% group_by(pos_tag) %>% summarise(count = n()) %>% arrange(desc(count)) %>% head(n=10)
posTagDfSub = posTagDf %>% inner_join(posTagTop)
totalNonZeroHits = (hitCountDf %>% inner_join(posTagDfSub) %>% filter(hit_count > 0) %>% dim())[1]
totalZeroHits = (hitCountDf %>% inner_join(posTagDfSub) %>% filter(hit_count == 0) %>% dim())[1]
compareMatrix = hitCountDf %>% inner_join(posTagDfSub) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  group_by(pos_tag) %>% summarise(hits = sum(hit_count > 0),no_hits = sum(hit_count == 0)) %>%
  mutate(total_hits = totalNonZeroHits) %>%
  mutate(total_no_hits = totalZeroHits) %>%
  mutate(count = no_hits+hits) %>% 
  mutate(no_hits_percentage = no_hits/count)
compareMatrix %>% rowwise() %>%
  mutate(generaateChiStat(no_hits, hits,total_no_hits,total_hits)) %>%
  arrange(-fisherOR) %>%
  ggplot(aes(y=fisherOR,x=pos_tag)) +
  geom_bar(aes(y=no_hits_percentage),stat='identity') + 
  geom_text(aes(label = round(no_hits_percentage,3), y = 0.2), size = 4) + 
  geom_point(aes(y=fisherOR,x=pos_tag,size=count)) + 
  geom_pointrange(aes(ymin = fisherCI_low, ymax = fisherCI_high),position = position_dodge(.7)) +
  coord_flip()

# token freq v.s. hit count
tokenCountDf = fread("../../03-data/raw/hpo/hp_2021_02_23.tokenCount")
colnames(tokenCountDf) = c("token","count")
countDf = hitCountDf %>% 
  inner_join(posTagDfSub) %>% dplyr::select(-count) %>%
  inner_join(tokenCountDf) %>% 
  filter(!is.na(hit_count)) %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F))
countDf %>% ggplot(aes(y=count,x=pos_tag,color=hit_count_bin)) +
  geom_boxplot()


# top 100 token v.s. hit count
tokenCountDf = fread("../../03-data/raw/hpo/hp_2021_02_23.tokenCount")
colnames(tokenCountDf) = c("token","count")
# a_ranks <- rank(tokenCountDf$count, ties.method = "first")
# decile <- cut(a_ranks, quantile(a_ranks, probs=0:20/20), include.lowest=TRUE, labels=FALSE)  
countDf = tokenCountDf %>% 
  inner_join(posTagDf) %>% 
  inner_join(hitCountDf) %>% 
  filter(!is.na(hit_count))
topCountDf = countDf %>% filter(count>100)
totalNonZeroHits = (topCountDf %>% filter(hit_count > 0) %>% dim())[1]
totalZeroHits = (topCountDf %>% filter(hit_count == 0) %>% dim())[1]
compareMatrix = topCountDf %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  group_by(token) %>% summarise(hits = sum(hit_count > 0),no_hits = sum(hit_count == 0)) %>%
  mutate(total_hits = totalNonZeroHits) %>%
  mutate(total_no_hits = totalZeroHits) %>%
  mutate(count = no_hits+hits) %>% 
  mutate(no_hits_percentage = no_hits/count) %>% 
  rowwise() %>%
  mutate(generaateChiStat(no_hits, hits,total_no_hits,total_hits))
compareMatrix %>% 
  arrange(-count) %>% head(n=100) %>%
  ggplot(aes(y=log2(fisherOR),x=log2(count))) +
  geom_text(aes(label = token, y = log2(fisherOR), x = log2(count)), size = 3.5) + 
  coord_flip()
  # geom_pointrange(aes(ymin = fisherCI_low, ymax = fisherCI_high),position = position_dodge(.7)) +
  

# ontology v.s. hit count
patternDf = fread("../../03-data/raw/hpo/hp_2021_02_23.patDesign")
colnames(patternDf) = c('hp_id','hp_name','pat','ontology')
ontologyTop = patternDf %>% group_by(ontology) %>% summarise(count = n()) %>% arrange(desc(count)) %>% head(n=10)
patternDfSub = patternDf %>% inner_join(ontologyTop)
totalNonZeroHits = (hitCountDf %>% inner_join(patternDfSub) %>% filter(hit_count > 0) %>% dim())[1]
totalZeroHits = (hitCountDf %>% inner_join(patternDfSub) %>% filter(hit_count == 0) %>% dim())[1]
compareMatrix = hitCountDf %>% inner_join(patternDfSub) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  group_by(ontology) %>% summarise(hits = sum(hit_count > 0),no_hits = sum(hit_count == 0)) %>%
  mutate(total_hits = totalNonZeroHits) %>%
  mutate(total_no_hits = totalZeroHits) %>%
  mutate(count = no_hits+hits) %>% 
  mutate(no_hits_percentage = no_hits/count)
compareMatrix %>% rowwise() %>%
  mutate(generaateChiStat(no_hits, hits,total_no_hits,total_hits)) %>%
  arrange(-fisherOR) %>%
  ggplot(aes(y=fisherOR,x=ontology)) +
  geom_bar(aes(y=no_hits_percentage),stat='identity') + 
  geom_text(aes(label = round(no_hits_percentage,3), y = 0.2), size = 4) + 
  geom_point(aes(y=fisherOR,x=ontology,size=count)) + 
  geom_pointrange(aes(ymin = fisherCI_low, ymax = fisherCI_high),position = position_dodge(.7)) +
  coord_flip()

# annotation v.s hit count.
annotationDf = read.csv(file = "../../03-data/raw/hpo/phenotype.hpoa",sep = "\t")
annotationHpoDf = annotationDf %>% group_by(HPO_ID) %>% summarise(annotation_count=n())
colnames(annotationHpoDf)[1] = 'hp_id'
hitCountDf %>% left_join(annotationHpoDf) %>% 
  mutate_at('annotation_count', ~replace(., is.na(.), 0)) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  mutate(annotation_count_bin = cut(annotation_count,breaks = c(-Inf,0,5,2223),include.lowest = F)) %>% 
  ggplot(aes(y = annotation_count_bin,color = hit_count_bin)) + 
  geom_bar(aes(fill=hit_count_bin))

# evidence v.s hit count.
annotationDf = read.csv(file = "../../03-data/raw/hpo/phenotype.hpoa",sep = "\t")
colnames(annotationDf)[4] = 'hp_id'
totalNonZeroHits = (hitCountDf %>% inner_join(annotationDf) %>% filter(hit_count > 0) %>% dim())[1]
totalZeroHits = (hitCountDf %>% inner_join(annotationDf) %>% filter(hit_count == 0) %>% dim())[1]
compareMatrix = hitCountDf %>% inner_join(annotationDf) %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  group_by(Evidence) %>% summarise(hits = sum(hit_count > 0),no_hits = sum(hit_count == 0)) %>%
  mutate(total_hits = totalNonZeroHits) %>%
  mutate(total_no_hits = totalZeroHits) %>%
  mutate(count = no_hits+hits) %>% 
  mutate(no_hits_percentage = no_hits/count)
compareMatrix %>% rowwise() %>%
  mutate(generaateChiStat(no_hits, hits,total_no_hits,total_hits)) %>%
  arrange(-fisherOR) %>%
  ggplot(aes(y=fisherOR,x=Evidence)) +
  geom_bar(aes(y=no_hits_percentage),stat='identity') + 
  geom_text(aes(label = round(no_hits_percentage,3), y = 0.2), size = 4) + 
  geom_point(aes(y=fisherOR,x=Evidence,size=count)) + 
  geom_pointrange(aes(ymin = fisherCI_low, ymax = fisherCI_high),position = position_dodge(.7)) +
  geom_hline(yintercept = 1)+
  coord_flip()

# ICD mapping v.s. Hits
icd9Df = read.csv(file = "../../03-data/raw/hpo/hpo2icd/HPO_to_ICD9.txt",sep = "\t")
icd9Df = icd9Df %>% 
  mutate(hp_id = paste0('HP:',str_pad(`HPO.term.ID`,width = 7,side = 'left',pad = '0')))
icd10Df = read.csv(file = "../../03-data/raw/hpo/hpo2icd/HPO_to_ICD10.txt",sep = "\t")
icd10Df = icd10Df %>% 
  mutate(hp_id = paste0('HP:',str_pad(`HPO.term.ID`,width = 7,side = 'left',pad = '0')))
# ICD9
hitCountDf %>% 
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
  left_join(icd9Df) %>% 
  mutate(ICD9 = if_else(!is.na(`HPO.term.ID`),true = 'TRUE',false = 'FALSE')) %>%
  ggplot(aes(y = ICD9,color = hit_count_bin)) + 
  geom_bar(aes(fill=hit_count_bin))
# ICD10
hitCountDf %>% 
    mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,38000000),include.lowest = F)) %>% 
    left_join(icd10Df) %>% 
    mutate(ICD10 = if_else(!is.na(`HPO.term.ID`),true = 'TRUE',false = 'FALSE')) %>%
  ggplot(aes(y = ICD10,color = hit_count_bin)) + 
    geom_bar(aes(fill=hit_count_bin))

# freq v.s. Hits.
annotationDf = read.csv(file = "../../03-data/raw/hpo/phenotype.hpoa",sep = "\t")
colnames(annotationDf)[4] = 'hp_id'
freqCountDf = hitCountDf %>% left_join(annotationDf) %>% 
  dplyr::select(hp_id,hit_count,Frequency) %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F)) %>%
  rowwise() %>%
  mutate(freq = normFreq(Frequency))
freqCountDf %>% filter(!is.na(freq)) %>%
  group_by(hit_count_bin,hp_id) %>% summarise(avg_freq = mean(freq)) %>%
  ggplot(aes(y = avg_freq,x = hit_count_bin)) + 
  geom_boxplot() + ylim(c(0,1))

# pubmed freq v.s. Hits.
pubmedFreq = read.csv(file = "../../03-data/raw/hpo/hp_2021_02_23.pubmedCount",sep = "\t")
pubmedFreq = pubmedFreq %>% mutate(search_result = as.numeric(gsub(",","",search_result)))
hitCountDf %>% left_join(pubmedFreq) %>% 
  dplyr::select(hp_id,hp_name,hit_count,search_result) %>%
  mutate(hit_count_bin = cut(hit_count,breaks = c(-Inf,0,10,100,1000,10000,38000000),include.lowest = F)) %>%
  ggplot(aes(y =log2(search_result),x = hit_count_bin)) + 
  geom_boxplot() 