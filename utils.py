import PyPDF2
import json
import traceback

def parse_file(file):
    if file.name.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except PyPDF2.utils.PdfReadError:
            raise Exception("讀取PDF檔時有誤")
        
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    else:
        raise Exception(
            "不支援檔案格式。僅支援PDF或TXT檔。"
        )
    

def get_table_data(quiz_str, question_type):
    try:
        # convert the quiz from a str to dict
        quiz_dict = json.loads(quiz_str)
        quiz_table_data = []
        # Iterate over the quiz dictionary and extract the required information
        for key, value in quiz_dict.items():
            if question_type == "選擇題":
                mcq = value["mcq"]
                options = " | ".join(
                    [
                        f"{option}: {option_value}"
                        for option, option_value in value["options"].items()
                    ]
                )
                correct = value["correct"]
                quiz_table_data.append({"MCQ": mcq, "Choices": options, "Correct": correct})
            elif question_type == "是非題":
                statement = value["statement"]
                correct = value["correct"]
                quiz_table_data.append({"Statement": statement, "Correct": correct})
            elif question_type == "問答題":
                question = value["question"]
                quiz_table_data.append({"Question": question, "Answer": value.get("answer", "N/A")})
        return quiz_table_data
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        return False

def generate_response_json(question_count, question_type):
    if question_type == "選擇題":
        return {
            str(i): {
                "no": str(i),
                "mcq": f"multiple choice question {i}",
                "options": {
                    "A": "choice here",
                    "B": "choice here",
                    "C": "choice here",
                    "D": "choice here",
                },
                "correct": "correct answer",
            } for i in range(1, question_count + 1)
        }
    elif question_type == "是非題":
        return {
            str(i): {
                "no": str(i),
                "statement": f"true/false statement {i}",
                "correct": "True" if i % 2 == 0 else "False",
            } for i in range(1, question_count + 1)
        }
    elif question_type == "問答題":
        return {
            str(i): {
                "no": str(i),
                "question": f"question {i}",
                "answer": f"answer {i}",
            } for i in range(1, question_count + 1)
        }
    else:
        return {}
