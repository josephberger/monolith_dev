import os
from decouple import config as envconf
import logging
import importlib

basedir = os.path.abspath(os.path.dirname(__file__))
#logging configuration
# logging.basicConfig(filename="var/log/system.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
#                     datefmt='%Y-%m-%d %H:%M:%S')
#APP CONFIGS
class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    ELASTIC_HOST = envconf("ELASTIC_HOST", default="localhost", cast=str)
    ELASTIC_PORT = envconf("ELASTIC_PORT", default="9200", cast=int)
    ENDPOINT_INDEX = envconf("ENDPOINT_INDEX", default="endpoints", cast=str)
    EP_DETAILS_INDEX = envconf("EP_DETAILS_INDEX", default="endpoints", cast=str)
    NMAP_INDEX = envconf("NMAP_INDEX", default="nmap", cast=str)
    VLAN_INDEX = envconf("VLAN_INDEX", default="vlans", cast=str)
    INTERFACE_INDEX = envconf("INTERFACE_INDEX", default="interfaces", cast=str)
    GATEWAY_INDEX = envconf("GATEWAY_INDEX", default="interfaces", cast=str)
    ZONE_INDEX = envconf("ZONE_INDEX", default="zones", cast=str)
    REDIS_HOST = envconf("REDIS_HOST", default="localhost", cast=str)
    REDIS_PORT = envconf("REDIS_PORT", default="6379", cast=int)
    CREDENTIALS = envconf("CREDENTIALS", default=".credentials.yaml", cast=str)
    NMAP_ENABLED = envconf("NMAP_ENABLED", default="true", cast=bool)
    PLUGIN_MODS = ['cisco_ios', 'paloalto_panos']
    PLUGINS = {}

    for sd in PLUGIN_MODS:
        try:
            PLUGINS[sd] = importlib.import_module("plugins." + sd)
        except:
            pass
