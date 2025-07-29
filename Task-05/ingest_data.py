# ingest_data.py

import os
import boto3
import pandas as pd
from sqlalchemy import create_engine
from io import StringIO
import logging

# Configure logging to show info-level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration will be loaded from Environment Variables ---
S3_BUCKET = os.getenv('S3_BUCKET')
S3_KEY = os.getenv('S3_KEY')
RDS_ENDPOINT = os.getenv('RDS_ENDPOINT')
RDS_USER = os.getenv('RDS_USER')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')
RDS_TABLE_NAME = os.getenv('RDS_TABLE_NAME')
GLUE_DB_NAME = os.getenv('GLUE_DB_NAME')
GLUE_TABLE_NAME = os.getenv('GLUE_TABLE_NAME')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

def get_s3_data():
    """Reads a CSV file from S3 into a pandas DataFrame."""
    try:
        logging.info(f"Reading '{S3_KEY}' from bucket '{S3_BUCKET}'...")
        s3_client = boto3.client('s3')
        # Get the object from S3
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        # Read the content of the file
        csv_content = response['Body'].read().decode('utf-8')
        # Use pandas to read the CSV content into a DataFrame
        df = pd.read_csv(StringIO(csv_content))
        logging.info("Successfully read data from S3 into a DataFrame.")
        return df
    except Exception as e:
        logging.error(f"Failed to read data from S3: {e}")
        return None

def push_to_rds(df):
    """Pushes a DataFrame to an RDS MySQL database."""
    try:
        logging.info(f"Attempting to push data to RDS table '{RDS_TABLE_NAME}'...")
        # Create the database connection string
        conn_string = f"mysql+pymysql://{RDS_USER}:{RDS_PASSWORD}@{RDS_ENDPOINT}/{RDS_DB_NAME}"
        engine = create_engine(conn_string)
        
        # Push the DataFrame to the SQL table
        # if_exists='replace' will drop the table first and then create a new one
        df.to_sql(RDS_TABLE_NAME, engine, if_exists='replace', index=False)
        
        logging.info(f"Successfully pushed {len(df)} rows to RDS table '{RDS_TABLE_NAME}'.")
        return True
    except Exception as e:
        logging.warning(f"Failed to push data to RDS. This could be due to an unavailable DB or wrong credentials.")
        logging.warning(f"Error details: {e}")
        return False

def fallback_to_glue(df):
    """Creates a table in the AWS Glue Data Catalog as a fallback."""
    try:
        logging.info(f"Fallback initiated. Registering dataset in AWS Glue as '{GLUE_TABLE_NAME}'...")
        glue_client = boto3.client('glue', region_name=AWS_REGION)
        
        # Ensure the Glue Database exists, create if not
        try:
            glue_client.create_database(DatabaseInput={'Name': GLUE_DB_NAME})
            logging.info(f"Created Glue database: {GLUE_DB_NAME}")
        except glue_client.exceptions.AlreadyExistsException:
            logging.info(f"Glue database '{GLUE_DB_NAME}' already exists.")
            
        # Define the Glue table schema by converting pandas dtypes to Glue types
        column_definitions = []
        for col, dtype in df.dtypes.items():
            if 'int' in str(dtype):
                glue_type = 'bigint'
            elif 'float' in str(dtype):
                glue_type = 'double'
            elif 'datetime' in str(dtype):
                glue_type = 'timestamp'
            else:
                glue_type = 'string'
            column_definitions.append({'Name': col, 'Type': glue_type})

        # The S3 location for Glue should point to the folder containing the file(s)
        s3_location = f"s3://{S3_BUCKET}/"
        
        # Create or update the Glue table
        # Using a try-except block to handle table updates
        try:
            glue_client.delete_table(DatabaseName=GLUE_DB_NAME, Name=GLUE_TABLE_NAME)
            logging.info(f"Deleted existing Glue table '{GLUE_TABLE_NAME}' to update it.")
        except glue_client.exceptions.EntityNotFoundException:
            pass # Table didn't exist, which is fine

        glue_client.create_table(
            DatabaseName=GLUE_DB_NAME,
            TableInput={
                'Name': GLUE_TABLE_NAME,
                'Description': 'Table created via automated fallback process.',
                'StorageDescriptor': {
                    'Columns': column_definitions,
                    'Location': s3_location,
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                        'Parameters': {'field.delim': ','}
                    },
                },
                'TableType': 'EXTERNAL_TABLE',
                'Parameters': {
                    'skip.header.line.count': '1'
                }
            }
        )
        logging.info(f"Successfully created/updated Glue table: {GLUE_TABLE_NAME}")
    except Exception as e:
        logging.error(f"Failed to execute Glue fallback operation: {e}")

if __name__ == "__main__":
    dataframe = get_s3_data()
    
    if dataframe is not None:
        # Try to push to RDS first
        if not push_to_rds(dataframe):
            # If RDS push fails, execute the fallback to Glue
            fallback_to_glue(dataframe)

