# Import necessary libraries
import openai
import streamlit as st
from PIL import Image
import time
import os

tst = "tdsfadsestadsfa"
# Initialize the OpenAI client (ensure to set your API key in the sidebar within the app)
client = openai
# Retrieve OpenAI API key from environment variables
# openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize variable to store assistant ids
available_assistant_ids = [
    "asst_c31H2OYVhod2mY2R2rp6E8Ta" # Calibo Universal Assistant
    ,"asst_cuNHZWVmMTSGZE6hoGplgH27" # Calibo Sales
    ,"asst_k0AWkqe2WOvcapTeaJyzUhlJ" # Calibo Marketing
    ,"asst_fHy8v3BaH1i9CdsIURkm4hb8" # Calibo Product
    # ,"asst_lBblJYey0PciYoPmZFFPAKXF" # Calibo Internet Assistant
]

## SESSION VARIABLES ##

# Initialize session state variables for file IDs and chat control
if "assistant_name_list" not in st.session_state:
    st.session_state.assistant_name_list = []

if "selected_assistant_name" not in st.session_state:
    st.session_state.selected_assistant_name = ""

if "existing_file_id_list" not in st.session_state:
    st.session_state.existing_file_id_list = []

if "existing_file_name_list" not in st.session_state:
    st.session_state.existing_file_name_list = []

if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "assistant_id_instructions" not in st.session_state:
    st.session_state.assistant_id_instructions = {
        # sales assistant
        "asst_cuNHZWVmMTSGZE6hoGplgH27": {
            "subheader": "Helping on sales related questions about Calibo."
            ,"instructions": "Ask me specific questions about sales at Calibo \
                or refer to a list of questions that I should answer from the \
                    knowledge I have gained about the company so far. With my \
                        30+ years of experience in sales, I can also advise you \
                            on how to best approach your sales strategy. Just \
                                use me as your sounding board for sales matters."
            ,"prompt": "What's Calibo's sales strategy today?"
        },
        # marketing assistant
        "asst_k0AWkqe2WOvcapTeaJyzUhlJ": {
            "subheader": "Helping on marketing related questions about Calibo."
            ,"instructions": "Ask me questions about previous marketing campaigns \
                 of Calibo or refer to a list of questions that I should answer \
                    to the best of my ability. I bring 30+ years of experience \
                        in B2B software marketing and I'm happy to advise on \
                            ideal marketing strategies for Calibo tailored to \
                                 your needs."
            ,"prompt": "What are key benefits of Calibo for Enterprise Product \
                Managers?"
        },
        # product assistant
        "asst_fHy8v3BaH1i9CdsIURkm4hb8": {
            "subheader": "Helping on product related questions about Calibo."
            ,"instructions": "Ask me about Calibo's product features and \
                central concepts of our platform or refer to a list of \
                    questions that I should answer based on my knowledge \
                        about the product. I have 30+ years of experience \
                            in product management and I'm happy to advise \
                                you on how to best position Calibo in the \
                                    market from a technical perspective."
            ,"prompt": "What is the difference between Calibo and Azure DevOps?"
        },
        # universal assistant
        "asst_c31H2OYVhod2mY2R2rp6E8Ta": {
            "subheader": "Helping you to scale up Calibo to new heights."
            ,"instructions": "Ask me to help you with any request in the areas of \
                content creation, strategy development or market and competitive \
                    research. I can currently work with PDF attachments but cannot \
                        access the internet. Start with the sample prompt below \
                            or create your own. You can always ask me what \
                                I can do for you if you are unsure. I am working \
                                    really well, when I can interact with the \
                                        other Calibo expert assistants. Let's go!"
            ,"prompt": "Create a draft for a compelling 1-2 pager marketing \
                brief about how Product Managers can use Calibo and what \
                    their benefits are from using it."
        },
        # internet assistant
        "asst_lBblJYey0PciYoPmZFFPAKXF": {
            "subheader": "Helps the user with any request that involves \
                researching the internet."
            ,"instructions": "Provide questions and URLs to the websites \
                you want to access and summarize."
            ,"prompt": "Summarize the contents from www.snowflake.com."
        }

    }

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

## PAGE CONFIG ##

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="Awaike - AI-Powered Content Assistant", page_icon=":speech_balloon:")

## SIDEBAR FUNCTIONS ##

# Define functions to help with project setup
def upload_to_openai(filepath):
    with open(filepath, "rb") as file:
        response = openai.files.create(file=open(filepath, "rb"), purpose="assistants")
    return response.id

def get_assistants():
    all_assistants = client.beta.assistants.list()
    assistants = []
    for assistant in all_assistants:
        if assistant.id in available_assistant_ids:
            assistants.append(assistant)
    return assistants

def get_assistant_files(assistant_id):
    assistant_files = client.beta.assistants.files.list(
        assistant_id=assistant_id
    )
    return assistant_files

def get_organization_files():
    organization_files = client.files.list()
    return organization_files

def reset_conversation():
    st.session_state.messages = []
    start_conversation()

def start_conversation():
    st.session_state.start_chat = True
    # Create a thread once and store its ID in session state
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    # st.write("thread id: ", thread.id)

## SIDEBAR ##

# Show Company logo in the sidebar
dir_root = os.path.dirname(os.path.abspath(__file__))
logo = Image.open(dir_root+'/files/images/Digital Logo_Calibo.png')
st.sidebar.image(logo)

