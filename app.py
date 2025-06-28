import streamlit as st
import pandas as pd
import altair as alt
import io
import pypdf
import docx
from datetime import datetime
import os
# Import all three backend functions
from gemini_app import get_student_analysis, extract_chart_data_from_text, get_chat_response

# --- Helper Functions ---
def extract_text_from_files(uploaded_files):
    """Extracts text from uploaded files."""
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

def save_report_to_archive(report_content):
    """Saves the generated report to the archive folder."""
    if not os.path.exists("archive"):
        os.makedirs("archive")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"archive/analysis_report_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    return filename

def load_report_from_archive(filename):
    """Loads a specific report from the archive."""
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

# --- Main App ---
def main():
    st.set_page_config(page_title="Student AI Dashboard", page_icon="🚀", layout="wide")

    # Initialize session state for report, chat, and chart data
    if "analysis_report" not in st.session_state:
        st.session_state.analysis_report = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chart_df" not in st.session_state:
        st.session_state.chart_df = None

    # --- Sidebar ---
    with st.sidebar:
        st.header("Controls")

        with st.expander("1. Generate New Analysis", expanded=True):
            uploaded_work_files = st.file_uploader(
                "Upload Student Work Files",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True,
                key="work_uploader"
            )
            target_topics = st.text_area(
                "Enter Course Topics",
                height=150,
                help="List all relevant topics for the course, one per line."
            )
            analyze_button = st.button("Generate Report", use_container_width=True)

        with st.expander("2. View Past Reports"):
            archive_dir = "archive"
            if os.path.exists(archive_dir) and os.listdir(archive_dir):
                archived_files = sorted(os.listdir(archive_dir), reverse=True)
                selected_report = st.selectbox("Select a past report:", archived_files)
                if st.button("Load Report", use_container_width=True):
                    st.session_state.analysis_report = load_report_from_archive(os.path.join(archive_dir, selected_report))
                    st.session_state.chat_history = []
                    st.session_state.chart_df = None # Clear chart when loading old text report
                    st.success(f"Loaded report: {selected_report}")
            else:
                st.info("No past reports found.")

    # --- Main Content Area ---
    st.title("🚀 AI-Powered Student Dashboard")

    # --- Main button logic ---
    if analyze_button:
        if not uploaded_work_files or not target_topics:
            st.warning("Please upload files and enter topics to generate a new report.")
        else:
            with st.spinner("AI is processing files and generating a full report..."):
                student_work_text = extract_text_from_files(uploaded_work_files)
                if student_work_text:
                    st.session_state.chat_history = []
                    
                    # Call both backend functions
                    chart_data_list = extract_chart_data_from_text(student_work_text)
                    analysis_output = get_student_analysis(student_work_text, target_topics)
                    
                    # Store results in session state
                    st.session_state.chart_df = pd.DataFrame(chart_data_list) if chart_data_list else None
                    st.session_state.analysis_report = analysis_output
                    
                    if analysis_output and "Error:" not in analysis_output:
                        saved_filename = save_report_to_archive(analysis_output)
                        st.success(f"New analysis complete! Report saved to {saved_filename}")
                    else:
                        st.error(analysis_output or "Failed to generate the analysis.")

    # --- Display Chart if available in session state ---
    if st.session_state.chart_df is not None and not st.session_state.chart_df.empty:
        st.header("📈 AI-Generated Progress Chart")
        chart = alt.Chart(st.session_state.chart_df).mark_line(point=True).encode(
            x=alt.X('period:N', sort=None, title='Assignment/Period'),
            y=alt.Y('score:Q', title='Estimated Score (0-100)', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('topic:N', title='Topic'),
            tooltip=['course', 'topic', 'period', 'score']
        ).properties(title="Student Progress Based on Uploaded Files").interactive()
        st.altair_chart(chart, use_container_width=True)
        st.divider()

    # --- Display Analysis and Chat if a report exists in session state ---
    if st.session_state.analysis_report:
        st.header("🎓 Performance Analysis & Study Guide")
        st.markdown(st.session_state.analysis_report)
        st.divider()

        st.header("💬 Ask a Follow-up Question")
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about this report..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Thinking..."):
                api_history = [{"role": msg["role"], "parts": [msg["content"]]} for msg in st.session_state.chat_history]
                response = get_chat_response(
                    chat_history=api_history,
                    latest_question=prompt,
                    original_analysis=st.session_state.analysis_report
                )
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
    elif not analyze_button:
        st.info("Upload student work and click 'Generate Report' in the sidebar to get started.")

if __name__ == "__main__":
    main()