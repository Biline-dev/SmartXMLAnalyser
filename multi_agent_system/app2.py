import streamlit as st
import os
import tempfile
import shutil
from utils.xml_utils import extract_instructions_from_file
from connectors.snowflake_conn import get_snowflake_connection
from agent_corrector import corrector_agent
from agent_validator import agent_validator
from agent_modifier import agent_modifier

# Function imports from the original code
def call_corrector_agent(xml_file_path, suggestion, xpath):
    st.text("🛠️ Calling corrector agent")
    xml_file_correct_path = corrector_agent(xml_file_path, suggestion, xpath)
    return xml_file_correct_path

def call_modifier_agent(xml_file_path, instructions):
    st.text("📝 Calling modifier agent")
    agent_modifier(xml_file_path, instructions)
    return xml_file_path

def orchestrator_llm(status, suggestions, instructions, xml_file_path, xpath, has_been_modified):
    # Clean inputs
    status_clean = status.replace("'", "''").replace("\n", " ").replace("\r", " ") if status else ""
    suggestions_clean = suggestions.replace("'", "''").replace("\n", " ").replace("\r", " ") if suggestions else ""

    prompt = f"""
    Vous êtes un agent orchestrateur responsable de vérifier, corriger et modifier un fichier XML.

    Statut actuel du fichier XML : {status_clean}
    Le fichier a-t-il déjà été modifié ? : {"oui" if has_been_modified else "non"}

    Voici les suggestions de correction (si nécessaire) : {suggestions_clean}

    Règles :
    - Si le fichier nest pas valide, répondez "correction".
    - Si le fichier est valide mais na pas encore été modifié, répondez "modification".
    - Si le fichier est modifié mais na pas encore été validé, répondez "correction".
    - Si le fichier est valide et a déjà été modifié, répondez "stop".
    - La validation doit se faire après chaque modification et correction.

    Répondez uniquement par : "correction", "modification" ou "stop".
    """

    try:
        with st.spinner("Connecting to Snowflake and processing..."):
            conn = get_snowflake_connection()
            cursor = conn.cursor()

            sql = """
            SELECT SNOWFLAKE.cortex.COMPLETE(
                'claude-3-5-sonnet',
                '{}'
            )
            """.format(prompt)

            cursor.execute(sql)
            result = cursor.fetchone()

            if result and result[0]:
                response = result[0]
                decision = response.strip().lower().split()[0]
                st.text(f"🧠 Decision from orchestrator agent: {decision}")

                if decision == "correction":
                    st.text("❌ Correction required.")
                    xml_file_path = call_corrector_agent(xml_file_path, suggestions, xpath)
                elif decision == "modification":
                    st.text("✅ Modification required.")
                    xml_file_path = call_modifier_agent(xml_file_path, instructions)
                elif decision == "stop":
                    st.text("🛑 File is valid and has been modified. Stopping pipeline.")
                else:
                    raise ValueError(f"Unexpected decision from Mistral: {decision}")

                return xml_file_path, decision
            else:
                raise ValueError("No response received from Mistral")

    except Exception as e:
        st.error(f"Error when calling Mistral: {e}")
        import traceback
        st.code(traceback.format_exc())
        raise RuntimeError(f"Orchestrator agent failed: {str(e)}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

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
    
    # Initialize session state for active tab tracking
    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = 'Text Instructions'
    
    # Create tabs for different input methods with unique keys
    tab1, tab2 = st.tabs(["Text Instructions", "Instruction File"])
    
    # Track which tab is active
    with tab1:
        st.session_state['active_tab'] = 'Text Instructions'
        instructions_text = st.text_area(
            "Enter your modification instructions",
            height=200,
            placeholder="Example: Add a new step with title 'Pre-Operational Checks' at the beginning...",
            key="text_instructions_area"
        )
        
    with tab2:
        st.session_state['active_tab'] = 'Instruction File'
        instruction_file = st.file_uploader(
            "Upload instruction file",
            type=["txt"],
            key="instruction_file_uploader"
        )
    
    # XML file upload with unique key
    xml_file = st.file_uploader(
        "Upload XML file",
        type=["xml", "XML"],
        key="xml_file_uploader"
    )
    
    # Get instructions based on active tab
    instructions = ""
    if st.session_state['active_tab'] == 'Text Instructions':
        instructions = instructions_text
    else:
        if instruction_file:
            # Read instructions from file
            instructions = instruction_file.getvalue().decode("utf-8")
    
    # Process button with unique key
    process_clicked = st.button("Process File", key="process_button")
    
    if process_clicked and xml_file:
        if not instructions:
            st.error("Please provide instructions through text or file upload")
        else:
            # Create a temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the uploaded file to the temp directory
                temp_file_path = os.path.join(temp_dir, xml_file.name)
                with open(temp_file_path, 'wb') as f:
                    f.write(xml_file.getvalue())
                
                # Process the file
                with st.spinner("Processing file..."):
                    try:
                        processed_file_path = process_file(temp_file_path, instructions)
                        
                        # Check if the file exists
                        if os.path.exists(processed_file_path):
                            # Prepare for download
                            with open(processed_file_path, 'rb') as f:
                                file_content = f.read()
                            
                            st.success("File processed successfully!")
                            
                            # Provide download button
                            output_filename = "processed_" + os.path.basename(processed_file_path)
                            st.download_button(
                                label="Download Processed File",
                                data=file_content,
                                file_name=output_filename,
                                mime="application/xml",
                                key="download_button"
                            )
                        else:
                            st.error(f"Could not find processed file at: {processed_file_path}")
                    except Exception as e:
                        st.error(f"Error during processing: {str(e)}")
    elif process_clicked and not xml_file:
        st.warning("Please upload an XML file")
    
    # Add usage information
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