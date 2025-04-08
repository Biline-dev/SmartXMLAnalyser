from connectors.snowflake_conn import get_snowflake_connection

def explain_error_with_llm(error_msg: str) -> str:
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    cleaned_error = error_msg.replace("'", "''").replace("\n", " ").replace("\r", " ")
    prompt = f"XML validation error: {cleaned_error}"

    sql = """
    SELECT SNOWFLAKE.cortex.COMPLETE(
        'mistral-large',
        CONCAT('You are an expert in XML schema validation. Help fix this error clearly and concisely: ', 
               '{}', 
               '\\n\\nPlease explain: 1) What is causing this error, 2) How to fix it, 3) Example of correct XML structure')
    )
    """.format(prompt)

    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No explanation available from the LLM."
    except Exception as e:
        return f"Error querying Snowflake Cortex: {str(e)}"
    finally:
        cursor.close()
        conn.close()
