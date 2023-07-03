from flask import Flask, request
from flask_cors import CORS
import openai
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
import pandas as pd 
import os 
import tensorflow as tf
import tensorflow_hub as hub
from googletrans import Translator
import base64
import numpy as np 

print(os.getcwd())
cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
model_id = "text-embedding-ada-002"
openai.api_key = open_api_key
cloud_config= {
  'secure_connect_bundle': scb_path
}
auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)
translator = Translator(service_urls=['translate.googleapis.com'])
inception_model = hub.KerasLayer("https://tfhub.dev/google/imagenet/inception_v3/feature_vector/4", trainable=False)

app = Flask(__name__)
CORS(app)

def find_nearest_neighbour(embedding,column):
    query = SimpleStatement(
        f"""
        SELECT product_id, title,description, link, imagelink, availability, price, brand, condition, producttype, saleprice
        FROM {keyspace}.{table_name}
        ORDER BY {column} ANN OF {embedding} LIMIT 5;
        """
    )    
    results = session.execute(query)
    top_5_products = results._current_rows
    response = []
    for r in top_5_products:
        response.append({
            'id': r.product_id,
            'name': r.title,
            'description': r.description,
            'link': r.link,
            'image': 'images/' + os.path.basename(r.imagelink),
            'availability': r.availability,
            'price': r.price,
            'brand': r.brand,
            'condition': r.condition,
            'productype': r.producttype,
            'saleprice': r.saleprice
        })
    print(response)
    return response 

@app.route('/similaritems_byimage', methods=['POST'])
def upload_photo():
    photo_data = request.json.get('selectedimage')
    image_data = base64.b64decode(photo_data.split(',')[1])
    image = tf.image.decode_jpeg(image_data, channels=3)
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, (299, 299))
    image = tf.expand_dims(image, axis=0)    
    embedding = inception_model(image)
    embedding = np.array(embedding[0])
    embedding_list = embedding.tolist()       
    return find_nearest_neighbour(embedding_list,'image_embedding')

@app.route('/similaritems', methods=['POST'])
def ann_similarity_search():
    #customer_query='สีที่ดีที่ละลายได้อย่างสวยงาม'
    customer_query = request.json.get('newQuestion')
    print(customer_query)        
    embedding = openai.Embedding.create(input=customer_query, model=model_id)['data'][0]['embedding']    
    response = find_nearest_neighbour(embedding,'openai_central_group_embedding')
    message_objects = []
    message_objects.append({"role":"system",
                            "content":"You're a chatbot helping customers with questions and helping them with product recommendations"})
    
    # message_objects.append({"role":"user",
    #                         "content":"Provide answers in the language of the query"})
    
    message_objects.append({"role":"user",
                            "content": customer_query})

    message_objects.append({"role":"user",
                            "content": "Please give me a detailed explanation based on your recommendations provided earlier"})

    message_objects.append({"role":"user",
                            "content": "Please be friendly and talk to me like a person, don't just give me a list of recommendations"})

    message_objects.append({"role": "assistant",
                            "content": "I found these 3 products I would recommend"})

    products_list = []

    for row in response:  
        print(row)          
        brand_dict = {'role': "assistant", "content": f"{row['name']}, {row['description']}, {row['brand']}, {row['price']}"}
        products_list.append(brand_dict)

    message_objects.extend(products_list)
    message_objects.append({"role": "assistant", "content":"Here's my summarized recommendation of products, and why it would suit you:"})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_objects
    )
    print(completion)
    human_readable_response = completion.choices[0].message['content']
    print(human_readable_response) 
    #thai=translator.translate(human_readable_response,dest='th')

    values = dict()
    values['products'] = response
    values['botresponse'] = human_readable_response
    #values['english_response'] = thai.text
    return values

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)