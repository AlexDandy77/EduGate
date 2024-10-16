from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key


# ------------------ DATABASE CONNECTION FUNCTION ------------------
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Your MySQL username
        password='',  # Your MySQL password
        database='school_access'  # Your database name
    )


# ------------------ MAIN INDEX ROUTE ------------------
@app.route('/')
def index():
    return render_template('index.html')


# ------------------ LOGIN ROUTE ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phonenumber']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
        user = cursor.fetchone()

        if user and user['password_hash'] == password:  # You might want to hash and check the password
            session['user_id'] = user['user_id']  # Store user id in session
            session['role'] = user['role']  # Store user role in session

            if user['role'] == 'Student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'Teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'Parent':
                return redirect(url_for('parent_dashboard'))
            elif user['role'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid role')
                return redirect(url_for('login'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')


# ------------------ STUDENT DASHBOARD ROUTE ------------------
@app.route('/student_dashboard')
def student_dashboard():
    user_id = session.get('user_id')  # Assuming the user_id is stored in session after login
    if not user_id:
        return redirect('/login')  # Redirect if user is not logged in

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Updated query to fetch data from users and students tables
    cursor.execute("""
        SELECT u.full_name, u.profile_picture, s.class_id 
        FROM users u 
        JOIN students s ON u.user_id = s.user_id 
        WHERE u.user_id = %s
    """, (user_id,))
    user = cursor.fetchone()

    conn.close()

    return render_template('student_dashboard.html', user=user)


# ------------------ PARENT DASHBOARD ROUTE ------------------
@app.route('/parent_dashboard')
def parent_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        # Fetch parent details (from the users table)
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        # Fetch students related to the parent, joining users and students
        cursor.execute("""
            SELECT s.*, u.full_name as parent_name 
            FROM students s 
            JOIN users u ON s.parent_id = u.user_id 
            WHERE u.user_id = %s
        """, (user_id,))
        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template('parent_dashboard.html', user=user, students=students)
    else:
        return redirect(url_for('login'))


# ------------------ ADMIN DASHBOARD ROUTE ------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))  # Only allow admins to access this page

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch all users to display in the admin dashboard
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Fetch all classes for the admin to manage
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    # Fetch students for managing class and parent links
    cursor.execute("""
        SELECT s.student_id, s.user_id, u.full_name AS student_name, s.class_id, s.parent_id 
        FROM students s
        JOIN users u ON s.user_id = u.user_id
    """)
    students = cursor.fetchall()

    connection.close()

    return render_template('admin_dashboard.html', users=users, classes=classes, students=students)


# ------------------ ROUTE TO ADD USERS ------------------
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    username = request.form['username']
    password_hash = request.form['password']  # Consider hashing this password
    email = request.form['email']
    phone_number = request.form['phone_number']
    role = request.form['role']

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, email, phone_number, role) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (username, password_hash, full_name, email, phone_number, role))

    connection.commit()
    cursor.close()
    connection.close()

    flash('User added successfully!')
    return redirect(url_for('admin_dashboard'))


# ------------------ ROUTE TO LINK STUDENTS TO CLASSES ------------------
@app.route('/link_student_class', methods=['POST'])
def link_student_class():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    class_id = request.form['class_id']

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE students SET class_id = %s WHERE student_id = %s
    """, (class_id, student_id))

    connection.commit()
    cursor.close()
    connection.close()

    flash('Student linked to class successfully!')
    return redirect(url_for('admin_dashboard'))


# ------------------ ROUTE TO LINK STUDENTS TO PARENTS ------------------
@app.route('/link_student_parent', methods=['POST'])
def link_student_parent():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    parent_id = request.form['parent_id']

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE students SET parent_id = %s WHERE student_id = %s
    """, (parent_id, student_id))

    connection.commit()
    cursor.close()
    connection.close()

    flash('Student linked to parent successfully!')
    return redirect(url_for('admin_dashboard'))


# ------------------ ROUTE TO DELETE USERS ------------------
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

    connection.commit()
    cursor.close()
    connection.close()

    flash('User deleted successfully!')
    return redirect(url_for('admin_dashboard'))


# ------------------ ROUTE TO RECORD ATTENDANCE ------------------
@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    student_id = request.form['student_id']
    date = request.form['date']
    status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
        (student_id, date, status)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_dashboard'))


# ------------------ ROUTE TO CHECK NFC READER ------------------
@app.route('/check_nfc_reader')
def check_nfc_reader():
    try:
        # Execute the command to check connected USB devices
        result = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the ACS NFC reader is mentioned in the output
        nfc_reader_connected = 'ACS' in result.stdout  # Adjust this check based on your device specifics

        return jsonify({'connected': nfc_reader_connected})
    except Exception as e:
        print(f"Error checking NFC reader: {e}")
        return jsonify({'connected': False})


# ------------------ LOGOUT ROUTE ------------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
