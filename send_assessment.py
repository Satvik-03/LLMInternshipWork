import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import openai
import re
import fitz  # PyMuPDF for extracting text from PDF
import os
from dotenv import load_dotenv

load_dotenv()
# Load the service account credentials
SERVICE_ACCOUNT_FILE = 'service_account.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/forms', 'https://www.googleapis.com/auth/drive']
)

# Set up Google Forms API service
forms_service = build('forms', 'v1', credentials=credentials)
user_email = os.getenv("EMAIL_ADDRESS")

# Set up OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")  # Replace with your actual OpenAI API key

# Function to generate unique questions
def generate_unique_questions(skill, number_of_questions=15):
    questions = set()
    attempts = 0
    max_attempts = number_of_questions * 2  # Allow up to twice the number of questions to ensure uniqueness
    
    while len(questions) < number_of_questions and attempts < max_attempts:
        prompt = f"Generate a multiple-choice question about {skill} with 4 options and indicate the correct answer."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert question generator for interview purpose test the skills by preparing questions based on tasks, challenges, Required skills and qualifications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7,
            n=1,
            stop=None
        )
        question = response['choices'][0]['message']['content'].strip()
        options = re.findall(r'[A-D]\)\s(.+)', question)  # Extract options
        if question and options and question not in questions:  # Check if both question and options are non-empty
            questions.add(question)
        attempts += 1
    
    return list(questions)

# Function to ensure unique options in questions
def ensure_unique_options(question):
    options = question['options']
    seen = set()
    unique_options = []
    for option in options:
        if option not in seen:
            seen.add(option)
            unique_options.append(option)
    if len(unique_options) < 4:
        # If fewer than 4 unique options, add placeholder options
        placeholders = [f"Option {i}" for i in range(1, 5)]
        for option in placeholders:
            if option not in unique_options:
                unique_options.append(option)
            if len(unique_options) == 4:
                break
    question['options'] = unique_options[:4]
    return question

# Parse OpenAI response
def parse_openai_response(response_text):
    lines = response_text.split('\n')
    question = lines[0].strip()
    options = []
    correct_answer = None

    for line in lines[1:]:
        match = re.match(r'([A-D])\)\s(.+)', line.strip())
        if match:
            option_text = match.group(2)
            options.append(option_text)
            if 'Correct' in line:
                correct_answer = option_text

    if correct_answer is None and len(options) == 4:
        # If correct answer is not explicitly stated, choose the first option as correct
        correct_answer = options[0]

    return {
        "question": question,
        "options": options,
        "correct_answer": correct_answer
    }

def create_google_form(skill, user_email):
    # Generate unique questions
    questions = generate_unique_questions(skill)

    # Apply parsing, ensure unique options, and remove blank questions
    formatted_questions = []
    seen_questions = set()
    for question in questions:
        parsed_question = parse_openai_response(question)
        if parsed_question["question"] not in seen_questions:
            seen_questions.add(parsed_question["question"])
            formatted_question = ensure_unique_options(parsed_question)
            formatted_questions.append(formatted_question)

    # Create a new Google Form with only a title
    form_metadata = {
        "info": {
            "title": f"PreScreening Exam",
        }
    }
    form = forms_service.forms().create(body=form_metadata).execute()
    form_id = form["formId"]

    # Prepare batch update request to add questions
    batch_update_request = {
        "requests": []
    }

    for i, q in enumerate(formatted_questions):
        question_request = {
            "createItem": {
                "item": {
                    "title": q["question"],
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": option} for option in q["options"]],
                                "shuffle": True
                            }
                        }
                    }
                },
                "location": {"index": i}
            }
        }
        batch_update_request['requests'].append(question_request)

    # Execute the batch update to add questions
    forms_service.forms().batchUpdate(formId=form_id, body=batch_update_request).execute()

    # Fetch the form with added questions to get item IDs
    form = forms_service.forms().get(formId=form_id).execute()

    # Set form as a quiz
    quiz_settings_request = {
        "requests": [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings"
                }
            }
        ]
    }

    forms_service.forms().batchUpdate(formId=form_id, body=quiz_settings_request).execute()

    # Prepare batch update request to set correct answers and point values
    answers_and_points_request = {
        "requests": []
    }

    for i, q in enumerate(formatted_questions):
        item = form['items'][i]
        question_id = item['itemId']
        correct_answer = q["correct_answer"]
        options = q["options"]
        
        # Check if the correct answer is within the options
        if correct_answer in options:
            correct_answer_index = options.index(correct_answer)

            answer_key_request = {
                "updateItem": {
                    "item": {
                        "itemId": question_id,
                        "questionItem": {
                            "question": {
                                "grading": {
                                    "pointValue": 1,
                                    "correctAnswers": {
                                        "answers": [{"value": options[correct_answer_index]}]
                                    }
                                }
                            }
                        }
                    },
                    "location": {"index": i},
                    "updateMask": "questionItem.question.grading"
                }
            }
            answers_and_points_request["requests"].append(answer_key_request)

    # Execute the requests to set correct answers and points
    forms_service.forms().batchUpdate(formId=form_id, body=answers_and_points_request).execute()

    # Share the form with the specified user and grant edit permissions
    drive_service = build('drive', 'v3', credentials=credentials)
    drive_service.permissions().create(
        fileId=form_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': user_email
        }
    ).execute()

    return form_id


