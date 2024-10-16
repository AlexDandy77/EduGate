# from flask import Flask, jsonify, request
# import mysql.connector
# from datetime import datetime
#
# app = Flask(__name__)
#
# # Database connection configuration
# def get_db_connection():
#     return mysql.connector.connect(
#         host='localhost',
#         user='root',
#         password='',
#         database='school_access'
#     )
#
# # ----------------NFC ACCESS----------------
#
# # Route to process access (toggle is_at_school and log entry/exit time)
# @app.route('/process_access', methods=['POST'])
# def process_access():
#     data = request.json
#     uid = data.get('uid')
#
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     cursor.execute('SELECT id, name_surname FROM students WHERE uid = %s', (uid,))
#     result = cursor.fetchone()
#
#     if result:
#         student_id, name_surname = result
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#         # Check the last attendance record
#         cursor.execute(
#             'SELECT entry_time, exit_time FROM attendance WHERE student_id = %s ORDER BY attendance_id DESC LIMIT 1',
#             (student_id,))
#         last_record = cursor.fetchone()
#
#         if last_record and last_record[1] is None:  # No exit time means student is still in school
#             cursor.execute('UPDATE attendance SET exit_time = %s, status = %s WHERE student_id = %s AND exit_time IS NULL',
#                            (current_time, 'Exited', student_id))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return jsonify({"message": f"Goodbye! {name_surname} is leaving. Time: {current_time}"}), 200
#         else:
#             cursor.execute('''INSERT INTO attendance (student_id, entry_time, date, status, entry_method)
#                               VALUES (%s, %s, %s, %s, %s)''',
#                            (student_id, current_time, datetime.now().date(), 'Entered', 'NFC'))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return jsonify({"message": f"Access granted. {name_surname} is entering. Time: {current_time}"}), 200
#     else:
#         cursor.close()
#         conn.close()
#         return jsonify({"error": f"Access denied. UID {uid} not found."}), 404
#
# # ----------------END NFC ACCESS----------------
#
# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import mysql.connector

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Your MySQL username
        password='',  # Your MySQL password
        database='school_access'  # Your database name
    )

# Route to render the dashboard
@app.route('/')
def dashboard():
    return render_template('dashboard.html')


