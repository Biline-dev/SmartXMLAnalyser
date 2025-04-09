l'ochestrateur verifie la fiabilité avec les input gurdrails si lin'struction est conforme à 




<p align="center">
   <img src="https://github.com/Biline-dev/SmartXMLAnalyser/raw/main/logo.png" alt="Logo" />
   
</p>The goal of the hackathon is to push the boundaries of GenAI solutions by tackling challenging use cases and complex problems.


## Table of Contents 📚
- [Project Scope](#project-scope)
- [Architecture](#architecture)
- [Experiment](#experiment)
- [User Interface](#user-interface)
- [How to Run](#how-to-run)
- [Challenges Encountered](#challenges-encountered)
- [Next Steps](#next-steps)

## **Project Scope**
Imagine having to manually update and validate an XML document with hundreds of pages, it’s time-consuming and error-prone.

We chose to work on the Accenture project because we recognized the strong potential for real-world implementation of intelligent systems like the XML Analyser across a wide range of industries.

**So, what was the scope of the project?**

The goal is to develop a multi-agent application capable of automating the modification of complex XML documents. Each agent is responsible for a specific task, a validation taks, correction tasks, modification and orchestration task.



## Piepline and Architecture ️

### Global Pipeline 
This is the pipeline we plan to implement for the MVP. More details on the multi-agent architecture will be presented in the next steps.

<p align="center">
   <img src="https://www.pixenli.com/image/XGOD398p" alt="Global pipeline">
</p>

### Multi Agent Architecture

We chose a supervisor architecture to implement our system. The idea is to design and implement a pipeline that efficiently manages and coordinates the different tasks within the system.


<p align="center">
   <img src="https://www.pixenli.com/image/65hNX6OP" alt="Architecture Diagram">
</p>

.



## Experimentation with Scenarios

If a user sends a corrupted file (e.g., a missing closing tag, a malformed tag, or incorrect format), such issues can be handled at the orchestrator level before the file is even sent to the agents.

A user can also send an instruction that will be processed by the orchestrator.

The orchestrator checks the reliability of the input using guardrails. If the instruction aligns with the system's supported tasks namely correction, deletion, or addition of elements in XML then it will be forwarded to the appropriate agent. Any other instructions will not be sent to the modifier or corrector agents.

### Scenario 1: With Validator Agent

If the XML file is syntactically correct, it goes through the validator agent, which checks if it conforms to the s1000d XML standards.
If the file is valid, it is sent directly to the orchestrator.
Otherwise, the validator returns a list of errors to the LLM, which generates a report with instructions to correct the document and sends it to the orchestrator.

### Scenario 2: With Corrector Agent

The orchestrator decides to send the report coming from the validator to the corrector The orchestrator sends the report from the validator to the corrector agent, which applies the necessary corrections based on the provided instructions and returns the corrected file to the orchestrator. The orchestrator then sends the file back to the validator. This cycle continues until the file is clean, a human intervenes, or a predefined threshold is reached.

The corrector receives a report with a clear error paths, allowing it to focus only on the necessary XML fragment without parsing the entire file. 

### Scenario 3: With Modifier Agent

If the user sends a modification instruction (add, delete, update), the LLM decides to call the modifier agent.
Once the modifications are made, the result is returned to the orchestrator, which then validates it.
Further details are available in John's code.

## LLms Comparison



## User Interface



## 🚀 How to Run the Project  


### ⚠️ Important Notes  


### 🌐 Access the Application  


## Challenges Encountered


## Next Staps



