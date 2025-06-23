import chainlit as cl
from config import llm
from langchain.schema import HumanMessage, AIMessage
from graph_builder.pdf_to_csv import main_pdf_to_csv

# rebuild the retriever after it has been stored
from custom_retriever import retriever_tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


memory = MemorySaver()

tools = [retriever_tool]

agent_executor = create_react_agent(llm, tools, checkpointer=memory, debug=False)


@cl.on_message
async def handle_message(message: cl.Message):

    messages = []

    system_prompt = AIMessage(content="You are a chatbot that helps to plot graphs")
    messages.append(system_prompt)

    # creating a dict to store each dict of pdf (can be placed in pdf to csv to be stored in a db locally?)
    pdf_dict = {}   

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

                # sending the uyser the summary of which tables that are able to be plotted
                # have to be converted to string to be printed nicely
                summary_string = summary.to_markdown(index=False)
                summary_statement = f"The tables available to plot graphs are:\n\n{summary_string}"

                messages.append(AIMessage(content=summary_statement))

                # sending the user an excel sheet to be downloaded to view the current data extracted and to be interacted 
                # before further choosing which graph it wishes to select to be plotted
                await cl.Message(content=summary_statement).send()

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

    # if graph found in output send it
    if "graph.png" in output:

        print("graph sent")

        # with open("graph.png", "rb") as f:
        #     img_bytes = f.read()

        output.replace("(sandbox:/mnt/data/graph.png)","(graph.png)")
        # await cl.Image(
        #                 name="graph.png",
        #                 content=img_bytes,
        #                 display="inline"
        #             ).send(for_id=message.id)
        
        await cl.Message(content=output).send()
        
    else:
        print("graph not sent")
        await cl.Message(content=output).send()

    # it is not updating the color because the retriever is the one generating the image
    
    print(f"repsonse forom llmis  {output}")
    messages.append(output)



