from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import csv
import json
from flask import Flask, render_template, request, redirect, url_for
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import plotly.graph_objs as go
import plotly.offline as pyo
import random 
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from mcqs import get_random_questions_bio
from mcqs import get_random_questions_chem
from mcqs import get_random_questions_phy
from mcqs import get_random_questions_logical
from mcqs import get_random_questions_eng
from mcqs import get_random_questions_mixed
import os
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'


#****************************************************************************
#FOR BLOG THING
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#***************************************************************************
# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="DB@educatify001",
        database="educatify_db"
    )

# Path to the CSV files
CSV_FILE_PATH_bio = 'CSV/biology.csv'
CSV_FILE_PATH_chem = 'CSV/chemistry.csv'
CSV_FILE_PATH_eng = 'CSV/english.csv'
CSV_FILE_PATH_logical = 'CSV/logical.csv'
CSV_FILE_PATH_phy = 'CSV/physics.csv'
CSV_FILE_PATH_mixed = 'CSV/MixMCQs.csv'

#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************LOGIN/SIGNUP*************************************************************************
# Route to display forgot password form
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM user WHERE username=%s AND email=%s", (username, email))
                user = cursor.fetchone()
                if user:
                    # Store the username in the session for the reset password route
                    session['reset_username'] = username
                    return redirect(url_for('reset_password'))
                else:
                    error = "No account found with the provided username and email."
                    return render_template('LOGIN/forgot_password.html', error=error)
        except Error as err:
            error = f"Error: {err}"
            return render_template('forgot_password.html', error=error)
        finally:
            connection.close()
    return render_template('LOGIN/forgot_password.html')

# Route to display reset password form
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_username' not in session:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            error = "Passwords do not match."
            return render_template('LOGIN/reset_password.html', error=error)
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)
        username = session.pop('reset_username')
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE user SET password=%s WHERE username=%s", (hashed_password, username))
                connection.commit()
                flash('Password reset successful. Please log in with your new password.', 'success')
                return redirect(url_for('login'))
        except Error as err:
            error = f"Error: {err}"
            return render_template('reset_password.html', error=error)
        finally:
            connection.close()
    return render_template('LOGIN/reset_password.html')

