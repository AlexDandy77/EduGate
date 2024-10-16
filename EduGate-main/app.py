from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import datetime


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

        if user and user['password_hash'] == password:  # Consider hashing and checking the password
            session['user_id'] = user['user_id']  # Store user id in session
            session['role'] = user['role']  # Store user role in session

            # Redirect to different dashboards based on role
            if user['role'] == 'Student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'Teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'Parent':
                return redirect(url_for('parents_dashboard'))
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
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # Redirect if user is not logged in

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch student details
    cursor.execute("""
        SELECT u.full_name, u.profile_picture, s.uid 
        FROM users u 
        JOIN students s ON u.user_id = s.user_id 
        WHERE u.user_id = %s
    """, (user_id,))
    user = cursor.fetchone()

    # Fetch attendance records for the student
    cursor.execute("""
        SELECT a.entry_time, a.exit_time, a.face_confirmation 
        FROM attendance a 
        WHERE a.student_id = (SELECT student_id FROM students WHERE user_id = %s) 
        ORDER BY a.entry_time DESC
    """, (user_id,))
    attendance_records = cursor.fetchall()

    conn.close()

    return render_template('student_dashboard.html', user=user, attendance_records=attendance_records)

# ------------------ PARENT DASHBOARD ROUTE ------------------
@app.route('/parent_dashboard')
def parents_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch parent details along with parent_id and profile picture
    cursor.execute("""
        SELECT u.*, p.parent_id 
        FROM users u 
        JOIN parents p ON u.user_id = p.user_id 
        WHERE u.user_id = %s
    """, (user_id,))
    parent = cursor.fetchone()

    if not parent:
        return "Parent not found or not linked properly."

    # Fetch students linked to this parent with their profile pictures
    cursor.execute("""
        SELECT 
            s.student_id,
            u.full_name AS student_full_name,
            u.profile_picture AS student_profile_picture,  -- Fetching student's profile picture
            p.parent_id,
            parent_user.full_name AS parent_full_name,
            parent_user.profile_picture AS parent_profile_picture  -- Fetching parent's profile picture
        FROM 
            students s
        JOIN 
            users u ON s.user_id = u.user_id
        JOIN 
            parents p ON s.parent_id = p.parent_id
        JOIN 
            users parent_user ON p.user_id = parent_user.user_id
        WHERE 
            p.parent_id = %s
        ORDER BY 
            s.student_id;
    """, (parent['parent_id'],))
    students = cursor.fetchall()

    # For each student, fetch their attendance history and calculate stats
    for student in students:
        cursor.execute("""
            SELECT a.entry_time, a.exit_time, a.face_confirmation 
            FROM attendance a
            WHERE a.student_id = %s
            ORDER BY a.entry_time DESC
        """, (student['student_id'],))
        attendance_records = cursor.fetchall()

        student['attendance_records'] = attendance_records

        # Initialize attendance stats
        on_time = late = absent = 0
        total_records = len(attendance_records)

        for record in attendance_records:
            entry_time = record['entry_time']
            if entry_time is None:
                absent += 1
            elif isinstance(entry_time, datetime.datetime):
                if entry_time.time() <= datetime.time(8, 15):
                    on_time += 1
                else:
                    late += 1

        # Avoid division by zero
        if total_records > 0:
            on_time_percentage = (on_time / total_records) * 100
            late_percentage = (late / total_records) * 100
            absent_percentage = (absent / total_records) * 100
        else:
            on_time_percentage = late_percentage = absent_percentage = 0

        student['attendance_stats'] = {
            'on_time': on_time_percentage,
            'late': late_percentage,
            'absent': absent_percentage
        }

    conn.close()
    return render_template('parent_dashboard.html', parent=parent, students=students)




# ------------------ ADMIN DASHBOARD ROUTE ------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))  # Only allow admins to access this page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all users to display in the admin dashboard
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Fetch all classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    # Fetch students for managing class and parent links
    cursor.execute("""
        SELECT s.student_id, s.user_id, u.full_name AS student_name, s.class_id, s.parent_id 
        FROM students s
        JOIN users u ON s.user_id = u.user_id
    """)
    students = cursor.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', users=users, classes=classes, students=students)

# ------------------ ADD USER ROUTE ------------------
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    username = request.form['username']
    password_hash = request.form['password']  # Consider hashing the password
    email = request.form['email']
    phone_number = request.form['phone_number']
    role = request.form['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, email, phone_number, role) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (username, password_hash, full_name, email, phone_number, role))

    conn.commit()
    cursor.close()
    conn.close()

    flash('User added successfully!')
    return redirect(url_for('admin_dashboard'))

# ------------------ LINK STUDENT TO CLASS ROUTE ------------------
@app.route('/link_student_class', methods=['POST'])
def link_student_class():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    class_id = request.form['class_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE students SET class_id = %s WHERE student_id = %s", (class_id, student_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Student linked to class successfully!')
    return redirect(url_for('admin_dashboard'))

# ------------------ LINK STUDENT TO PARENT ROUTE ------------------
@app.route('/link_student_parent', methods=['POST'])
def link_student_parent():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    parent_id = request.form['parent_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE students SET parent_id = %s WHERE student_id = %s", (parent_id, student_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Student linked to parent successfully!')
    return redirect(url_for('admin_dashboard'))

# ------------------ DELETE USER ROUTE ------------------
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash('User deleted successfully!')
    return redirect(url_for('admin_dashboard'))

# ------------------ RECORD ATTENDANCE ROUTE ------------------
@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    student_id = request.form['student_id']
    entry_time = request.form['entry_time']  # Should include date and time
    exit_time = request.form['exit_time']    # Should include date and time
    face_confirmation = request.form['face_confirmation']  # true/false

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (student_id, entry_time, exit_time, face_confirmation) 
        VALUES (%s, %s, %s, %s)
    """, (student_id, entry_time, exit_time, face_confirmation))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# ------------------ VIEW ATTENDANCE ROUTE ------------------
@app.route('/view_attendance/<int:student_id>', methods=['GET'])
def view_attendance(student_id):
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch attendance records for the given student
    cursor.execute("""
        SELECT student_id, uid, entry_time, exit_time, face_confirmation 
        FROM attendance 
        WHERE student_id = %s
    """, (student_id,))
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_attendance.html', records=records)

# ------------------ LOGOUT ROUTE ------------------
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
