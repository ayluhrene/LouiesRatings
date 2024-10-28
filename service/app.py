from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from database import db, User, ClassData, ClassDetails, fetch_grade_distribution_data
import threading
import pandas as pd
import os
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("service")

# turn to true to start filling the database with class information when the server starts
FILL_DB_WITH_CLASS_DATA = False

# only fill if sqlite database does not already exists on start up
if not os.path.isfile('table.db'):
    FILL_DB_WITH_CLASS_DATA = True

# For testing only

# ====================================
# Create app
# ====================================
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# maybe change from sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///table.db'

# bind the database to backend
db.init_app(app)

# create database tables
with app.app_context():
    db.create_all()
# ====================================

# ====================================
# BACKEND FUNCTIONS
# ====================================
@app.route('/', methods=['GET', 'POST'])
def send_message():

    # checks if form is for post request
    if request.method == 'POST':

        # all post functions to the backend will have to do data manipulation 
        # think of POST as a way to send data to the backend to make changes to the data

        # usually a different return here 
        users = [{'id': 1, 'username': 'Alice'}, {'id': 2, 'username': 'Bob'}]
        return jsonify(users), 200

    # we cannot send render templates as we are not using flask python templates on the frontend
    return jsonify(message="Hello From Backend"), 200

@app.route('/search', methods=['POST'])
def search():

    # checks if the request is a get type also think Post as a way to send data to the backend to make changes to the data 
    # or just get data from the backend in this case
    if request.method == 'POST':

        # Get the JSON data from the request
        data = request.get_json() 

        # Extract the search query from the JSON data
        search_query = data.get('query')

        # usually a different return here 
        users = [{'id': 1, 'username': 'Alice'}, {'id': 2, 'username': 'Bob'}, {'id': 3, 'username': search_query}]

        # Return the mock users to test and 200 means a successful request
        return jsonify(users), 200
    
@app.route('/add_user', methods=["GET", "POST"])
def profile():
    if request.method == 'POST':
        data = request.json  # Get JSON data from the request

        # get username and password
        username = data.get('username')
        password = data.get('password')

        # create an object of the User class of models
        # and store data as a row in our datatable
        if username != '' and password != '':
            p = User(username=username, password=password)
            db.session.add(p)
            db.session.commit()

        return jsonify({'message': 'Data received!', 'data': {'name': username}}), 200
    
@app.route('/professor', methods=['GET'])
def get_professor_data():
    instructor_name = request.args.get('name')
    # Testing
    # app.logger.debug(f"Received request for instructor: {instructor_name}")

    if instructor_name:
        # Split the instructor name into last name and first name and search database for any matching names
        last_name, first_name = instructor_name.split(", ")
        courses = ClassData.query.filter(
            ClassData.instructor_name.ilike(f"%{last_name}%"),
            ClassData.instructor_name.ilike(f"%{first_name}%")
        ).all()
    else:
        return jsonify({"error": "Professor not found"}), 404

    # Extract full instructor name from the first matched course, add space following comma
    full_instructor_name = courses[0].instructor_name

    course_data = [
        {
            "semester": course.semester,
            "subject": course.subject,
            "class_name": course.class_name,
            "section": course.section,
            "grades": {
                "A": course.a,
                "B": course.b,
                "C": course.c,
                "D": course.d,
                "F": course.f,
                "P": course.p,
                "W": course.w
            },
        }
        for course in courses
    ]

    # Include the full instructor name in the response
    return jsonify({"professor": full_instructor_name, "courses": course_data})

@app.route('/class', methods=['GET'])
def get_class_data():
    class_id = request.args.get('classId') 
    if not class_id:
        return jsonify({"error": "Class ID is required"}), 400

    # Fetch class data from the database
    class_data = ClassData.query.filter_by(class_name=class_id).first() 

    if class_data:
        return jsonify({"class": {
            "title": f"{class_data.subject} {class_data.class_name}",
            "code": class_data.class_name,
            "instructor": class_data.instructor_name,
            "grades": {
                "A": class_data.a,
                "B": class_data.b,
                "C": class_data.c,
                "D": class_data.d,
                "F": class_data.f,
                "P": class_data.p,
                "W": class_data.w,
            },
        }}), 200
    else:
        return jsonify({"error": "Class not found"}), 404
    
@app.route('/class/details', methods=['GET'])
def get_class_details():
    class_name = request.args.get('classId')
    
    # Find class by class_name
    class_data = ClassDetails.query.filter_by(class_name=class_name).first()

    if class_data:
        return jsonify({
            "class": {
                "title": class_data.class_title,
                "description": class_data.description,
                "instructor": class_data.instructor
            }
        }), 200
    else:
        return jsonify({"error": "Class not found"}), 404



@app.route('/get_graph_data', methods=["GET", "POST"])
def get_graph_data():
    if request.method == 'POST':
        request_data = request.json  # Get JSON data from the request

        # get specfic class data
        search_by = request_data.get('search_by')

        # get specific data from search name
        grade_data = list()

        search_name = request_data.get(search_by)

        if search_by == 'class_name':
            grade_data = ClassData.query.filter_by(class_name=search_name).all()

        else:
            grade_data = ClassData.query.filter_by(instructor_name=search_name).all()

        if len(grade_data) == 0:
            # nothing found, so return empty data
            return jsonify({"grade": "empty", "sum":0})
        
        # create pandas data frame user the data, only get relevant information
        grade_distributions= pd.DataFrame([
            {
                'A': data.a,
                'B': data.b,
                'C': data.c,
                'D': data.d,
                'F': data.f,
                'P': data.p,
                'W': data.w
            } for data in grade_data
        ])

        # add row for column sums
        grade_distributions.loc["sum"] = grade_distributions.sum(numeric_only=True)

        # remove all rows except for the last two
        grade_distributions = grade_distributions.iloc[[-1]]

        # transpose, and make the index a column for grades
        grade_distributions = grade_distributions.T.reset_index(drop=False).rename(columns={"index":"grade"})
        
        return jsonify(grade_distributions.to_json(orient='records'))

# ====================================

def fill_db_with_class_data():
    logger.info("\nWebscraper running...")
    # only run this to fill database with class data
    with app.app_context():
        fetch_grade_distribution_data(db)
    logger.info("\nWebscraper finished...")

if __name__ == '__main__':
    if FILL_DB_WITH_CLASS_DATA:
        thread = threading.Thread(target=fill_db_with_class_data)
        thread.start()

    app.run(host='0.0.0.0', port=8080)