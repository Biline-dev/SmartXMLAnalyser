import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Known schemas
SCHEMA_URL_MAP = {
    "http://www.s1000d.org/S1000D_4-2/xml_schema_flat/proced.xsd": "data/xml_schema_flat/proced.xsd",
    # Add more if needed
}

# Snowflake credentials
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USERNAME"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE")
}
