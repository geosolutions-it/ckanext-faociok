#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

# remove faulty mongodb repo, we don't use it anyway
sudo rm -f /etc/apt/sources.list.d/mongodb-3.2.list
sudo add-apt-repository --remove 'http://us-central1.gce.archive.ubuntu.com/ubuntu/ main restricted'
sudo add-apt-repository --remove 'http://us-central1.gce.archive.ubuntu.com/ubuntu/ universe'
sudo add-apt-repository --remove 'http://us-central1.gce.archive.ubuntu.com/ubuntu/ multiverse'
sudo add-apt-repository 'http://archive.ubuntu.com/ubuntu/'
sudo add-apt-repository 'http://archive.ubuntu.com/ubuntu/ universe'
sudo add-apt-repository 'http://archive.ubuntu.com/ubuntu/ multiverse'
sudo apt-get -qq --fix-missing update
sudo apt-get install solr-jetty libcommons-fileupload-java


# PostGIS 2.1 already installed on Travis

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
if [ $CKANVERSION == 'master' ]
then
    echo "CKAN version: master"
else
    CKAN_TAG=$(git tag | grep ^ckan-$CKANVERSION | sort --version-sort | tail -n 1)
    git checkout $CKAN_TAG
    echo "CKAN version: ${CKAN_TAG#ckan-}"
fi

# Unpin CKAN's psycopg2 dependency get an important bugfix
# https://stackoverflow.com/questions/47044854/error-installing-psycopg2-2-6-2
sed -i '/psycopg2/c\psycopg2' requirements.txt
pip install -r requirements.txt
pip install -r dev-requirements.txt
python setup.py develop
cd -

echo
echo "Setting up Solr..."
printf "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml

# fao specific
sudo sed -i -e 's-</fields>-<field name="fao_m49_regions*" type="string" indexed="true" stored="false" multiValued="true"/>\n</fields>-g' /etc/solr/conf/schema.xml
sudo sed -i -e 's-</fields>-<field name="fao_agrovoc*" type="string" indexed="true" stored="false" multiValued="true"/>\n</fields>-g' /etc/solr/conf/schema.xml

sudo service jetty restart

echo
echo "Creating the PostgreSQL user and database..."

sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c "CREATE USER datastore_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'
sudo -u postgres psql -c 'CREATE DATABASE datastore_test WITH OWNER ckan_default;'

#echo
#echo "Setting up PostGIS on the database..."

#sudo -u postgres psql -d ckan_test -c 'CREATE EXTENSION postgis;'
#sudo -u postgres psql -d ckan_test -c 'ALTER VIEW geometry_columns OWNER TO ckan_default;'
#sudo -u postgres psql -d ckan_test -c 'ALTER TABLE spatial_ref_sys OWNER TO ckan_default;'

echo "Install other libraries required..."
sudo apt-get install python-dev libxml2-dev libxslt1-dev libgeos-c1

echo "Initialising the database..."

echo "Installing ckanext-harvest and its requirements..."
git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
python setup.py develop
pip install -r pip-requirements.txt
cd -

echo "Installing ckanext-dcat and its requirements..."
git clone https://github.com/ckan/ckanext-dcat
cd ckanext-dcat
python setup.py develop
pip install -r requirements.txt
cd -

echo "Installing ckanext-scheming and its requirements..."
git clone https://github.com/ckan/ckanext-scheming
cd ckanext-scheming
pip install -r requirements.txt
pip install -r test-requirements.txt
python setup.py develop
# paster schemingdb initdb -c ../ckan/test-core.ini
cd -


echo "Installing ckanext-ddi and its requirements..."
git clone https://github.com/geosolutions-it/ckanext-ddi
cd ckanext-ddi
git checkout dev
pip install -r requirements.txt
python setup.py develop
# paster ddidb initdb -c ../ckan/test-core.ini
cd -


echo "Installing ckanext-faociok and its requirements..."
python setup.py develop

pip install -r dev-requirements.txt
cd subdir
echo "initializing database for ckan"
paster --plugin=ckan db init -c test.ini
echo ".. ckanext-harvest "
paster --plugin=ckanext-harvest harvester initdb -c test.ini

echo ".. ckanext-faociok "
paster --plugin=ckanext-faociok vocabulary initdb -c test.ini 
paster --plugin=ckanext-faociok vocabulary load datatype ../files/faociok.datatype.csv  -c test.ini
paster --plugin=ckanext-faociok vocabulary import_m49 ../files/M49_Codes.xlsx -c test.ini

# ckan/test-core.ini

echo "travis-build.bash is done."
