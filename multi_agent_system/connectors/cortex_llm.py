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



from lxml.etree import _ElementTree
from lxml import etree


def correct_with_llm(tree: _ElementTree, instruction: str, xpaths: list) -> str:
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    
    # Process each XPath in the list
    for xpath in xpaths:
        elements = tree.xpath(xpath)
        
        if not elements:
            print(f"Warning: No elements found for XPath: {xpath}. Skipping.")
            continue
            
        target_elem = elements[0]
        target_xml = etree.tostring(target_elem, pretty_print=True).decode()
        sanitized_instruction = instruction.replace("'", "''").replace("\n", " ").replace("\r", " ")
        
        prompt = (
            f"Instruction: {sanitized_instruction}\n\n"
            f"Fragment to correct:\n{target_xml}"
        )
        
        sql = """
        SELECT SNOWFLAKE.cortex.COMPLETE(
            'mistral-large',
            CONCAT('You are an expert in XML schema correction.  Based on the following instruction', 
                'generate the corrected version of the given XML fragment.:',
                '{}',
                'return the corrected XML fragment (no explanations).\n\n')
        )
        """.format(prompt)
        
        cursor.execute(sql)
        result = cursor.fetchone()
        llm_output = result[0] if result and result[0] else None
        print(llm_output)
        if not llm_output:
            print(f"Warning: LLM returned no modification for XPath: {xpath}. Skipping.")
            continue
            
        
        new_elem = etree.fromstring(llm_output)
        parent = target_elem.getparent()
        if parent is not None:
            parent.replace(target_elem, new_elem)
        else:
            print(f"Warning: Could not find parent for element at XPath: {xpath}. Skipping.")
        
    
    # Return the final modified XML
    return etree.tostring(tree, pretty_print=True, encoding="unicode")



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