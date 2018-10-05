from db import models as modelos
from django.db import models
import datetime
import os
import requests
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files import File
import time
from urllib.parse import urlparse
import traceback
from django.conf import settings
import json
import urllib3
from urllib3.util import Retry
from urllib3 import PoolManager
import pickle
urllib3.disable_warnings()
from google.cloud import translate
from .tasks import request_from_thingi, get_thing_categories_list, download_file
from thingiverse.models import ObjetoThingi

def add_objects(max_things,start_page=0):
    #Funcion para popular la base de datos
    thing_counter = 0
    page_counter = start_page
    while thing_counter < max_things:
        page_counter += 1
        r = request_from_thingi('/popular',False,'&page={}'.format(page_counter))
        for item in r:
            try:
                ObjetoThingi.objects.create_object(external_id=item['id'])
                thing_counter += 1
            except:
                traceback.print_exc()
                time.sleep(2)
                print('Error al agregar objeto: {}'.format(item['id']))
        print('Contador: {}'.format(thing_counter))

def import_from_thingiverse_parser():
    '''
    A partir de un BufferedReader de un archivo de pickle, importa las things
    '''
    with open('things_ids_complete.db','rb') as file:
        base = pickle.load(file)
    for thing in base:
        try:
            ObjetoThingi.objects.create_object(external_id=thing['thing_id'],file_list = thing['thing_files_id'], origin='human')
        except:
            traceback.print_exc()
            time.sleep(2)
            print('Error al agregar objeto: {}'.format(thing['thing_id']))




'''
from db.tools.import_from_thingi import *
from db.models import *
import pickle
with open('things_ids_complete.db','rb') as base:
    import_from_thingiverse_parser(base)
'''
