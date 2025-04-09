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
    """Insert the error details into Snowflake."""
    try:
        # Connect to Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Insert the error details into the table
        cursor.execute("""
            INSERT INTO xml_validation_errors (
                filename, validity, error_message, instance, path, llm_suggestion, datetime
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP());
        """, (filename, validity, error_msg, instance, path, llm_suggestion))

        # Commit the transaction
        conn.commit()

        print("✅ Error logged into Snowflake.")
    except Exception as e:
        print(f"Error inserting into Snowflake: {e}")
    finally:
        cursor.close()
        conn.close()


def get_xsd_files_from_stage(stage_name):
    """List and download XSD files from a Snowflake stage."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        # List files in the stage to get the XSD files
        list_query = f"LIST @{stage_name}"
        cursor.execute(list_query)
        files = cursor.fetchall()

        # Filter for XSD files
        xsd_files = [file[0] for file in files if file[0].lower().endswith('.xsd')]

        if not xsd_files:
            print(f"No XSD files found in stage {stage_name}")
            return []

        print(f"Found {len(xsd_files)} XSD files in stage {stage_name}")
        return xsd_files
    except Exception as e:
        print(f"Error listing files in stage: {e}")
    finally:
        cursor.close()
        conn.close()