from connectors.snowflake_conn import get_snowflake_connection
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