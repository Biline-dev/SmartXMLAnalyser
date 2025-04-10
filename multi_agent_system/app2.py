import streamlit as st
import os
import tempfile
import shutil
from utils.xml_utils import extract_instructions_from_file
from connectors.snowflake_conn import get_snowflake_connection
from agent_corrector import corrector_agent
from agent_validator import agent_validator
from agent_modifier import agent_modifier
from orchestrator import orchestrator_llm

# Function imports from the original code
def call_corrector_agent(xml_file_path, suggestion, xpath):
    st.text("🛠️ Calling corrector agent")
    xml_file_correct_path = corrector_agent(xml_file_path, suggestion, xpath)
    return xml_file_correct_path

def call_modifier_agent(xml_file_path, instructions):
    st.text("📝 Calling modifier agent")
    agent_modifier(xml_file_path, instructions)
    return xml_file_path

def process_file(file_path, instructions):
    """Process the uploaded file with the given instructions"""
    should_continue = True
    has_been_modified = False
    
    # Create a progress tracker
    progress_bar = st.progress(0)
    status_message = st.empty()
    
    iteration = 0
    max_iterations = 10  # Safety limit
    
    while should_continue and iteration < max_iterations:
        iteration += 1
        progress = min(0.1 * iteration, 0.9)  # Cap at 90% until complete
        progress_bar.progress(progress)
        
        status_message.text(f"Iteration {iteration}: Validating file...")
        status, suggestions, xpath = agent_validator(file_path)
        print("instructions------->", instructions)
        status_message.text(f"Iteration {iteration}: Orchestrating next action...")
        file_path, decision = orchestrator_llm(
            status, suggestions, instructions, file_path, xpath, has_been_modified
        )
        
        if decision == "modification":
            has_been_modified = True
            status_message.text(f"Iteration {iteration}: File modified")
        elif decision == "stop":
            should_continue = False
            status_message.text("Processing complete!")
    
    # Complete the progress bar
    progress_bar.progress(1.0)
    
    if iteration >= max_iterations and should_continue:
        st.warning("Reached maximum iterations. Process may not be complete.")
    
    return file_path

def main():
    st.title("XML File Processor")
    st.subheader("Upload, Process, and Download XML Files")

    # Exemple de prompt utilisé comme placeholder
    example_prompt = """
At the very beginning of the main procedure, add a new step that acts as a chapter header. This step should include a title with the text 'Pre-Operational Checks.'

As the first instruction within the 'Pre-Operational Checks' chapter, add a substep with a description: 'Inspect the brake lever for signs of wear or corrosion.'

As the second instruction within the 'Pre-Operational Checks' chapter, add a substep with a description: 'Ensure the hydraulic fluid is at the recommended level.'

Finally, as the third instruction within the 'Pre-Operational Checks' chapter, add a substep with a description: 'Verify that all mounting bolts are properly secured.'
""".strip()

    # Onglets pour les instructions
    tab1, tab2 = st.tabs(["Text Instructions", "Instruction File"])

    with tab1:
        instructions_text = st.text_area(
            "Enter your modification instructions",
            height=200,
            placeholder=example_prompt,
            key="text_instructions_area"
        )

    with tab2:
        instruction_file = st.file_uploader(
            "Upload instruction file",
            type=["txt"],
            key="instruction_file_uploader"
        )

    # Upload du fichier XML
    xml_file = st.file_uploader(
        "Upload XML file",
        type=["xml", "XML"],
        key="xml_file_uploader"
    )

    # Récupération des instructions
    instructions = ""
    if instructions_text.strip():  # Priorité au champ texte s'il est rempli
        instructions = instructions_text.strip()
    elif instruction_file:
        instructions = instruction_file.getvalue().decode("utf-8").strip()

    # Zone de prévisualisation des instructions (pour debug ou UX)
    if instructions:
        st.text_area("📄 Instructions Preview", value=instructions, height=150, disabled=True)

    # Bouton de traitement
    process_clicked = st.button("Process File", key="process_button")

    if process_clicked and xml_file:
        if not instructions:
            st.error("Please provide instructions through text or file upload")
        else:
            # Création d'un répertoire temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, xml_file.name)
                with open(temp_file_path, 'wb') as f:
                    f.write(xml_file.getvalue())

                # Traitement du fichier
                with st.spinner("Processing file..."):
                    try:
                        processed_file_path = process_file(temp_file_path, instructions)

                        if os.path.exists(processed_file_path):
                            with open(processed_file_path, 'rb') as f:
                                file_content = f.read()

                            st.success("File processed successfully!")

                            st.download_button(
                                label="Download Processed File",
                                data=file_content,
                                file_name="processed_" + os.path.basename(processed_file_path),
                                mime="application/xml",
                                key="download_button"
                            )
                        else:
                            st.error(f"Could not find processed file at: {processed_file_path}")
                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")

    elif process_clicked and not xml_file:
        st.warning("Please upload an XML file")

    # Guide d'utilisation
    st.markdown("---")
    st.subheader("How to use this app")
    st.markdown("""
    1. Upload your XML file using the file uploader  
    2. Enter instructions for modification either as text or via an instruction file  
    3. Click 'Process File' to start the processing  
    4. Once complete, download your processed file  
    """)

if __name__ == "__main__":
    main()
