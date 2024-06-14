import streamlit as st
import os
import datetime
import base64
from PyPDF2 import PdfReader
from io import BytesIO
from dotenv import load_dotenv, set_key

# Load existing .env file
env_path = ".env"
load_dotenv(env_path)

# Function to save API key to .env file
def save_api_key_to_env(api_key):
    set_key(env_path, "OPENAI_API_KEY", api_key)

# Function to save uploaded file
def save_uploaded_file(file_data, file_type):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"uploaded_file_{timestamp}.{file_type}"
    file_path = os.path.join("uploaded_files", file_name)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(file_data)
    
    return file_path

# Function to display PDF content
def display_pdf_content(file_data):
    pdf_reader = PdfReader(BytesIO(file_data))
    content = []
    for page in pdf_reader.pages:
        content.append(page.extract_text())
    return "\n".join(content)

# Main function
def main():
    st.set_page_config(page_title="RecAgent", page_icon="📄")
    st.title("RecAgent")
    st.write("Upload the Job Description and enter your OpenAI API key to store and view the content.")

    # Two columns layout
    col1, col2 = st.columns(2)

    with col1:
        # File upload widget
        uploaded_file = st.file_uploader("Choose a PDF or text file", type=["pdf", "txt"])

    with col2:
        # OpenAI API Key input
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key here.")

    if st.button("Save"):
        if uploaded_file is not None and openai_api_key:
            file_type = uploaded_file.name.split('.')[-1]

            # Store OpenAI API key in .env file
            save_api_key_to_env(openai_api_key)
            st.success("OpenAI API key stored in .env file.")

            # Save the uploaded file in Gitpod filesystem
            file_data = uploaded_file.getvalue()
            file_path = save_uploaded_file(file_data, file_type)
            st.success(f"File uploaded and saved as {file_path}.")

            # Provide download link for the uploaded file
            st.download_button(
                f"Download {file_type.upper()} File",
                data=file_data,
                file_name=f"uploaded_file_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"
            )
            
            # Display file content
            st.subheader("File Content")
            if file_type == "txt":
                # For text files, display the content
                file_content = file_data.decode("utf-8")
                st.text(file_content)
            elif file_type == "pdf":
                # For PDF files, extract and display text
                file_content = display_pdf_content(file_data)
                st.text(file_content)
        else:
            st.error("Please upload a file and enter the OpenAI API key.")

    # Display stored API key
    if os.getenv("OPENAI_API_KEY"):
        st.subheader("Stored OpenAI API Key")
        st.text(os.getenv("OPENAI_API_KEY"))

    # List saved files for download
    st.subheader("Saved Files")
    if os.path.exists("uploaded_files"):
        for file_name in os.listdir("uploaded_files"):
            file_path = os.path.join("uploaded_files", file_name)
            with open(file_path, "rb") as file:
                st.download_button(f"Download {file_name}", file, file_name=file_name)

if __name__ == "__main__":
    main()