# Function to extract the job description from the PDF text
def extract_job_description(pdf_text):
    # Identify common headers for the job description section
    job_description_patterns = [
        r"\b(Job\sDescription|Duties\sand\sResponsibilities|Role|Primary\sDuties|Key\sResponsibilities)\b",
        r"\b(Responsibilities|Role\sSummary|Position\sOverview|What\sYou'll\sDo|Key\sTasks|Job\sResponsibilities)\b"
    ]
    
    # Combine patterns into a single regex
    job_description_regex = "|".join(job_description_patterns)
    
    # Extract the job description section
    job_description_match = re.search(job_description_regex, pdf_text, re.IGNORECASE)
    if job_description_match:
        start_index = job_description_match.start()
        # Heuristic: extract text from the matched header till the next header or a reasonable length
        end_index = pdf_text.find("\n\n", start_index)  # Finding the next paragraph break
        if end_index == -1:
            end_index = len(pdf_text)
        job_description = pdf_text[start_index:end_index]
    else:
        # If no header is found, consider the entire text (fallback)
        job_description = pdf_text

    return job_description

# Function to extract skill from job description using LLM
def extract_skill_with_llm(job_description):
    # Use OpenAI LLM to analyze the text and extract the skill
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in analyzing the skills required for the position mentioned in job description."},
            {"role": "user", "content": f"Analyze the following job description and identify the key skill: {job_description} and return the key skill."}
        ],
        max_tokens=100,
        temperature=0.5,
        n=1,
        stop=None
    )
    extracted_skill = response['choices'][0]['message']['content'].strip()
    # Remove newline characters
    extracted_skill = extracted_skill.replace('\n', '')
    return extracted_skill


# Streamlit app
def main():
    st.title("Skill-based Question Generator & Form Creator")

    # Define the path to the PDF file in Gitpod directory
    pdf_file_path = "/workspace/GVP-LLMAgents-Team05/Python Programmer for Data Science Team .pdf"  # Adjust this path

    if os.path.exists(pdf_file_path):
        # Extract text from PDF
        pdf_document = fitz.open(pdf_file_path)
        pdf_text = ""
        for page_num in range(len(pdf_document)):
            pdf_text += pdf_document.load_page(page_num).get_text()

        # Extract job description
        job_description = extract_job_description(pdf_text)

        # Extract skill from job description
        skill = extract_skill_with_llm(job_description)

        # Display extracted skill
        st.write(f"**Extracted Skill:** {skill}")

        if st.button("Generate Questions and Create Form"):
            form_id = create_google_form(skill, user_email)
            st.success(f"Form created successfully! View it here: https://docs.google.com/forms/d/{form_id}/edit")
            st.info(f"Edit access granted to {user_email}")
    else:
        st.warning("PDF file not found. Please check the path and try again.")

if __name__ == "__main__":
    main()
