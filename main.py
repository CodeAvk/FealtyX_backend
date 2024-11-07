from flask import Flask, jsonify, request, abort, render_template
import threading
import requests

app = Flask(__name__)

# In-memory data structure to store student information
students = {}
current_id = 1
lock = threading.Lock()

# Helper function to generate a new unique student ID
def get_new_id():
    global current_id
    with lock:
        new_id = current_id
        current_id += 1
    return new_id

# Helper function to integrate with Ollama and generate student summary
def generate_summary(student):
    # Customize the prompt for Ollama
    prompt = f"Generate a short summary for the following student: Name: {student['name']}, Age: {student['age']}, Email: {student['email']}."
    try:
        # Send the prompt to Ollama's local API
        response = requests.post(
            "http://localhost:port/ollama",  # Replace with correct Ollama endpoint
            json={"prompt": prompt}
        )
        if response.status_code == 200:
            return response.json().get("response", "No summary available")
        else:
            return "Failed to generate summary from Ollama"
    except Exception as e:
        return str(e)

# Route to render the frontend
@app.route('/')
def index():
    return render_template('index.html')

# Route to create a new student
@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "age", "email")):
        abort(400, "Invalid student data")

    student_id = get_new_id()
    students[student_id] = {
        "id": student_id,
        "name": data['name'],
        "age": data['age'],
        "email": data['email']
    }
    return jsonify(students[student_id]), 201

# Route to get all students
@app.route('/students', methods=['GET'])
def get_all_students():
    return jsonify(list(students.values()))

# Route to get a student by ID
@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = students.get(student_id)
    if not student:
        abort(404, "Student not found")
    return jsonify(student)

# Route to update a student by ID
@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = students.get(student_id)
    if not student:
        abort(404, "Student not found")

    data = request.get_json()
    if not data or not all(k in data for k in ("name", "age", "email")):
        abort(400, "Invalid student data")

    student['name'] = data['name']
    student['age'] = data['age']
    student['email'] = data['email']
    return jsonify(student)

# Route to delete a student by ID
@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = students.pop(student_id, None)
    if not student:
        abort(404, "Student not found")
    return jsonify({"message": "Student deleted successfully"})

# Route to generate a summary of a student by ID using Ollama
@app.route('/students/<int:student_id>/summary', methods=['GET'])
def get_student_summary(student_id):
    student = students.get(student_id)
    if not student:
        abort(404, "Student not found")

    summary = generate_summary(student)
    return jsonify({"summary": summary})

# Error handler for 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Error handler for 400 errors
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

if __name__ == "__main__":
    app.run(debug=True)
