import chainlit as cl
from config import llm
from langchain.schema import HumanMessage, AIMessage
from graph_builder.formatted_excel import main_excel_to_formatted_excel
from custom_retriever import excel_to_df, create_retriever
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from graph_builder.excel_to_graph import extract_code_and_response
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

        # processing a pdf
        for excel_file in message.elements:

            # Verify the file is indeed a PDF
            if excel_file.mime in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:

                print("Processing Excel", excel_file.name)

                # converting the pdf into excel
                # the files are only created temporarily from the covnersation
                # retrieivng the summary text to print it
                summary = await main_excel_to_formatted_excel(excel_file.path)        

                # rebuild the agent
                document_array = excel_to_df(output_excel_path)
                retriever_tool = create_retriever(document_array)
                tools = [retriever_tool]
                agent_executor = create_react_agent(llm, tools, checkpointer=memory, debug=False)

                # sending the uyser the summary of which tables that are able to be plotted
                # have to be converted to string to be printed nicely
                summary_string = summary.to_markdown(index=False)
                summary_statement = f"These are the tables found in my excel file: \n\n{summary_string}"

                # adding as a human message instead to prevent the LLM from beign confused as to what it has said
                messages.append(HumanMessage(content=summary_statement))

                # sending the user an excel sheet to be downloaded to view the current data extracted and to be interacted 
                # before further choosing which graph it wishes to select to be plotted
                await cl.Message(content=summary_statement).send()

    
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
