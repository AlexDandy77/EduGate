from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ------------------ DATABASE CONNECTION FUNCTION ------------------
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Your MySQL username
        password='',  # Your MySQL password
        database='school_access'  # Your database name
    )

# ------------------ DASHBOARD ROUTE ------------------
@app.route('/')
def dashboard():
    return render_template('admin_dashboard.html')

# ------------------ USER MANAGEMENT ROUTES ------------------
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.form
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Insert into the users table
        user_query = """
        INSERT INTO users (username, password_hash, role, full_name, email, phone_number, profile_picture)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(user_query, (
            data['username'], data['password_hash'], data['role'], data['full_name'],
            data['email'], data['phone_number'], data['profile_picture']
        ))
        conn.commit()

        # Step 2: Get the user_id of the newly added user
        user_id = cursor.lastrowid

        # Step 3: Insert into the corresponding table based on role
        if data['role'] == 'Student':
            cursor.execute("INSERT INTO students (user_id) VALUES (%s)", (user_id,))
        elif data['role'] == 'Parent':
            cursor.execute("INSERT INTO parents (user_id) VALUES (%s)", (user_id,))
        elif data['role'] == 'Teacher':
            cursor.execute("INSERT INTO teachers (user_id) VALUES (%s)", (user_id,))
        elif data['role'] == 'Admin':
            cursor.execute("INSERT INTO admins (user_id, role) VALUES (%s, 'Admin')", (user_id,))

        conn.commit()

        return jsonify({"message": "User and role-specific record added successfully!"}), 201

    except Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


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
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "DELETE FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully!"}), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ------------------ CLASSES MANAGEMENT ROUTES ------------------
@app.route('/get_classes', methods=['GET'])
def get_classes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT class_id, class_name FROM classes"
        cursor.execute(query)
        classes = cursor.fetchall()

        return jsonify(classes), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/add_class', methods=['POST'])
def add_class():
    data = request.form
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO classes (class_name, description) VALUES (%s, %s)"
        cursor.execute(query, (data['class_name'], data['description']))
        conn.commit()

        return jsonify({"message": "Class added successfully!"}), 201
    except Error as err:
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

        sql_query = """
            SELECT c.class_id, c.class_name, c.description, c.teacher_id, u.full_name AS teacher_name
            FROM classes c
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE c.class_name LIKE %s OR c.description LIKE %s
        """
        cursor.execute(sql_query, (f'%{query}%', f'%{query}%'))
        classes = cursor.fetchall()

        return jsonify(classes), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/delete_class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        delete_class_query = "DELETE FROM classes WHERE class_id = %s"
        cursor.execute(delete_class_query, (class_id,))
        conn.commit()

        return jsonify({"message": "Class deleted successfully!"}), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ------------------ TEACHERS MANAGEMENT ROUTES ------------------
@app.route('/get_teachers', methods=['GET'])
def get_teachers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT teacher_id, full_name FROM teachers JOIN users ON teachers.user_id = users.user_id"
        cursor.execute(query)
        teachers = cursor.fetchall()

        return jsonify(teachers), 200
    except Error as err:
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

        sql_query = """
            SELECT t.teacher_id, u.user_id, u.full_name, u.email, u.phone_number, u.profile_picture
            FROM teachers t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.teacher_id LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s
        """
        cursor.execute(sql_query, (f'%{query}%', f'%{query}%', f'%{query}%'))
        teachers = cursor.fetchall()

        return jsonify(teachers), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ------------------ PARENTS MANAGEMENT ROUTES ------------------
@app.route('/get_parents', methods=['GET'])
def get_parents():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT p.parent_id, u.full_name 
        FROM parents p
        JOIN users u ON p.user_id = u.user_id
        """
        cursor.execute(query)
        parents = cursor.fetchall()

        return jsonify(parents), 200
    except Error as err:
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

        query = """
        SELECT p.parent_id, u.username, u.full_name, u.email, u.phone_number, u.profile_picture 
        FROM parents p
        JOIN users u ON p.user_id = u.user_id
        WHERE u.username LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s
        """
        cursor.execute(query, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        parents = cursor.fetchall()

        return jsonify(parents), 200
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)
