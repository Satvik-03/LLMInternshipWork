# LLMInternshipWork


# Opening Page
1. pip install streamlit PyPDF2 python-dotenv 
2. streamlit run job_description.py 


# Necessary requirements
1. Require an OpenAI API Key.
2. Generate Gmail App Password for email to be used.
3. Have access to Google Cloud Console.
4. Add the email address and app password into the .env file 
   
# Google Cloud Console
1. Go to Google Cloud Console and enable Google Forms API and Google Drive API for a new project.
2. Create a new project in Google Cloud Console.
3. Go to Enabled API and search for Google Forms API, Google Drive API and enable them.
4. Enable OAuth Consent Screen.
5. Go to Credentials.
6. Create new Credentials and select Service Account.
7. After creating account , Create Key after selecting account.
8. Download the Key
9. Add the file to the Git

# Question and Form Generator
1. Install the necessary libraries present in requirements.txt using pip install -r requirements.txt
2. Go the code present in send_assessment.py
3. Make necessary changes for the path ie  copy the path of service_account.json and enter your own OpenAi Key and add email for the necessary authorized email to edit and view responses.
4. Now run the code using streamlit run send_assessment.py
5. The Google Form will be generated along with a text file containing the questions and the correct answers.
6. From the Authorized email, go to the Google Form and enable quiz , choose the correct answers from text file and assign the marks.
7. Now send the quiz to the participants.

# Extraction and Email Generation
1. Now copy the link of the Spreadsheet assosciated with the Google Form and add the sheet to Git
2. Replace the path in the .env file 
3. Replace the gmail address and gmail app password in the .env
4. streamlit run evaluate_performance.py
5. The emails will be sent to the qualified canddiates.
