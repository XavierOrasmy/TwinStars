import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import io
import pypdf
import docx

def extract_text_from_files(uploaded_files):
    """
    Extracts text from a list of uploaded files (PDF, DOCX, TXT).
    """
    full_text = ""
    for file in uploaded_files:
        try:
            if file.name.endswith('.pdf'):
                pdf_reader = pypdf.PdfReader(io.BytesIO(file.getvalue()))
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n\n"
            elif file.name.endswith('.docx'):
                doc = docx.Document(io.BytesIO(file.getvalue()))
                for para in doc.paragraphs:
                    full_text += para.text + "\n"
                full_text += "\n"
            elif file.name.endswith('.txt'):
                full_text += file.getvalue().decode('utf-8') + "\n\n"
        except Exception as e:
            st.error(f"Error reading file {file.name}: {e}")
    return full_text

def get_gemini_response(prompt):
    """
    Loads the API key from a .env file and generates a response from the Gemini API.
    """
    try:
        # Load environment variables from your .env file
        load_dotenv()
        
        # Get your API key from the loaded environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("GEMINI_API_KEY not found in .env file. Please make sure the file and variable are correctly set.")
            return None

        # Configure the generative AI model with the API key
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        st.error(f"An error occurred with the Gemini API: {e}")
        return None

def main():
    st.set_page_config(page_title="Student Performance Analyzer", page_icon=":mortar_board:", layout="wide")

    st.title("🎓 Student Performance Analyzer & Study Planner")
    st.write("Upload a student's past work and a list of topics to receive a detailed performance analysis, a forecast of future challenges, and a tailored study plan.")

    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("Inputs")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Upload Homework/Exam Files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload the student's past homework, exams, and any other relevant work."
        )

        # Text area for topics
        target_topics = st.text_area(
            "Enter Target Topics",
            height=200,
            help="List all relevant topics for the course or subject, one per line."
        )

        # Analyze button
        analyze_button = st.button("Analyze Student Performance", use_container_width=True)

    # --- Main Area for Output ---
    if analyze_button:
        if not uploaded_files:
            st.warning("Please upload at least one file of student work.")
        elif not target_topics:
            st.warning("Please enter the list of target topics.")
        else:
            with st.spinner("Analyzing student work and generating report... This may take a moment."):
                # 1. Extract text from uploaded files
                student_work_text = extract_text_from_files(uploaded_files)

                if student_work_text:
                    # 2. Construct the prompt for the Gemini API
                    prompt = f"""
                    You are an expert educational analyst. Based on the following student work and list of topics, please perform a detailed three-part analysis.

                    **Part 1: Analyze Existing Weaknesses**
                    Analyze the provided student work to identify every area of underperformance. Then, present a ranked list of these topics from weakest to strongest.

                    **Part 2: Predict Future Challenges**
                    Using the ranked weakness profile from Part 1 and the full list of target topics, predict which upcoming subjects the student is most likely to struggle with. Provide a prioritized list of these future trouble spots.

                    **Part 3: Generate a Tailored Study Plan**
                    Generate a concise and actionable study plan to address both the current weak areas and the predicted challenges. For each topic in the study plan, you must include:
                    1.  **Key Concepts to Review:** A bulleted list of the most important concepts for that topic.
                    2.  **Recommended Practice Exercises:** Suggestions for types of problems or questions to practice.
                    3.  **Resource Links or Summaries:** Provide a relevant, high-quality resource link (like a Khan Academy or university page) or a brief summary of the topic if a link is not available.

                    Please structure your entire output clearly with the following markdown headings:
                    ### 1. Ranked List of Existing Weaknesses
                    ### 2. Forecast of Future Trouble Spots
                    ### 3. Tailored Study Plan

                    ---
                    **Provided Student Work Content:**
                    {student_work_text}
                    ---
                    **Provided List of Target Topics:**
                    {target_topics}
                    ---
                    """

                    # 3. Get the response from the Gemini API
                    gemini_output = get_gemini_response(prompt)

                    # 4. Display the results
                    if gemini_output:
                        st.success("Analysis Complete!")
                        
                        # Use st.expander to neatly organize the output
                        with st.expander("1. Ranked List of Existing Weaknesses", expanded=True):
                            # A simple way to parse the section. Assumes the LLM follows instructions.
                            try:
                                weaknesses = gemini_output.split("### 2.")[0].split("### 1. Ranked List of Existing Weaknesses")[1]
                                st.markdown(weaknesses)
                            except IndexError:
                                st.write("Could not parse this section from the response.")

                        with st.expander("2. Forecast of Future Trouble Spots", expanded=True):
                            try:
                                forecast = gemini_output.split("### 3.")[0].split("### 2. Forecast of Future Trouble Spots")[1]
                                st.markdown(forecast)
                            except IndexError:
                                st.write("Could not parse this section from the response.")

                        with st.expander("3. Tailored Study Plan", expanded=True):
                            try:
                                study_plan = "### 3. Tailored Study Plan" + gemini_output.split("### 3. Tailored Study Plan")[1]
                                st.markdown(study_plan, unsafe_allow_html=True)
                            except IndexError:
                                st.write("Could not parse this section from the response.")
                    else:
                        st.error("Failed to get a response from the analysis model.")

if __name__ == "__main__":
    main()