#------------------ USER MANAGEMENT ROUTES ------------------
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.form
    username = data['username']
    password_hash = data['password_hash']
    role = data['role']
    full_name = data['full_name']
    email = data['email']
    phone_number = data['phone_number']
    profile_picture = data['profile_picture']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Insert into the users table
        user_query = """
        INSERT INTO users (username, password_hash, role, full_name, email, phone_number, profile_picture)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(user_query, (username, password_hash, role, full_name, email, phone_number, profile_picture))
        conn.commit()

        # Step 2: Get the user_id of the newly added user
        user_id = cursor.lastrowid  # Fetch the ID of the newly inserted user

        # Step 3: Insert into the corresponding table based on role
        if role == 'Student':
            # Insert into students table
            student_query = "INSERT INTO students (user_id) VALUES (%s)"
            cursor.execute(student_query, (user_id,))

        elif role == 'Parent':
            # Insert into parents table
            parent_query = "INSERT INTO parents (user_id) VALUES (%s)"
            cursor.execute(parent_query, (user_id,))

        elif role == 'Teacher':
            # Insert into parents table
            teacher_query = "INSERT INTO teachers (user_id) VALUES (%s)"
            cursor.execute(teacher_query, (user_id,))

        elif role == 'Admin':
            # Insert into admins table
            admin_query = "INSERT INTO admins (user_id, role) VALUES (%s, %s)"
            cursor.execute(admin_query, (user_id, 'Admin'))

        # Commit the changes to the corresponding table
        conn.commit()

        return jsonify({"message": "User and role-specific record added successfully!"}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Route to search for users
@app.route('/search_users', methods=['GET'])
def search_users():
    search_query = request.args.get('query', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username LIKE %s OR full_name LIKE %s OR email LIKE %s"
        cursor.execute(query, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        users = cursor.fetchall()
        return jsonify(users), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "DELETE FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully!"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END USER MANAGEMENT ROUTES ------------------



#------------------ CLASSES MANAGEMENT ROUTES ------------------
@app.route('/get_classes', methods=['GET'])
def get_classes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch classes
        query = "SELECT class_id, class_name FROM classes"
        cursor.execute(query)
        classes = cursor.fetchall()

        return jsonify(classes), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/add_class', methods=['POST'])
def add_class():
    data = request.form
    class_name = data['class_name']
    description = data['description']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the new class into the classes table
        query = "INSERT INTO classes (class_name, description) VALUES (%s, %s)"
        cursor.execute(query, (class_name, description))
        conn.commit()

        return jsonify({"message": "Class added successfully!"}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/search_classes', methods=['GET'])
def search_classes():
    query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch class details along with the teacher's name
        sql_query = """
            SELECT c.class_id, c.class_name, c.description, c.teacher_id, u.full_name AS teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE c.class_name LIKE %s OR c.description LIKE %s
        """

        # Execute the query with the search pattern
        cursor.execute(sql_query, (f'%{query}%', f'%{query}%'))
        classes = cursor.fetchall()

        return jsonify(classes), 200

    except mysql.connector.Error as err:
        # Log the error to the server console for debugging
        print(f"SQL Error: {err}")
        return jsonify({"error": str(err)}), 500

    except Exception as e:
        # Catch any other exceptions and log them
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/delete_class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the class from the classes table
        delete_class_query = "DELETE FROM classes WHERE class_id = %s"
        cursor.execute(delete_class_query, (class_id,))

        conn.commit()

        return jsonify({"message": "Class deleted successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END CLASSES MANAGEMENT ROUTES ------------------



#------------------ TEACHERS MANAGEMENT ROUTES ------------------
@app.route('/get_teachers', methods=['GET'])
def get_teachers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT teacher_id, full_name FROM teachers JOIN users ON teachers.user_id = users.user_id")
        teachers = cursor.fetchall()
        return jsonify(teachers), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/search_teachers', methods=['GET'])
def search_teachers():
    query = request.args.get('query', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch teacher details
        sql_query = """
            SELECT t.teacher_id, u.user_id, u.full_name, u.email, u.phone_number, u.profile_picture
            FROM teachers t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.teacher_id LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s
        """

        # Execute the query with the search pattern
        cursor.execute(sql_query, (f'%{query}%', f'%{query}%', f'%{query}%'))
        teachers = cursor.fetchall()

        return jsonify(teachers), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END TEACHERS MANAGEMENT ROUTES ------------------



#------------------ PARENTS MANAGEMENT ROUTES ------------------
@app.route('/get_parents', methods=['GET'])
def get_parents():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch parents
        query = """
        SELECT p.parent_id, u.full_name 
        FROM parents p
        JOIN users u ON p.user_id = u.user_id
        """
        cursor.execute(query)
        parents = cursor.fetchall()

        return jsonify(parents), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/search_parents', methods=['GET'])
def search_parents():
    search_query = request.args.get('query', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Updated query to include parent_id
        query = """
        SELECT p.parent_id, u.username, u.full_name, u.email, u.phone_number, u.profile_picture 
        FROM parents p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.parent_id = %s OR u.username LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s
        """

        # If search_query is an integer, use it to search by parent_id
        if search_query.isdigit():
            cursor.execute(query, (search_query, f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute(query, (-1, f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))

        parents = cursor.fetchall()

        return jsonify(parents), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/delete_parent/<int:user_id>', methods=['DELETE'])
def delete_parent(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the parent from the parents table
        delete_parent_query = "DELETE FROM parents WHERE user_id = %s"
        cursor.execute(delete_parent_query, (user_id,))

        # Delete the user from the users table
        delete_user_query = "DELETE FROM users WHERE user_id = %s"
        cursor.execute(delete_user_query, (user_id,))

        conn.commit()

        return jsonify({"message": "Parent deleted successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END PARENTS MANAGEMENT ROUTES ------------------



#------------------ STUDENTS MANAGEMENT ROUTES ------------------
@app.route('/get_students', methods=['GET'])
def get_students():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch students
        cursor.execute("""
                    SELECT s.student_id, u.full_name, u.profile_picture
                    FROM students s
                    JOIN users u ON s.user_id = u.user_id
                """)
        students = cursor.fetchall()

        return jsonify(students), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/search_students', methods=['GET'])
def search_students():
    search_query = request.args.get('query', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Search for students and include their parent's name
        query = """
        SELECT s.student_id, u.username, u.full_name AS student_name, u.profile_picture, c.class_name, u.email, p.parent_id, pu.full_name AS parent_name 
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN classes c ON s.class_id = c.class_id
        LEFT JOIN parents p ON s.parent_id = p.parent_id
        LEFT JOIN users pu ON p.user_id = pu.user_id
        WHERE u.username LIKE %s OR u.full_name LIKE %s OR c.class_name LIKE %s
        """
        cursor.execute(query, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        students = cursor.fetchall()

        return jsonify(students), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END STUDENTS MANAGEMENT ROUTES ------------------



#------------------ LINK ROUTES ------------------
@app.route('/link_student_to_class', methods=['POST'])
def link_student_to_class():
    data = request.form
    student_id = data['student_id']
    class_id = data['class_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the students table with the class_id
        query = "UPDATE students SET class_id = %s WHERE student_id = %s"
        cursor.execute(query, (class_id, student_id))
        conn.commit()

        return jsonify({"message": "Student linked to class successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/link_student_to_parent', methods=['POST'])
def link_student_to_parent():
    data = request.form
    student_id = data['student_id']
    parent_id = data['parent_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the students table with the parent_id
        query = "UPDATE students SET parent_id = %s WHERE student_id = %s"
        cursor.execute(query, (parent_id, student_id))
        conn.commit()

        return jsonify({"message": "Student linked to parent successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/link_class_to_teacher', methods=['POST'])
def link_class_to_teacher():
    class_id = request.form.get('class_id')
    teacher_id = request.form.get('teacher_id')

    if not class_id or not teacher_id:
        return jsonify({"error": "Class ID and Teacher ID are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Update the class to link it with the teacher
        cursor.execute('UPDATE classes SET teacher_id = %s WHERE class_id = %s', (teacher_id, class_id))
        conn.commit()
        return jsonify({'message': 'Class linked to teacher successfully'}), 200

    except mysql.connector.Error as err:
        print(f"SQL Error: {err}")
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#------------------ END LINK ROUTES ------------------

if __name__ == '__main__':
    app.run(debug=True)
