#!/bin/bash

AV_FILE="${1}"
DEST_FILE="${AV_FILE}.clean.nt"

echo "input file: ${AV_FILE}"

(test -n "${AV_FILE}" && test -f ${AV_FILE}) || (echo 'no input file. exiting' && exit 1)

if [ $? -gt 0 ] ; then
    exit 1;
fi;

echo "cleaning" $(cat ${AV_FILE} | wc -l)
cat ${AV_FILE} | grep -v 'terms/created\|terms/modified\|agrontology#isUsedAs\|terms/source\|agrontology#isMeansFor\|core#altLabel\|core#closeMatch\|skos-xl#Label\|agrontology#developsFrom\|agrontology#controls\|http://aims.fao.org/aos/agrontology\|skos-xl#\|core#hasTopConcept\|core#narrowMatch\|owl#deprecated\|core#notation\|void#inDataset\|core#exactMatch' > ${DEST_FILE}

echo 'cleaned to' $(cat ${DEST_FILE} | wc -l)
echo "call paster: paster --plugin=ckan -plugin=ckanext-faociok vocabulary import_agrovoc ${DEST_FILE} -c config.ini"
