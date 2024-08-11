import csv
import random

def load_questions_from_csv(file_path):
    questions = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            question = {
                "question": row["Questions"],
                "answers": [
                    {"text": row["A"], "correct": row["Correct Option"] == "A"},
                    {"text": row["B"], "correct": row["Correct Option"] == "B"},
                    {"text": row["C"], "correct": row["Correct Option"] == "C"},
                    {"text": row["D"], "correct": row["Correct Option"] == "D"}
                ]
            }
            questions.append(question)
    return questions

#********************************************************************************
#BIOLOGY MCQs
def get_random_questions_bio(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
    # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions
#********************************************************************************
#CHEMISTRY MCQs
def get_random_questions_chem(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
    # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions

#********************************************************************************
#PHYSICS MCQs

def get_random_questions_phy(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
    # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions

#********************************************************************************
#LOGICAL MCQs

def get_random_questions_logical(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
    # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions

#********************************************************************************
#ENGLISH MCQs
def get_random_questions_eng(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
    # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions

#********************************************************************************
#MIXED MCQs
def get_random_questions_mixed(file_path, num_questions=20):
    all_questions = load_questions_from_csv(file_path)
   # Ensure num_questions does not exceed the number of available questions
    if num_questions > len(all_questions):
        num_questions = len(all_questions)
    random_questions = random.sample(all_questions, num_questions)
    return random_questions
