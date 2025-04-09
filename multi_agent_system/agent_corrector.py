import os
from connectors.cortex_llm import correct_with_llm
from lxml import etree

from dotenv import load_dotenv  

load_dotenv()

def handle_xml_correction(xml_file: str, instruction: str = None, xpath: list = None) -> dict:
    """
    Corrige un fichier XML en utilisant un modèle de langage et enregistre le résultat.
    
    Args:
        xml_file (str): Chemin vers le fichier XML à corriger
        instruction (str, optional): Instructions pour la correction
        xpath (str, optional): Expression XPath indiquant la partie à corriger
        
    Returns:
        dict: Dictionnaire contenant le statut de l'opération et des informations supplémentaires
    """
    
    if not xml_file:
        return {"status": "error", "message": "Chemin du fichier XML non spécifié"}
        
    try:
        # Génération du nom du fichier de sortie
        tree = etree.parse(xml_file)
        output_filename = f"corrected_files/{os.path.basename(xml_file)}"
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        # Correction du XML avec le modèle de langage
        corrected_content = correct_with_llm(tree, instruction, xpath)
        
        # Enregistrement du résultat
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(corrected_content)
            
        return {
            "status": "success", 
            "message": f"Fichier corrigé et enregistré sous {output_filename}",
            "output_path": output_filename
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Erreur lors de la correction: {str(e)}"
        }
    
def corrector_agent(xml_file, instruction, xpath):
    #xpath = ["/dmodule/identAndStatusSection/dmAddress/dmIdent/dmCode"]
    result = handle_xml_correction(xml_file=xml_file, instruction=instruction, xpath=xpath)
    if result["status"] == "success":
        print(result["message"])
        return result['output_path']
    else:
        print(f"Échec: {result['message']}")
