import streamlit as st
import pandas as pd
import altair as alt
import io

def main():
    """
    Main function to run the Streamlit application.
    """
    # --- Page Configuration ---
    # Set the page configuration for a wider layout, which is good for charts.
    st.set_page_config(layout="wide")

    # --- Data Initialization & Upload ---
    # We start with some sample data, but allow the user to upload their own.
    # Updated sample data to match the new 'course', 'period', 'score' model
    sample_data = {
        'course': ['Calculus', 'Calculus', 'Calculus', 'Data Structures', 'Data Structures', 'Spanish', 'Calculus', 'Data Structures', 'Spanish', 'Calculus', 'Calculus'],
        'topic': ['Limits', 'Limits', 'Derivatives', 'Arrays', 'Linked Lists', 'Verb Conjugation', 'Limits', 'Arrays', 'Verb Conjugation', 'Derivatives', 'Limits'],
        'period': ['Week 1', 'Week 2', 'Week 1', 'Week 1', 'Week 2', 'Month 1', 'Week 3', 'Week 3', 'Month 2', 'Week 2', 'Week 4'],
        'score': [70, 75, 65, 80, 85, 90, 80, 92, 95, 70, 85]
    }
    df = pd.DataFrame(sample_data)

    # Initialize session state for accumulated data if not already present
    if 'all_progress_data' not in st.session_state:
        st.session_state.all_progress_data = df

    # --- File Uploader (Bonus Feature) ---
    st.sidebar.header("Upload New Data")
    uploaded_file = st.sidebar.file_uploader(
        "Upload new progress CSV or JSON data (must contain 'course', 'topic', 'period', 'score')",
        type=['csv', 'json']
    )

    # If a user uploads a file, process it and append to existing data
    if uploaded_file is not None:
        try:
            if uploaded_file.type == 'text/csv':
                new_data = pd.read_csv(uploaded_file)
            elif uploaded_file.type == 'application/json':
                new_data = pd.read_json(uploaded_file)
            else:
                st.sidebar.error("Unsupported file type. Please upload CSV or JSON.")
                new_data = pd.DataFrame() # Empty DataFrame if unsupported

            # Basic validation for new data columns
            required_columns = {'course', 'topic', 'period', 'score'}
            if not required_columns.issubset(new_data.columns):
                st.sidebar.error(f"Error: Uploaded file must contain the columns: {', '.join(required_columns)}")
            else:
                # Append new data and remove duplicates based on all columns
                st.session_state.all_progress_data = pd.concat([st.session_state.all_progress_data, new_data]).drop_duplicates().reset_index(drop=True)
                st.sidebar.success("Successfully uploaded and merged new data!")

        except Exception as e:
            st.sidebar.error(f"Error processing file: {e}. Please ensure data is correctly formatted.")

    # Always use the current state of the data
    current_df = st.session_state.all_progress_data.copy()

    # --- UI Controls: Course Selection (Right of Chart) and Chart Display at Top ---
    # Create two columns for layout: one for the chart, one for the selectbox
    # This places the chart and its controls at the very top.
    chart_col, selectbox_col = st.columns([4, 1]) # 4 parts for chart, 1 for selectbox

    # Get a unique list of courses from the DataFrame to populate the dropdown.
    course_list = current_df['course'].unique()

    with selectbox_col:
        st.write("### Course Selector") # Small heading for the selector
        selected_course = st.selectbox(
            "Select a Course:",
            course_list,
            key="course_selector", # Unique key for the selectbox
            label_visibility="collapsed" # Hide the label for compactness
        )

    # Filter the DataFrame based on the selected course.
    course_data = current_df[current_df['course'] == selected_course]

    # Sort data by period for proper line chart rendering
    course_data['period_sort_key'] = course_data['period'].astype(str) # Convert to string for consistent sorting
    course_data = course_data.sort_values(by=['period_sort_key', 'topic']).drop(columns=['period_sort_key'])


    with chart_col:
        # --- Chart Creation (Altair Multi-Line Chart) ---
        if not course_data.empty:
            chart_title = f"Progress by Topic – {selected_course}"
            chart_caption = "Track your weekly/monthly understanding to stay motivated."

            base = alt.Chart(course_data).encode(
                # X-axis: Period
                x=alt.X('period:N', sort=None, title='Period'), # 'sort=None' to use natural sort order of 'period' or sorted dataframe

                # Y-axis: Score
                y=alt.Y('score:Q', title='Understanding Level (0-100)', scale=alt.Scale(domain=[0, 100])),

                # Color: One line per topic
                color=alt.Color('topic:N', title='Topic'),

                # Tooltips: Show topic, period, and score
                tooltip=[
                    alt.Tooltip('topic:N', title='Topic'),
                    alt.Tooltip('period:N', title='Period'),
                    alt.Tooltip('score:Q', title='Score', format='.1f')
                ]
            ).properties(
                title=chart_title,
                height=250 # Reduced height for a more compact appearance
            ).interactive() # Enable zooming and panning

            line_chart = base.mark_line(point=True).encode( # point=True ensures markers are shown
                # No special trend highlighting requested for this specific graph style
            )

            st.altair_chart(line_chart, use_container_width=True)
            st.caption(chart_caption) # Caption directly below the chart

        else:
            st.warning(f"No data available for the selected course: {selected_course}.")

    # --- Main Website Content Below the Chart ---
    # General title and description moved below the chart section
    st.title("📚 Learning Progress Tracker")
    st.write("An interactive dashboard to visualize your knowledge growth over time, by topic.")
    st.write("---") # Visual separator to distinguish the top section from main content


    # --- Bonus: Show/Hide Raw Data ---
    # A checkbox to conditionally display the raw data table for the selected course.
    show_data = st.checkbox(f"Show raw data for {selected_course}")

    if show_data:
        st.subheader(f"Raw Data for {selected_course}")
        # Display the filtered data in a clean table.
        st.dataframe(course_data)


if __name__ == "__main__":
    main()
