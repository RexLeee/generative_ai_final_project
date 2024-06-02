import streamlit as st
import pandas as pd
import json
from utils import get_table_data
from fpdf import FPDF

def display_history():
    st.title("Quiz History")
    if "quiz_history" in st.session_state and st.session_state.quiz_history:
        for i, entry in enumerate(st.session_state.quiz_history, start=1):
            st.write(f"#### Quiz {i}")
            question_type = entry["question_type"]
            quiz_data = entry["quiz_data"]
            user_answers = entry["user_answers"]
            correct_answers = entry["correct_answers"]

            st.write("### Quiz Data")
            table_data = get_table_data(json.dumps(quiz_data),question_type)  # Adjust as needed
            if table_data:
                df = pd.DataFrame(table_data)
                df.index = df.index + 1
                st.table(df)

            st.write("### User Answers")
            for key, value in user_answers.items():
                st.write(f"Question {key}: {value}")
    else:
        st.write("No quiz history available now.")




display_history()