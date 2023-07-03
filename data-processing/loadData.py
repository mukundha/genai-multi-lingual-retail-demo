import cohere
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
from sentence_transformers import SentenceTransformer

cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
data_file = os.environ.get('data_file')
coherekey = os.environ.get('coherekey')
embedding_model = os.environ.get('embedding_model')

inception_model = hub.KerasLayer("https://tfhub.dev/google/imagenet/inception_v3/feature_vector/4", trainable=False)
print('Loaded Inception model')
paraphrase_ml_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
print('Loaded Paraphrase model')

openai.api_key = open_api_key
openai_modelid = "text-embedding-ada-002"

cohere_model_id='embed-multilingual-v2.0'
co = cohere.Client(coherekey)
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
#print(products_list)

def get_embeddings(text):
  if embedding_model == 'cohere_embedding':
    return co.embed(texts=full_chunk, model=cohere_model_id).embeddings[0]   
  elif embedding_model == 'paraphraseml_embedding':
    return paraphrase_ml_model.encode(text)[0].tolist()
  elif embedding_model == 'openai_embedding':
    return openai.Embedding.create(input=text, model=openai_modelid)['data'][0]['embedding']
  
def get_image_embeddings(file):
  try:
    image = tf.io.read_file(file)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, (299, 299))
    image = tf.expand_dims(image, axis=0)    
    embedding = inception_model(image)
    embedding = np.array(embedding[0])
    embedding_list = embedding.tolist()
    return embedding_list
  except:
    return None

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
    image_file = 'images/' + os.path.basename(row.imagelink)
    image_embeddings = get_image_embeddings(image_file)
    query = SimpleStatement(
                f"""
                INSERT INTO {keyspace}.{table_name}
                (product_id, chunk_id, title, description, link, imagelink,availability, price, brand, condition,producttype,saleprice,{embedding_model},image_embedding)
                VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s)
                """
            )    
    session.execute(query, (row.id, chunk_id, row.title, row.description,row.link,row.imagelink,row.availability,  pricevalue ,row.brand,row.condition,row.producttype,row.sale_price, embeddings, image_embeddings))
    print(row.name)