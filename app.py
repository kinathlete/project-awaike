# Import necessary libraries
import openai
import streamlit as st
from PIL import Image
from bs4 import BeautifulSoup
import requests
import pdfkit
import time
import os

# Set your OpenAI Assistant ID here
# assistant_id = 'asst_g51Qwp7RKViQEQVaWEjK1aYM'

# Initialize the OpenAI client (ensure to set your API key in the sidebar within the app)
client = openai
# Retrieve OpenAI API key from environment variables
# openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize variable to store assistant ids
available_assistant_ids = [
    "asst_LItDuB8TJeX8UojC21zzoNDw",
    "asst_vvjDSGC3ojf0YBXG7QtXDUz5",
    "asst_Cnjbb9Q91Gi7HmDhWxnCouXf"
]

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
        "asst_LItDuB8TJeX8UojC21zzoNDw": {
            "subheader": "Creates drafts for marketing briefs about \
                how a particular persona benefits from using Calibo."
            ,"instructions": "See the example prompt below. \
                Replace the persona name with the persona you want to use."
            ,"prompt": "Create a draft for a compelling marketing brief \
                about how Product Owners can use Calibo and what their \
                    benefits are from using it."
        },
        "asst_vvjDSGC3ojf0YBXG7QtXDUz5": {
            "subheader": "Creates drafts for marketing briefs about \
                how Calibo helps to solve a particular problem."
            ,"instructions": "See the example prompt below. \
                Replace the problem with the problem you want to use. \
                    And attach any relevant files in the sidebar. \
                        Make sure to reference the file in the prompt. \
                            Alternatively, you can reference a URL to \
                                a website that describes the problem."
            ,"prompt": "Create a draft for a marketing brief about how \
                enterprise organizations can build their data fabric \
                    more efficiently with Calibo. Use the attached file \
                        to understand the concept of Data Fabric better."
        },
        "asst_Cnjbb9Q91Gi7HmDhWxnCouXf": {
            "subheader": "Creates drafts for landing pages that show \
                how Calibo perfectly matches with other technologies."
            ,"instructions": "See the example prompt below. \
                Replace the technology names with the technologies \
                    you want to use. And replace the URLs with the \
                        corresponding URLs of your selected technologies."
            ,"prompt": "calibo: https://www.calibo.com/, \
                snowflake: https://www.snowflake.com/en/, \
                    databricks: https://www.databricks.com/"
        },
    }

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="ChatGPT-like Chat App", page_icon=":speech_balloon:")

# Define functions for scraping, converting text to PDF, and uploading to OpenAI
def scrape_website(url):
    """Scrape text from a website URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()

def text_to_pdf(text, filename):
    """Convert text content to a PDF file."""
    path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdfkit.from_string(text, filename, configuration=config)
    return filename

def upload_to_openai(filepath):
    """Upload a file to OpenAI and return its file ID."""
    with open(filepath, "rb") as file:
        response = openai.files.create(file=file.read(), purpose="assistants")
    return response.id

def get_assistants():
    """Retrieve the list of assistants associated with an organization."""
    all_assistants = client.beta.assistants.list()
    assistants = []
    for assistant in all_assistants:
        if assistant.id in available_assistant_ids:
            assistants.append(assistant)
    return assistants

def get_assistant_files(assistant_id):
    """Retrieve the list of files associated with an assistant."""
    assistant_files = client.beta.assistants.files.list(
        assistant_id=assistant_id
    )
    return assistant_files

def get_organization_files():
    """Retrieve the list of files associated with an organization."""
    organization_files = client.files.list()
    return organization_files

# Show Company logo
# Logo
dir_root = os.path.dirname(os.path.abspath(__file__))
logo = Image.open(dir_root+'/files/images/Calibo_229X64_neg.png')
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

# Divider line
st.sidebar.divider()

# Additional features in the sidebar for web scraping and file uploading
st.sidebar.header("Prepare the Project :paperclip:")
# website_url = st.sidebar.text_input("Enter a website URL to scrape and organize into a PDF", key="website_url")

# Button to scrape a website, convert to PDF, and upload to OpenAI
# if st.sidebar.button("Scrape and Upload"):
#     # Scrape, convert, and upload process
#     scraped_text = scrape_website(website_url)
#     pdf_path = text_to_pdf(scraped_text, "scraped_content.pdf")
#     file_id = upload_to_openai(pdf_path)
#     st.session_state.file_id_list.append(file_id)
#     #st.sidebar.write(f"File ID: {file_id}")

#  project_name = st.sidebar.text_input("Enter a project name", key="project_name")

# Sidebar option for users to upload their own files
uploaded_file = st.sidebar.file_uploader("Upload additional files to the assistant.", key="file_uploader")

# Button to upload a user's file and store the file ID
if st.sidebar.button("Upload File"):
    # Upload file provided by user
    if uploaded_file:
        with open(f"{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())
        additional_file_id = upload_to_openai(f"{uploaded_file.name}")
        st.session_state.file_id_list.append(additional_file_id)
        st.sidebar.write(f"Additional File ID: {additional_file_id}")

# Display all new file IDs
if st.session_state.file_id_list:
    st.sidebar.write("Uploaded File IDs:")
    for file_id in st.session_state.file_id_list:
        st.sidebar.write(file_id)
        # Associate files with the assistant
        assistant_file = client.beta.assistants.files.create(
            assistant_id=assistant_id, 
            file_id=file_id
        )

# Display all existing file names
if st.session_state.existing_file_name_list:
    st.sidebar.write("Knowledge Base:")
    for file_name in st.session_state.existing_file_name_list:
        name = '<p style="font-size: 10px;">{0}</p>'.format(file_name)
        st.sidebar.write(name, unsafe_allow_html=True)

# Divider line
st.sidebar.divider()

st.sidebar.header("Start the Chat :rocket:")
# Button to start the chat session
if st.sidebar.button("Start Chat"):
    # Check if files are uploaded before starting chat
    if st.session_state.file_id_list or st.session_state.existing_file_id_list:
        st.session_state.start_chat = True
        # Create a thread once and store its ID in session state
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.write("thread id: ", thread.id)
    else:
        st.sidebar.warning("Please upload at least one file to start the chat.")

# Define the function to process messages with citations
def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
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
    st.write(":exclamation: {0} :exclamation:".format(st.session_state.assistant_id_instructions[assistant_id]["instructions"]))
    st.write("**Example Prompt**")
    st.write(st.session_state.assistant_id_instructions[assistant_id]["prompt"])
else:
    st.title("Welcome to Awaike! :wave:")
    st.subheader("This is a revolutionary chat application that helps you to create compelling marketing content for your product.")

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
            st.markdown(message["content"])

    # Chat input for the user
    if prompt := st.chat_input("What shall I do?", key="chat_input"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add the user's message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
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
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            with st.chat_message("assistant"):
                st.markdown(full_response, unsafe_allow_html=True)
else:
    # Prompt to start the chat
    st.write("Please enter API Key, upload files and click 'Start Chat' to begin the conversation.")
