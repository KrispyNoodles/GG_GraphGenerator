import chainlit as cl
from config import llm
from langchain.schema import HumanMessage, AIMessage
from graph_builder.pdf_to_csv import main_pdf_to_csv
from graph_builder.csv_to_graph import main_csv_to_graph

@cl.on_message
async def handle_message(message: cl.Message):

    messages = []

    # Checking if there is a pdf attached to the message
    if message.elements:

        processed_files = []

        # processing a pdf
        for pdf_file in message.elements:

            # Verify the file is indeed a PDF
            if pdf_file.mime == 'application/pdf':
                print("Processing PDF", pdf_file.name)

                # converting the pdf into excel
                # the files are only created temporarily from the covnersation
                await main_pdf_to_csv(pdf_file.path)

                processed_files.append(pdf_file.name)

        total_files = (", ".join(f"{name}" for name in processed_files))

        # Create an AI message indicating the file has been processed
        user_process_msg = HumanMessage(content=f"I have uploaded {total_files}.")
        messages.append(user_process_msg)

        await cl.Message(content=f"These files: {total_files} have been processed").send()
    
    user_input = message.content

    system_prompt = AIMessage(content="You are a chatbot that speaks in cat language")

    response = llm.invoke([system_prompt,HumanMessage(content=user_input)])

    excel_file_path = "/home/ljunfeng/prototyping/pdf_to_graph/dataset/D22000797 Bonder K-NET 11Aug23/extracted_tables.xlsx"
    user_request = "please plot the most appropriate data viz this table"
    selected_table = "Unnamed_Table_f0fa025a_1"

    main_csv_to_graph(excel_file_path, user_request, selected_table)
    await cl.Message(content=response.content).send()
