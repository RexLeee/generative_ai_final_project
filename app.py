import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains import SequentialChain
import streamlit as st
import traceback
import pandas as pd
from utils import parse_file, generate_response_json

load_dotenv()

llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")

template = """
Text: {text}
You are an expert MCQ maker. Given the above text, it is your job to\
create a quiz of {number} {type} questions for students in {tone} tone.
Make sure that questions are not repeated and check all the questions to be conforming to the text as well.
Make sure to format your response like the RESPONSE_JSON below and use it as a guide.\
Ensure to make the {number} questions.
Make sure to use traditional Chinese to form your quiz questions.
### RESPONSE_JSON
{response_json}
"""

quiz_generation_prompt = PromptTemplate(
    template=template,
    input_variables= ["text", "number", "type", "tone", "response_json"]
)

quiz_chain = LLMChain(
    llm=llm, prompt=quiz_generation_prompt, output_key="quiz", verbose=True
)

llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")

template = """You are an expert. Given a quiz for students.\
You need to evaluate complexity of the questions and give a complete analysis of the quiz if the students 
will be able to understand the questions and answer them. Only use at max 50 words for complexity analysis.
If quiz is not at par with the cognitive and analytical abilities of the students,\
update the quiz questions which need to be changed and change the tone such that it perfectly fits the students abilities. 
Quiz:
{quiz}
Critique from an expert of the above quiz:
Make sure to use traditional Chinese to form your response."""

quiz_evaluation_prompt = PromptTemplate(
    template=template,
    input_variables= ["quiz"]
)

review_chain = LLMChain(
    llm=llm, prompt=quiz_evaluation_prompt, output_key="review", verbose=True
)

generate_evaluate_chain = SequentialChain(
    chains= [quiz_chain, review_chain],
    input_variables=["text", "number", "type", "tone", "response_json"],
    output_variables=["quiz", "review"],
    verbose=True,
)


def add_to_history(question_type, quiz_data, user_answers, correct_answers):
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = []
    st.session_state.quiz_history.append({
        "question_type": question_type,
        "quiz_data": quiz_data,
        "user_answers": user_answers,
        "correct_answers": correct_answers
    })


st.title("AI出題教師👩‍🏫")

# Create a form using st.form
with st.form("user_inputs"):
    # File upload
    uploaded_file = st.file_uploader("請上傳PDF或TXT檔")

    if uploaded_file is not None:
        # Store the uploaded file in session state
        st.session_state.uploaded_file = uploaded_file

    # Input fields
    question_count = st.number_input("選擇題題數", min_value=3, max_value=20)

    question_type = st.selectbox(label="出題類型", options=["選擇題","是非題", "問答題"])

    question_tone = st.text_input("輸入出題特色", max_chars=100, placeholder="simple")

    button = st.form_submit_button("生成考題📄")



if button:
    if 'uploaded_file' not in st.session_state:
        st.error("請上傳檔案")
    elif not question_count or not question_type or not question_tone:
        st.error("請填寫所有欄位")
    else:
        with st.spinner("Loading..."):
            try:
                # Assuming parse_file is a function to extract text from the uploaded file
                text = parse_file(st.session_state.uploaded_file)

                # Generate the response JSON based on the question type and count
                RESPONSE_JSON = generate_response_json(question_count, question_type)

                # Generate and evaluate the chain
                response = generate_evaluate_chain(
                    {
                        "text": text,
                        "number": question_count,
                        "type": question_type,
                        "tone": question_tone,
                        "response_json": json.dumps(RESPONSE_JSON),
                    }
                )
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                st.error("Error")
            else:
                if isinstance(response, dict):
                    quiz_str = response.get("quiz", None)
                    if quiz_str is not None:
                        quiz = json.loads(quiz_str)  # Ensure quiz is parsed from JSON string to dictionary
                        st.session_state.quiz = quiz
                        st.session_state.question_type = question_type  # Initialize question_type in session state
                        if question_type in ["選擇題", "是非題"]:
                            st.session_state.correct_answers = {
                                key: value["correct"] for key, value in quiz.items() if isinstance(value, dict) and "correct" in value
                            }
                        else:
                            st.session_state.correct_answers = {
                                key: value["answer"] for key, value in quiz.items() if isinstance(value, dict) and "answer" in value
                            }
                        st.session_state.user_answers = {}
                else:
                    st.write(response)

if 'quiz' in st.session_state:
    st.title("Quiz")
    quiz = st.session_state.quiz
    user_answers = st.session_state.user_answers
    option_labels = ['A', 'B', 'C', 'D']
    for key, value in quiz.items():
        if isinstance(value, dict):  # Ensure each value is a dictionary
            if st.session_state.question_type == "選擇題":
                options = list(value["options"].values())
                labeled_options = [f"{option_labels[i]}: {option}" for i, option in enumerate(options)]
                user_answer = st.radio(f"Q{key}: {value['mcq']}", labeled_options, key=key)
                user_answers[key] = user_answer.split(': ')[0]  # Get the label (e.g., A, B, C, D)
            elif st.session_state.question_type == "是非題":
                user_answer = st.radio(f"Q{key}: {value['statement']}", ["True", "False"], key=key)
                user_answers[key] = user_answer.split(': ')[0]  # Get the label (e.g., A, B)
            elif st.session_state.question_type == "問答題":
                user_answer = st.text_area(f"Q{key}: {value['question']}", key=key)
                user_answers[key] = user_answer
    st.session_state.user_answers = user_answers

    if st.button("繳交試卷"):
        if st.session_state.question_type in ["選擇題", "是非題"]:
            correct_answers = st.session_state.correct_answers
            score = sum(1 for key in correct_answers if user_answers[key] == correct_answers[key])
            st.write(f"Score: {score}/{len(correct_answers)}")
        else:
            correct_answers = st.session_state.correct_answers
        
        for key in quiz:
            if isinstance(quiz[key], dict):  # Ensure each value is a dictionary
                question = quiz[key].get('mcq') or quiz[key].get('statement') or quiz[key].get('question')
                st.write(f"Q{key}: {question}")
                st.write(f"Your answer: {user_answers[key]}")
                if st.session_state.question_type in ["選擇題", "是非題"]:
                    st.write(f"Correct answer: {st.session_state.correct_answers[key]}")
                else:
                    st.write(f"Correct answer: {st.session_state.correct_answers[key]}")
        add_to_history(question_type, st.session_state.quiz, user_answers, st.session_state.correct_answers)
        del st.session_state.quiz
        del st.session_state.correct_answers
        del st.session_state.user_answers

