from connectors.snowflake_conn import get_snowflake_connection
from typing import List

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

def prompt_correction_with_llm(instruction: str) -> str:

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        # Nettoyage du texte brut (important pour SQL)
        cleaned_instruction = instruction.replace("'", "''").replace("\n", " ").replace("\r", " ")

        # Construction du prompt pour l'agent correcteur
        prompt = (
            "You are an expert in XML correction. "
            "You will receive instructions describing an XML validation error, the cause of the issue, and how to fix it. "
            "Based on these instructions, generate a clean and precise prompt for a corrector agent to automatically apply the fix "
            "on the XML file so that it complies with the S1000D standard. "
            f"Here are the instructions: {cleaned_instruction}"
        )

        # Requête Snowflake Cortex
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            '{prompt}'
        );
        """

        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No explanation available from the LLM."
    
    except Exception as e:
        return f"Error querying Snowflake Cortex: {str(e)}"
    
    finally:
        cursor.close()
        conn.close()


def prompt_modifier_with_llm(instruction: str, xml_input: str) -> str:
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        # Nettoyage pour éviter les erreurs SQL (échappement des apostrophes, suppressions de sauts de ligne)
        cleaned_instruction = instruction.replace("'", "''").replace("\n", " ").replace("\r", " ")
        cleaned_xml_input = xml_input.replace("'", "''").replace("\n", " ").replace("\r", " ")

        # Construction du prompt
        prompt = (
            "You are an expert in XML editing and transformation, especially for technical documentation following S1000D standards. "
            "You will receive a valid XML document and a list of detailed modification instructions. "
            "Apply all the modifications as described and return the full modified XML content, properly formatted. "
            "Do not explain the changes. Just return the updated XML content. "
            f"\n\nOriginal XML:\n{cleaned_xml_input}\n\nModification Instructions:\n{cleaned_instruction}"
        )

        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            '{prompt}'
        );
        """

        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No modified XML was generated by the LLM."

    except Exception as e:
        return f"Error querying Snowflake Cortex: {str(e)}"

    finally:
        cursor.close()
        conn.close()
