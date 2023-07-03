CREATE TABLE IF NOT EXISTS {keyspace}.{table_name}
(product_id int,
 chunk_id int,
 title text,
 description text,
 link text,
 imagelink text,
 availability text,   
 price text,
 brand text,
 condition text,
 producttype text,
 saleprice text,                                              
 cohere_embedding vector<float, 768>,
 use_embedding vector<float, 384>,
 paraphraseml_embedding vector<float,768>,
 openai_embedding vector<float, 1536>
 image_embedding vector<FLOAT,2048>,
 PRIMARY KEY (product_id,chunk_id))

CREATE CUSTOM INDEX IF NOT EXISTS cohere_embedding_index ON {keyspace}.{table_name} (cohere_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
CREATE CUSTOM INDEX IF NOT EXISTS use_embedding_index ON {keyspace}.{table_name} (use_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
CREATE CUSTOM INDEX IF NOT EXISTS paraphraseml_embedding_index ON {keyspace}.{table_name} (paraphraseml_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
CREATE CUSTOM INDEX IF NOT EXISTS openai_embedding_index ON {keyspace}.{table_name} (openai_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
CREATE CUSTOM INDEX IF NOT EXISTS image_embedding_index ON {keyspace}.{table_name} (image_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
CREATE CUSTOM INDEX IF NOT EXISTS title_index ON {keyspace}.{table_name} (title) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
