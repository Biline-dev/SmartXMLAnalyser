from connectors.snowflake_conn import get_snowflake_connection

def explain_error_with_llm(error_msg: str) -> str:
    """Use direct Snowflake connection to explain the error."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    
    # Properly escape the error message for SQL
    cleaned_error = error_msg.replace("'", "''").replace("\n", " ").replace("\r", " ")
    
    # Define the prompt
    prompt = f"XML validation error: {cleaned_error}"
    
    # Call Snowflake COMPLETE function directly, following the example pattern
    sql = """
    SELECT SNOWFLAKE.cortex.COMPLETE(
        'mistral-large',
        CONCAT('You are an expert in XML schema validation. Give instruction to correct each error in the xml code: ', 
               '{}', 
               '\\n\\nPlease explain: 1) What is causing this error,  2) How to fix it, 3) Example of correct XML structure')
    )
    """.format(prompt)
    
    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return "No explanation available from the LLM."
    except Exception as e:
        return f"Error querying Snowflake Cortex: {str(e)}"
    finally:
        cursor.close()
        conn.close()


