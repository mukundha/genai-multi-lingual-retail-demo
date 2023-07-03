import openai
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
import tensorflow as tf
import tensorflow_hub as hub
import pandas as pd 
import numpy as np
import os 

cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
data_file = os.environ.get('data_file')
EMBEDDING_MODEL = 'OPENAI'
openai.api_key = open_api_key

def get_embeddings(text):
  if EMBEDDING_MODEL == 'OPENAI':
    return openai.Embedding.create(input=text, model="text-embedding-ada-002")['data'][0]['embedding']


cloud_config= {
  'secure_connect_bundle': scb_path
}

auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)

df = pd.read_csv(data_file)

products_list = df.replace(np.nan, '', regex=True)
print('Products Loaded')

for id, row in products_list.iterrows():    
  # Create Embedding for each conversation row, save them to the database
  text_chunk_length = 2500
  text_content = f"{row.description} {row.title} {row.brand}"
  text_chunks = [text_content[i:i + text_chunk_length] for i in range(0, len(text_content), text_chunk_length)]
  for chunk_id, chunk in enumerate(text_chunks):
    pricevalue = row.price if isinstance(row.price, str) else ""
    full_chunk = []
    full_chunk.append(f"{chunk} price: {pricevalue}")    
    embeddings = get_embeddings(full_chunk)    
    query = f"""
                UPDATE {keyspace}.{table_name}
                SET openai_embedding = {embeddings}
                WHERE product_id = {row.id} and chunk_id = {chunk_id}
                """                
    session.execute(query)
    print(row.name, row.id)