# Route for login (for reference)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_username = 'team-edu-mzu'
        admin_password = '#MAKEitHAPPEN'
        if username == admin_username and password == admin_password:
            session['username'] = admin_username
            session['user_id'] = 'admin'
            return redirect(url_for('add_article'))
        
        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
                user = cursor.fetchone()
                if user and check_password_hash(user['password'], password):
                    session['username'] = user['username']
                    session['user_id'] = user['ID']
                    return redirect(url_for('dash'))
                else:
                    flash('Invalid credentials. Please try again.', 'danger')
        except Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            connection.close()
    return render_template('LOGIN/login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Check if the email already exists
                cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Make sure to fetch all results before returning
                    cursor.fetchall()  # Ensure no unread results remain
                    return render_template('LOGIN/signup.html', email_error='Email already exists. Please use a different email or log in.')
                
                # Insert the new user if the email does not exist
                cursor.execute("INSERT INTO user (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
                connection.commit()
                
            flash('Signup successful! Welcome to the platform.', 'success')
            return redirect(url_for('login'))
        except Error as err:
            flash(f"Error: {err}", 'danger')
            return redirect(url_for('signup'))
        finally:
            if connection.is_connected():
                connection.close()
    return render_template('LOGIN/signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    #return redirect(url_for('login'))
    return render_template('landingpage.html')

#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************PROFILE OF USER*************************************************************************
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    user_id = session['user_id']
    user = None

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM user WHERE ID=%s", (user_id,))
            user = cursor.fetchone()
            if request.method == 'POST':
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

                cursor.execute("""
                    UPDATE user SET username=%s, email=%s, password=%s WHERE ID=%s
                """, (username, email, hashed_password, user_id))
                connection.commit()

                # Update session data
                session['username'] = username

                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
    finally:
        connection.close()

    return render_template('profile.html', user=user)

#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************LANDING PAGE*************************************************************************

@app.route('/')
def home():
        return render_template('landingpage.html')

#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************DASHBOARD****************************************************************************
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    return render_template('DASHBOARD/dashboard.html', username=username)

@app.route('/mocktests')
def mocktests():
    return render_template('DASHBOARD/mocktests.html')

@app.route('/SubjMCQs')
def SubjMCQs():
    return render_template('DASHBOARD/SubjMCQs.html')

@app.route('/dashboard')
def dash():
    if 'username' in session:
        return render_template('DASHBOARD/Dashboard.html', username=session['username'])
    return redirect(url_for('login'))

# ##################SCOREBOARD##################
@app.route('/scores')
def show_scores():
    user_id = session.get('user_id')  # Example: retrieving from session
    if not user_id:
        return redirect(url_for('login'))
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch subject scores
            cursor.execute("SELECT Biology, Chemistry, Physics, English, Logical, Total FROM SubjScore WHERE ID = %s", (user_id,))
            scores = cursor.fetchone()
            # Fetch mock test results (fetch the latest entry)
            cursor.execute("SELECT Marks, Timestamp FROM MockTests WHERE ID = %s ORDER BY Timestamp DESC LIMIT 1", (user_id,))
            mock_test = cursor.fetchone()
        # Set default values if no scores are found
        if not scores:
            scores = {'Biology': 0, 'Chemistry': 0, 'Physics': 0, 'English': 0, 'Logical': 0, 'Total': 0}
        # Set default values if no mock test results are found
        if not mock_test:
            mock_test = {'Marks': 0, 'Timestamp': None}
        return render_template('DASHBOARD/scores.html', scores=scores, mock_test=mock_test)
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        connection.close()


# ##################TOP SCORERS######################
@app.route('/top-users')
def top_users():
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch top 10 users based on highest Total score
            cursor.execute("""
                SELECT user.username, MAX(SubjScore.Total) as Total
                FROM user 
                JOIN SubjScore ON user.ID = SubjScore.ID 
                GROUP BY user.username
                ORDER BY Total DESC 
                LIMIT 10
            """)
            top_users = cursor.fetchall()

            # Fetch top 10 users based on highest Marks in mock tests
            cursor.execute("""
                SELECT user.username, MAX(MockTests.Marks) as Marks
                FROM user 
                JOIN MockTests ON user.ID = MockTests.ID 
                GROUP BY user.username
                ORDER BY Marks DESC 
                LIMIT 10
            """)
            top_mock_test_users = cursor.fetchall()

        return render_template('DASHBOARD/top_users.html', top_users=top_users, top_mock_test_users=top_mock_test_users)
    except Error as err:
        return f"Error: {err}"
    finally:
        connection.close()

    
#*******************************************************************************************************
#*******************************************************************************************************
#*********************************SUBJ MCQS*************************************************************
#*********************************BIOLOGY***************************************************************
@app.route('/BiologyQuiz')
def BIO():
    return render_template('MCQS/BiologyQuiz.html')

@app.route('/BIO_questions', methods=['GET']) 
def BIO_get_questions():
    random_questions = get_random_questions_bio(CSV_FILE_PATH_bio, 20)
    return jsonify(random_questions)

@app.route('/BIO_submit', methods=['POST'])
def BIO_submit_answer():
    data = request.json
    current_question_index = data['currentQuestionIndex']
    selected_answer = data['selectedAnswer']
    questions = get_random_questions_bio(CSV_FILE_PATH_bio, 20)  # Get the same set of random questions
    is_correct = any(answer['text'] == selected_answer and answer['correct'] for answer in questions[current_question_index]['answers'])
    response = {"correct": is_correct}
    if current_question_index + 1 < len(questions):
        next_question = questions[current_question_index + 1]
        response["nextQuestion"] = next_question
    else:
        response["end"] = True
    return jsonify(response)

@app.route('/save_score', methods=['POST'])
def bio_save_score():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json
        new_score = data.get('score')
        print(f"Adding Biology score for user {user_id}: {new_score}")  # Debug print

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Check if the user already has a record in SubjScore
                cursor.execute("SELECT Biology FROM SubjScore WHERE ID=%s", (user_id,))
                result = cursor.fetchone()
                if result:
                    # Retrieve the current Biology score
                    current_score = result['Biology'] if result['Biology'] is not None else 0
                    updated_score = current_score + new_score

                    # Update the existing Biology score by adding the new score
                    cursor.execute(
                        "UPDATE SubjScore SET Biology=%s WHERE ID=%s",
                        (updated_score, user_id)
                    )
                else:
                    # Insert a new record with the initial Biology score
                    cursor.execute(
                        "INSERT INTO SubjScore (ID, Biology) VALUES (%s, %s)",
                        (user_id, new_score)
                    )
                # Update the Total field to sum all subjects for the user
                cursor.execute(
                    "UPDATE SubjScore SET Total = COALESCE(Logical, 0) + COALESCE(English, 0) + COALESCE(Physics, 0) + COALESCE(Biology, 0) + COALESCE(Chemistry, 0) WHERE ID=%s",
                    (user_id,)
                )
                connection.commit()
            return jsonify({"message": "Biology score updated successfully"})
        except Error as err:
            print(f"Database error: {err}")  # Debug print
            return jsonify({"error": str(err)}), 500
        finally:
            connection.close()
    else:
        print("User not logged in")  # Debug print
        return jsonify({"error": "User not logged in"}), 401
    
#*********************************CHEMISTRY************************************************************
@app.route('/ChemistryQuiz')
def CHEM():
    return render_template('MCQS/ChemistryQuiz.html')

@app.route('/CHEM_questions', methods=['GET'])
def CHEM_get_questions():
    random_questions = get_random_questions_chem(CSV_FILE_PATH_chem, 20)
    return jsonify(random_questions)

@app.route('/CHEM_submit', methods=['POST'])
def CHEM_submit_answer():
    data = request.json
    current_question_index = data['currentQuestionIndex']
    selected_answer = data['selectedAnswer']
    questions = get_random_questions_chem(CSV_FILE_PATH_chem, 20)  # Get the same set of random questions
    is_correct = any(answer['text'] == selected_answer and answer['correct'] for answer in questions[current_question_index]['answers'])
    response = {"correct": is_correct}
    if current_question_index + 1 < len(questions):
        next_question = questions[current_question_index + 1]
        response["nextQuestion"] = next_question
    else:
        response["end"] = True
    return jsonify(response)

@app.route('/save_chemistry_score', methods=['POST'])
def chemistry_save_score():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json
        new_score = data.get('score')
        print(f"Adding Chemistry score for user {user_id}: {new_score}")  # Debug print
        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Check if the user already has a record in SubjScore
                cursor.execute("SELECT Chemistry FROM SubjScore WHERE ID=%s", (user_id,))
                result = cursor.fetchone()
                if result:
                    # Retrieve the current Chemistry score
                    current_score = result['Chemistry'] if result['Chemistry'] is not None else 0
                    updated_score = current_score + new_score
                    # Update the existing Chemistry score by adding the new score
                    cursor.execute(
                        "UPDATE SubjScore SET Chemistry=%s WHERE ID=%s",
                        (updated_score, user_id)
                    )
                else:
                    # Insert a new record with the initial Chemistry score
                    cursor.execute(
                        "INSERT INTO SubjScore (ID, Chemistry) VALUES (%s, %s)",
                        (user_id, new_score)
                    )
                # Update the Total field to sum all subjects for the user
                cursor.execute(
                    "UPDATE SubjScore SET Total = COALESCE(Logical, 0) + COALESCE(English, 0) + COALESCE(Physics, 0) + COALESCE(Biology, 0) + COALESCE(Chemistry, 0) WHERE ID=%s",
                    (user_id,)
                )
                connection.commit()
            return jsonify({"message": "Chemistry score updated successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")  # Debug print
            return jsonify({"error": str(err)}), 500
        finally:
            connection.close()
    else:
        print("User not logged in")  # Debug print
        return jsonify({"error": "User not logged in"}), 401

#*********************************PHYSICS**************************************************************
@app.route('/PhysicsQuiz')
def PHY():
    return render_template('MCQS/PhysicsQuiz.html')

@app.route('/PHY_questions', methods=['GET'])
def PHY_get_questions():
    random_questions = get_random_questions_phy(CSV_FILE_PATH_phy, 20)
    return jsonify(random_questions)

@app.route('/PHY_submit', methods=['POST'])
def PHY_submit_answer():
    data = request.json
    current_question_index = data['currentQuestionIndex']
    selected_answer = data['selectedAnswer']
    questions = get_random_questions_phy(CSV_FILE_PATH_phy, 20)  # Get the same set of random questions
    is_correct = any(answer['text'] == selected_answer and answer['correct'] for answer in questions[current_question_index]['answers'])
    response = {"correct": is_correct}
    if current_question_index + 1 < len(questions):
        next_question = questions[current_question_index + 1]
        response["nextQuestion"] = next_question
    else:
        response["end"] = True
    return jsonify(response)

@app.route('/save_physics_score', methods=['POST'])
def save_physics_score():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json
        new_score = data.get('score')
        print(f"Adding Physics score for user {user_id}: {new_score}")  # Debug print

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Check if the user already has a record in SubjScore
                cursor.execute("SELECT Physics FROM SubjScore WHERE ID=%s", (user_id,))
                result = cursor.fetchone()
                if result:
                    # Retrieve the current Physics score
                    current_score = result['Physics'] if result['Physics'] is not None else 0
                    updated_score = current_score + new_score

                    # Update the existing Physics score by adding the new score
                    cursor.execute(
                        "UPDATE SubjScore SET Physics=%s WHERE ID=%s",
                        (updated_score, user_id)
                    )
                else:
                    # Insert a new record with the initial Physics score
                    cursor.execute(
                        "INSERT INTO SubjScore (ID, Physics) VALUES (%s, %s)",
                        (user_id, new_score)
                    )
                # Update the Total field to sum all subjects for the user
                cursor.execute(
                    "UPDATE SubjScore SET Total = COALESCE(Logical, 0) + COALESCE(English, 0) + COALESCE(Physics, 0) + COALESCE(Biology, 0) + COALESCE(Chemistry, 0) WHERE ID=%s",
                    (user_id,)
                )
                connection.commit()
            return jsonify({"message": "Physics score updated successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")  # Debug print
            return jsonify({"error": str(err)}), 500
        finally:
            connection.close()
    else:
        print("User not logged in")  # Debug print
        return jsonify({"error": "User not logged in"}), 401

#*********************************LOGICAL**************************************************************
@app.route('/LogicalQuiz')
def LOGICAL():
    return render_template('MCQS/LogicalQuiz.html')

# API endpoint to get a random set of questions
@app.route('/LOGICAL_questions', methods=['GET'])
def LOGICAL_get_questions():
    random_questions = get_random_questions_chem(CSV_FILE_PATH_logical, 20)
    return jsonify(random_questions)

# API endpoint to submit an answer and get the next question or score
@app.route('/submit', methods=['POST'])
def LOGICAL_submit_answer():
    data = request.json
    current_question_index = data['currentQuestionIndex']
    selected_answer = data['selectedAnswer']
    questions = get_random_questions_chem(CSV_FILE_PATH_logical, 20)  # Get the same set of random questions
    is_correct = any(answer['text'] == selected_answer and answer['correct'] for answer in questions[current_question_index]['answers']) 
    if is_correct:
        response = {"correct": True}
    else:
        response = {"correct": False}
    if current_question_index + 1 < len(questions):
        next_question = questions[current_question_index + 1]
        response["nextQuestion"] = next_question
    else:
        response["end"] = True
    return jsonify(response)

@app.route('/save_logical_score', methods=['POST'])
def save_logical_score():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json
        new_score = data.get('score')
        print(f"Adding Logical score for user {user_id}: {new_score}")  # Debug print

        connection = get_db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Check if the user already has a record in SubjScore
                cursor.execute("SELECT Logical FROM SubjScore WHERE ID=%s", (user_id,))
                result = cursor.fetchone()
                if result:
                    # Retrieve the current Logical score
                    current_score = result['Logical'] if result['Logical'] is not None else 0
                    updated_score = current_score + new_score

                    # Update the existing Logical score by adding the new score
                    cursor.execute(
                        "UPDATE SubjScore SET Logical=%s WHERE ID=%s",
                        (updated_score, user_id)
                    )
                else:
                    # Insert a new record with the initial Logical score
                    cursor.execute(
                        "INSERT INTO SubjScore (ID, Logical) VALUES (%s, %s)",
                        (user_id, new_score)
                    )
                # Update the Total field to sum all subjects for the user
                cursor.execute(
                    "UPDATE SubjScore SET Total = COALESCE(Logical, 0) + COALESCE(English, 0) + COALESCE(Physics, 0) + COALESCE(Biology, 0) + COALESCE(Chemistry, 0) WHERE ID=%s",
                    (user_id,)
                )

                connection.commit()
            return jsonify({"message": "Logical score updated successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")  # Debug print
            return jsonify({"error": str(err)}), 500
        finally:
            connection.close()
    else:
        print("User not logged in")  # Debug print
        return jsonify({"error": "User not logged in"}), 401
#*********************************ENGLISH**************************************************************
@app.route('/EnglishQuiz')
def ENG():
    return render_template('MCQS/EnglishQuiz.html')

# API endpoint to get a random set of questions
@app.route('/ENG_questions', methods=['GET'])
def ENG_get_questions():
    random_questions = get_random_questions_chem(CSV_FILE_PATH_eng, 20)
    return jsonify(random_questions)

# API endpoint to submit an answer and get the next question or score
@app.route('/submit', methods=['POST'])
def ENG_submit_answer():
    data = request.json
    current_question_index = data['currentQuestionIndex']
    selected_answer = data['selectedAnswer']
    questions = get_random_questions_chem(CSV_FILE_PATH_eng, 20)  # Get the same set of random questions
    is_correct = any(answer['text'] == selected_answer and answer['correct'] for answer in questions[current_question_index]['answers'])
    if is_correct:
        response = {"correct": True}
    else:
        response = {"correct": False}
    if current_question_index + 1 < len(questions):
        next_question = questions[current_question_index + 1]
        response["nextQuestion"] = next_question
    else:
        response["end"] = True
    return jsonify(response)

@app.route('/save_english_score', methods=['POST'])
def save_english_score():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json
        new_score = data.get('score')
        print(f"Adding English score for user {user_id}: {new_score}")  # Debug print
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Check if the user already has a record in SubjScore
            cursor.execute("SELECT English FROM SubjScore WHERE ID=%s", (user_id,))
            result = cursor.fetchone()
            if result:
                current_score = result['English'] if result['English'] is not None else 0
                updated_score = current_score + new_score
                # Update the existing English score by adding the new score
                cursor.execute(
                    "UPDATE SubjScore SET English=%s WHERE ID=%s",
                    (updated_score, user_id)
                )
            else:
                # Insert a new record with the initial English score
                cursor.execute(
                    "INSERT INTO SubjScore (ID, English) VALUES (%s, %s)",
                    (user_id, new_score)
                )
            # Update the Total field to sum all subjects for the user
            cursor.execute(
                "UPDATE SubjScore SET Total = COALESCE(Logical, 0) + COALESCE(English, 0) + COALESCE(Physics, 0) + COALESCE(Biology, 0) + COALESCE(Chemistry, 0) WHERE ID=%s",
                (user_id,)
            )
            db.commit()
            cursor.close()
            db.close()
            return jsonify({"message": "English score updated successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")  # Debug print
            return jsonify({"error": str(err)}), 500
    else:
        print("User not logged in")  # Debug print
        return jsonify({"error": "User not logged in"}), 401

#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************MOCK TEST****************************************************************************
# Function to read MCQs from a single CSV file and distribute them into different subject lists
def read_mcqs_from_file(filename):
    mcqs = []
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mcq = {
                'Question': row['Questions'],
                'Option A': row['A'],
                'Option B': row['B'],
                'Option C': row['C'],
                'Option D': row['D'],
                'Correct Answer': row['Correct Option'],
                'is_correct': None
            }
            mcqs.append(mcq)

    # Divide the MCQs into different subject lists based on the specified counts
    biology_mcqs = mcqs[:68]
    chemistry_mcqs = mcqs[68:122]
    physics_mcqs = mcqs[122:176]
    english_mcqs = mcqs[176:194]
    logical_reasoning_mcqs = mcqs[194:200]

    return biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs

def get_all_mcqs(biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs):
    all_mcqs = biology_mcqs + chemistry_mcqs + physics_mcqs + english_mcqs + logical_reasoning_mcqs
    return all_mcqs

VALID_CODES = {
    4: 'PREMIUMCODE4',
    5: 'PREMIUMCODE5',
    6: 'PREMIUMCODE6'
}

@app.route('/MOCKEXAM')
def MOCKEXAM():
    if 'username' in session:
        exam_num = request.args.get('exam_num', default=1, type=int)
        # Check if the exam number is within the allowed range
        if exam_num in [1, 2, 3, 4, 5, 6]:
            return render_template('MOCKEXAM/MDCAT.html', username=session['username'], exam_num=exam_num)
        else:
            return redirect(url_for('index'))  # Redirect to index if exam number is invalid
    else:
        return redirect(url_for('index'))  # Redirect to index if not logged in

# Route to handle code validation for exams 4, 5, and 6
@app.route('/validate_code', methods=['POST'])
def validate_code():
    if 'username' in session:
        entered_code = request.form.get('code')
        correct_code = 'PREMIUMCODE'  # Replace with the actual code
        # Check if the code is correct
        if entered_code == correct_code:
            exam_num = request.form.get('exam_num')
            return redirect(url_for('MOCKEXAM', exam_num=exam_num))
        else:
            # Redirect to the same page with an error message
            return render_template('MOCKEXAM/MDCAT.html', username=session['username'], exam_num=request.form.get('exam_num'), error='Invalid code. Please try again.')
    else:
        return redirect(url_for('index'))


@app.route('/MDCAT', methods=['GET', 'POST'])
def MDCATEXAM():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Session expired. Please log in again.')
            return redirect(url_for('index'))

        exam_num = request.args.get('exam_num', default=1, type=int)
        user_id = session['user_id']
        filename = f'CSV/mockexam{exam_num}.csv'
        biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs = read_mcqs_from_file(filename)
        all_mcqs = get_all_mcqs(biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs)

        for mcq in all_mcqs:
            user_answer = request.form.get(mcq['Question'])
            correct_answer = mcq['Correct Answer']
            mcq['is_correct'] = user_answer == correct_answer
            mcq['user_answer'] = user_answer if not mcq['is_correct'] else None

        total_mcqs, total_correct, subject_wise_correct = calculate_results(all_mcqs, biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs)
        bar_chart_div = generate_bar_chart(subject_wise_correct)
        pie_chart_div = generate_pie_chart(total_mcqs, total_correct)
        subject_pie_chart_div = generate_subject_pie_chart(subject_wise_correct)

        insert_quiz_result(user_id, total_correct)

        # Storing the result data in the session
        session['result_data'] = {
            'total_mcqs': total_mcqs,
            'total_correct': total_correct,
            'subject_wise_correct': subject_wise_correct,
            'bar_chart_div': bar_chart_div,
            'pie_chart_div': pie_chart_div,
            'subject_pie_chart_div': subject_pie_chart_div
        }

        return render_template('MOCKEXAM/result.html', all_mcqs=all_mcqs, total_correct=total_correct, 
                               subject_wise_correct=subject_wise_correct, bar_chart_div=bar_chart_div, 
                               pie_chart_div=pie_chart_div, subject_pie_chart_div=subject_pie_chart_div)

    exam_num = request.args.get('exam_num', default=1, type=int)
    filename = f'CSV/mockexam{exam_num}.csv'
    biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs = read_mcqs_from_file(filename)
    all_mcqs = get_all_mcqs(biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs)
    return render_template('MOCKEXAM/MDCATEXAM.html', all_mcqs=all_mcqs, username=session['username'])

@app.route('/result')
def result():
    if 'user_id' not in session:
        flash('Session expired. Please log in again.')
        return redirect(url_for('index'))
    user_id = session['user_id']
    result_data = session.get('result_data')
    if not result_data:
        flash('Session expired. Please start the quiz again.')
        return redirect(url_for('MOCKEXAM'))
    return render_template('MOCKEXAM/result.html', **result_data)

def insert_quiz_result(user_id, total_correct):
    date = datetime.now().date()  # Get the current date without time
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO MockTests (ID, Marks, Timestamp)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            Marks = %s, Timestamp = %s
            """,
            (user_id, total_correct, date, total_correct, date)
        )
        db.commit()
        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")

def get_user_result(user_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT Marks, Timestamp FROM MockTests WHERE ID = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()
        
        if result:
            return {
                'total_correct': result['Marks'],
                'timestamp': result['Timestamp'].strftime("%Y-%m-%d")  # Convert timestamp to string in desired format
            }
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def calculate_results(all_mcqs, biology_mcqs, chemistry_mcqs, physics_mcqs, english_mcqs, logical_reasoning_mcqs):
    total_mcqs = len(all_mcqs)
    total_correct = sum(mcq['is_correct'] for mcq in all_mcqs)
    subject_wise_correct = {
        'Biology': sum(mcq['is_correct'] for mcq in biology_mcqs),
        'Chemistry': sum(mcq['is_correct'] for mcq in chemistry_mcqs),
        'Physics': sum(mcq['is_correct'] for mcq in physics_mcqs),
        'English': sum(mcq['is_correct'] for mcq in english_mcqs),
        'Logical Reasoning': sum(mcq['is_correct'] for mcq in logical_reasoning_mcqs)
    }
    return total_mcqs, total_correct, subject_wise_correct

# Generate bar chart using Plotly
def generate_bar_chart(subject_wise_correct):
    subjects = list(subject_wise_correct.keys())
    correct_counts = list(subject_wise_correct.values())
    bar_data = [go.Bar(x=subjects, y=correct_counts, marker=dict(color=['blue', 'green', 'orange', 'red', 'purple']))]
    layout = go.Layout(title='Subject-wise Correct MCQs', xaxis=dict(title='Subjects'), yaxis=dict(title='Number of Correct MCQs'))
    fig = go.Figure(data=bar_data, layout=layout)
    bar_chart_div = pyo.plot(fig, output_type='div', include_plotlyjs=False)
    return bar_chart_div

# Generate pie chart using Plotly
def generate_pie_chart(total_mcqs, total_correct):
    incorrect_count = total_mcqs - total_correct
    labels = ['Correct MCQs', 'Incorrect MCQs']
    sizes = [total_correct, incorrect_count]
    colors = ['green', 'red']
    pie_data = [go.Pie(labels=labels, values=sizes, marker=dict(colors=colors))]
    layout = go.Layout(title='Correct vs Incorrect MCQs')
    fig = go.Figure(data=pie_data, layout=layout)
    pie_chart_div = pyo.plot(fig, output_type='div', include_plotlyjs=False)
    return pie_chart_div

# Generate pie chart for subject-wise distribution using Plotly
def generate_subject_pie_chart(subject_wise_correct):
    labels = list(subject_wise_correct.keys())
    values = list(subject_wise_correct.values())
    colors = ['blue', 'green', 'orange', 'red', 'purple']
    pie_data = [go.Pie(labels=labels, values=values, marker=dict(colors=colors))]
    layout = go.Layout(title='Subject-wise Correct MCQs Distribution')
    fig = go.Figure(data=pie_data, layout=layout)
    subject_pie_chart_div = pyo.plot(fig, output_type='div', include_plotlyjs=False)
    return subject_pie_chart_div

#*****************************************************************************************
#******************************************************************************************
# ALL THE CODE FOR YOUTUBE SEARCH FEATURE 

# Directly embed the API key here
API_KEY = 'AIzaSyC2cueTnlXMoHS35wuWmL892yk4KwaZyTo'

# List of non-educational keywords
NON_EDUCATIONAL_KEYWORDS = [
    'songs', 'movies', 'sex', 'porn', 'nudity', 'memes', 'gaming', 'entertainment',
    'funny', 'comedy', 'music', 'dance', 'pranks', 'fashion', 'vlogs', 'tv shows',
    'films', 'drama', 'celebrity', 'gossip', 'sports', 'news', 'trailers', 'concerts',
    'clips', 'horror', 'action', 'adventure', 'romance', 'sci-fi', 'fantasy', 'thriller',
    'crime', 'mystery', 'reality tv', 'talk shows', 'sketches', 'animation', 'cartoons', 'movie', 'song'
]

def is_educational_query(query):
    query_lower = query.lower()
    for keyword in NON_EDUCATIONAL_KEYWORDS:
        if keyword in query_lower:
            return False
    return True

def search_youtube_videos(query, max_results=30):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    try:
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=max_results,
            order='viewCount',
            videoDuration='medium',  # Exclude videos shorter than 4 minutes
            safeSearch='strict'  # Filter out adult content
        ).execute()
    except HttpError as e:
        print(f'An error occurred: {e}')
        return None

    videos = []
    for search_result in search_response.get('items', []):
        video_id = search_result['id']['videoId']
        title = search_result['snippet']['title']
        description = search_result['snippet']['description']
        thumbnail_url = search_result['snippet']['thumbnails']['high']['url']
        video_info = {
            'title': title,
            'video_id': video_id,
            'description': description,
            'thumbnail_url': thumbnail_url
        }
        videos.append(video_info)

    return videos

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    if not query:
        return redirect(url_for('index'))

    # Concatenate "tutorial" to the search query
    query = query + " tutorial"

    if not is_educational_query(query):
        return render_template('SEARCH/error.html', message="Please enter a proper educational keyword.")

    return redirect(url_for('results', query=query))

@app.route('/results')
def results():
    query = request.args.get('query')
    videos = search_youtube_videos(query)

    if videos is None:
        return render_template('SEARCH/error.html', message="An error occurred while searching for videos.")

    return render_template('SEARCH/results.html', query=query, videos=videos)

@app.route('/watch/<video_id>')
def watch(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    try:
        video_response = youtube.videos().list(
            part='snippet,contentDetails',
            id=video_id
        ).execute()
        video_info = video_response['items'][0]['snippet']
    except HttpError as e:
        print(f'An error occurred: {e}')
        return render_template('SEARCH/error.html', message="An error occurred while fetching the video details.")
    
    return render_template('SEARCH/watch.html', video_id=video_id, video_info=video_info)



#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************CHAPTER WISE ************************************************************************
@app.route('/ChapterWiseMcqs')
def ChapterWiseMcqs():
    return render_template('DASHBOARD/ChapterWiseMcqs.html')


#************************************************************************************************************************************
#************************************************************************************************************************************
#***********************************************INTERN CERTIFICATE VERIFICATION ************************************************************************

@app.route('/certverification')
def CertificatesVerification():
    return render_template('certverification.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
