#!/usr/bin/env bash
rm -r db/migrations thingiverse/migrations vision/migrations slaicer/migrations photogrammetry/migrations media tmp
mkdir media tmp
mkdir media/slaicer
mkdir media/slaicer/configuration_files media/slaicer/plots media/slaicer/geometry media/slaicer/gcode
mkdir media/images media/renders media/sfb media/stl
mkdir media/images/plots
mkdir media/images/visionapi

chmod 777 -R media tmp
#PSQL DB preparation
sudo -u postgres -H -- psql -c "DROP DATABASE dbapi"
sudo -u postgres -H -- psql -c "CREATE USER dbapi WITH PASSWORD '***REMOVED***'"
sudo -u postgres -H -- psql -c "DROP DATABASE dbapi"
sudo -u postgres -H -- psql -c "CREATE DATABASE dbapi"
sudo -u postgres -H -- psql -c "ALTER ROLE dbapi SET client_encoding TO 'utf8'"
sudo -u postgres -H -- psql -c "ALTER ROLE dbapi SET default_transaction_isolation TO 'read committed'"
sudo -u postgres -H -- psql -c "ALTER ROLE dbapi SET timezone TO 'UTC'"
sudo -u postgres -H -- psql -c "GRANT ALL PRIVILEGES ON DATABASE dbapi TO dbapi"
#DB population
python manage.py makemigrations db
python manage.py makemigrations photogrammetry
python manage.py makemigrations thingiverse
python manage.py makemigrations vision
python manage.py makemigrations slaicer
python manage.py migrate
python populate.py