# Create a sidebar for API key configuration and additional features
st.sidebar.header("Configuration :wrench:")

api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if api_key:
    openai.api_key = api_key

    # Create a selectbox to pick the assistant by name and list all files associated with the assistant
    assistants = get_assistants()
    assistant_names = []
    for assistant in assistants:
        assistant_names.append(assistant.name)
    st.session_state.assistant_name_list = assistant_names
    st.session_state.selected_assistant_name = st.sidebar.selectbox("Select an Assistant", st.session_state.assistant_name_list)
    if st.session_state.selected_assistant_name:
        for assistant in assistants:
            if assistant.name == st.session_state.selected_assistant_name:
                assistant_id = assistant.id
                assistant_files = get_assistant_files(assistant_id)
                organization_files = get_organization_files()
                assistant_file_id_list = []
                assistant_file_list = []
                for file in assistant_files:
                    for org_file in organization_files:
                        if file.id == org_file.id:
                            assistant_file_id_list.append(org_file.id)
                            assistant_file_list.append(org_file.filename)
                st.session_state.existing_file_id_list = assistant_file_id_list
                st.session_state.existing_file_name_list = assistant_file_list
    
    # Starte conversation with the selected assistant
    if st.session_state.start_chat == False:
        start_conversation()

    # Divider line
    st.sidebar.divider()

    # Reset the chat
    st.sidebar.header("Reset the Chat :rewind:")
    # Button to reset the chat session
    if st.session_state.start_chat: 
        st.sidebar.button("Reset Chat", on_click=reset_conversation, type="primary")

    # Divider line
    st.sidebar.divider()

    # Additional features in the sidebar for web scraping and file uploading
    st.sidebar.header("Edit the Assistant :paperclip:")

    # # Sidebar option for users to upload their own files
    # uploaded_file = st.sidebar.file_uploader("Upload additional files to the assistant.", key="file_uploader")

    # # Button to upload a user's file and store the file ID
    # if st.sidebar.button("Upload File"):
    #     # Upload file provided by user
    #     if uploaded_file:
    #         with open(f"{uploaded_file.name}", "wb") as f:
    #             f.write(uploaded_file.getbuffer())
    #         additional_file_id = upload_to_openai(f"{uploaded_file.name}")
    #         st.session_state.file_id_list.append(additional_file_id)
    #         st.sidebar.write(f"Additional File ID: {additional_file_id}")

    # Display all existing file names
    if st.session_state.existing_file_name_list:
        st.sidebar.write("Knowledge Base:")
        for file_name in st.session_state.existing_file_name_list:
            name = '<p style="font-size: 10px;">{0}</p>'.format(file_name)
            st.sidebar.write(name, unsafe_allow_html=True)

## MAIN CHAT FUNCTIONS ##

# Define the function to process messages with citations
def process_message_with_citations(message):
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {'filename': 'cited_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            cited_file = {'filename': 'downloaded_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')  # The download link should be replaced with the actual download path

    # Add footnotes to the end of the message content
    full_response = message_content.value + '\n\n' + '\n'.join(citations)
    return full_response

# Main chat interface setup
if st.session_state.selected_assistant_name:
    st.title("{0} :robot_face:".format(st.session_state.selected_assistant_name))
    st.subheader(st.session_state.assistant_id_instructions[assistant_id]["subheader"])
    st.write("*{0}*".format(st.session_state.assistant_id_instructions[assistant_id]["instructions"]))
    st.write("**Example Prompt**")
    st.write(st.session_state.assistant_id_instructions[assistant_id]["prompt"])
else:
    st.title("Welcome to Awaike! :wave:")
    st.subheader("The revolutionary AI-assistant app promising to \
                 gain you the competitive edge you have been looking for.")

# Only show the chat interface if the chat has been started
if st.session_state.start_chat:
    # Initialize the model and messages list if not already in session state
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown("**{0}**".format(message["name"]))
            st.markdown(message["content"])

    # Let user attach file to message
    uploaded_file = st.file_uploader("Attach files to your message.", type=["pdf"], key="message_file_uploader")

    # Chat input for the user
    if prompt := st.chat_input("What shall I do?", key="chat_input"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "name": "You", "content": prompt})
        with st.chat_message("user"):
            st.markdown("**You**")
            st.markdown(prompt)
            if uploaded_file:
                st.markdown(f"File attached: {uploaded_file.name}")

        # Upload files provided by user
        if uploaded_file:
            with open(f"{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
            additional_file_id = upload_to_openai(f"{uploaded_file.name}")

        # Add the user's message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt,
            file_ids=[additional_file_id] if uploaded_file else []
        )

        # Create a run with additional instructions
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id
        )

        # Poll for the run to complete and retrieve the assistant's messages
        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )

        # Retrieve messages added by the assistant
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]

        for message in reversed(assistant_messages_for_run):
            full_response = process_message_with_citations(message)
            st.session_state.messages.append({"role": "assistant", "name": \
                                              st.session_state.selected_assistant_name, \
                                                "content": full_response})
            with st.chat_message("assistant"):
                st.markdown(f"**{st.session_state.selected_assistant_name}**")
                st.markdown(full_response, unsafe_allow_html=True)

else:
    # Prompt to start the chat
    st.write("Please enter API Key to begin your work with the assistants.")