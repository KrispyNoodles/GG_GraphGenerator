import chainlit as cl
from config import llm
from langchain.schema import HumanMessage, AIMessage
from graph_builder.pdf_to_csv import main_pdf_to_csv
from custom_retriever import excel_to_df, create_retriever
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from graph_builder.csv_to_graph import extract_code_and_response
from prompts import system_prompt


memory = MemorySaver()

# initializing the excel
output_excel_path = "extracted_tables.xlsx"
document_array = excel_to_df(output_excel_path)
retriever_tool = create_retriever(document_array)

tools = [retriever_tool]

agent_executor = create_react_agent(llm, tools, checkpointer=memory, debug=False)

@cl.on_message
async def handle_message(message: cl.Message):

    global agent_executor

    messages = []

    systemprompt = AIMessage(content=system_prompt)
    messages.append(systemprompt)

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
                # retrieivng the summary text to print it
                summary = await main_pdf_to_csv(pdf_file.path)        

                # rebuild the agent
                document_array = excel_to_df(output_excel_path)
                retriever_tool = create_retriever(document_array)
                tools = [retriever_tool]
                agent_executor = create_react_agent(llm, tools, checkpointer=memory, debug=False)

                # sending the uyser the summary of which tables that are able to be plotted
                # have to be converted to string to be printed nicely
                summary_string = summary.to_markdown(index=False)
                summary_statement = f"I have processed the PDF and extracted the following tables that are available for plotting: \n\n{summary_string}"

                # adding as a human message instead to prevent the LLM from beign confused as to what it has said
                messages.append(HumanMessage(content=summary_statement))

                # sending the user an excel sheet to be downloaded to view the current data extracted and to be interacted 
                # before further choosing which graph it wishes to select to be plotted
                await cl.Message(content=summary_statement).send()

                # adding a file that sends the excel file to the user
                excel_file = [
                            cl.File(
                                name=f"excel_{pdf_file.name}.xlsx",
                                path=f"extracted_tables.xlsx",
                                display="inline",
                            ),
                        ]
                await cl.Message(
                    content="The file is available for download below.", elements=excel_file
                ).send()

                processed_files.append(pdf_file.name)

        total_files = (", ".join(f"{name}" for name in processed_files))

        # Create an AI message indicating the file has been processed
        user_process_msg = HumanMessage(content=f"I have uploaded {total_files}.")
        messages.append(user_process_msg)

        await cl.Message(content=f"These files: {total_files} have been processed").send()
    
    
    # adding the user's message
    messages.append(HumanMessage(content=message.content))

    response = agent_executor.invoke(    
        {"messages": messages},
        config={"configurable": {"thread_id": "session-1"}}
    )
    
    output = response["messages"][-1].content

    print(f"repsonse forom LLM is: {output}")

    # if graph code found in output send it
    if "import" in output and "plt" in output:

        # a function that seperates the python file and the text
        code_block, response_text = extract_code_and_response(output)

        try:
            exec(code_block)
            print("graph sent")
                    
        except Exception as e:
            print(f"There was a problem running the code to plot because of: {e}")        

        image = cl.Image(path="graph.png", name="image1", display="inline")

        # Attach the image to the message
        await cl.Message(
            content=response_text,
            elements=[image],
        ).send()
        
    else:
        print("graph not sent")

        # reformatting the tail_text
        output = output.replace("## RESPONSE","").replace("## END RESPONSE","")

        await cl.Message(content=output).send()
    
    messages.append(output)
