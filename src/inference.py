import hopsworks
from hsfs.feature_store import FeatureStore
from dotenv import load_dotenv
import os 
from src.paths import PARENT_DIR

load_dotenv(PARENT_DIR / '.env')

HOPSWORKS_PROJECT_NAME = os.environ['HOPSWORKS_PROJECT_NAME']
HOPSWORKS_API_KEY = os.environ['HOPSWORKS_API_KEY']
FEATURE_GROUP_NAME=os.environ['FEATURE_GROUP_NAME']
FEATURE_GROUP_VERSION=os.environ['FEATURE_GROUP_VERSION']
FEATURE_VIEW_NAME=os.environ['FEATURE_VIEW_NAME']

'''
project = hopsworks.login(
        project=HOPSWORKS_PROJECT_NAME,
        api_key_value=HOPSWORKS_API_KEY
    )
'''

import hsfs

project = hsfs.connection(
    host='c.app.hopsworks.ai',  # DNS of your Feature Store instance
    project=HOPSWORKS_PROJECT_NAME,         # Name of your Hopsworks Feature Store project
    api_key_value=HOPSWORKS_API_KEY,   # The API key to authenticate with Hopsworks
)

def get_feature_group():
    feature_store = project.get_feature_store()
    feature_group = feature_store.get_or_create_feature_group(
        name = FEATURE_GROUP_NAME,
        version=FEATURE_GROUP_VERSION,
        description="Seniment about chatgpt on twitter",
        primary_key = ['country_code'],
    )
    return feature_store, feature_group

def get_feature_view():
    feature_store, feature_group = get_feature_group()
    feature_group = feature_store.get_or_create_feature_group(
        name = FEATURE_GROUP_NAME,
        version=FEATURE_GROUP_VERSION
    )
    try:
        feature_store.create_feature_view(
            name = FEATURE_VIEW_NAME,
            version=FEATURE_GROUP_VERSION,
            query=feature_group.select_all()
        )
    except:
        print('Feature view already exists, skipping createion...')
    
    
    feature_view = feature_store.get_feature_view(
        name = FEATURE_VIEW_NAME,
        version = FEATURE_GROUP_VERSION
    )

    return feature_view

def get_latest_data():
    feature_store, feature_group = get_feature_group()
    tweet_data = feature_group.read()
    return tweet_data