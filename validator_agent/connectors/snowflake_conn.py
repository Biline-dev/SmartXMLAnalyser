import snowflake.connector
from config import SNOWFLAKE_CONFIG

def get_snowflake_connection():
    return snowflake.connector.connect(
        account=SNOWFLAKE_CONFIG["account"],
        user=SNOWFLAKE_CONFIG["user"],
        password=SNOWFLAKE_CONFIG["password"],
        database=SNOWFLAKE_CONFIG["database"],
        schema=SNOWFLAKE_CONFIG["schema"],
        role=SNOWFLAKE_CONFIG["role"],
        warehouse=SNOWFLAKE_CONFIG["warehouse"]
    )

def insert_error_to_snowflake(filename, validity, error_msg, instance, path, llm_suggestion):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO xml_validation_errors (
                filename, validity, error_message, instance, path, llm_suggestion, datetime
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP());
        """, (filename, validity, error_msg, instance, path, llm_suggestion))

        conn.commit()
        print("✅ Error logged into Snowflake.")
    except Exception as e:
        print(f" Error inserting into Snowflake: {e}")
    finally:
        cursor.close()
        conn.close()
