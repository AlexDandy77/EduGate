import cv2
import face_recognition
import mysql.connector
import time

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="school_access"
    )

# Load known faces and student IDs from the database
def load_known_faces():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT student_id, profile_picture FROM students s JOIN users u ON s.user_id = u.user_id WHERE profile_picture IS NOT NULL")
    known_faces = []
    student_ids = []

    for row in cursor.fetchall():
        image_path = f"static/profile_pictures/{row['profile_picture']}"
        image = face_recognition.load_image_file(image_path)

        # Get the face encoding from the image
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_faces.append(encodings[0])  # Use the first face found
            student_ids.append(row['student_id'])

    cursor.close()
    conn.close()
    return known_faces, student_ids

# Initialize known faces and student IDs
known_face_encodings, known_student_ids = load_known_faces()

# Load OpenCV's Haar Cascade for faster face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize camera
video_capture = cv2.VideoCapture(0)

# Set the resolution to lower to increase FPS
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize the time for the delay
last_recognition_time = time.time()

print("Starting live face recognition... Press 'q' to quit.")

while True:
    # Capture a frame from the video feed
    ret, frame = video_capture.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Check if 1 second has passed since the last recognition
    current_time = time.time()
    if current_time - last_recognition_time >= 1:
        # Update the last recognition time
        last_recognition_time = current_time

        # Convert the frame to grayscale (needed for Haar Cascade)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces using Haar Cascade
        face_locations = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # For each face detected, find the face encoding and compare it with known encodings
        for (x, y, w, h) in face_locations:
            # Convert the face bounding box into the format expected by face_recognition (top, right, bottom, left)
            top, right, bottom, left = y, x + w, y + h, x

            # Get the face encoding for this detected face
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame, [(top, right, bottom, left)])

            if len(face_encodings) > 0:
                face_encoding = face_encodings[0]

                # Compare this encoding with the known encodings
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                best_match_index = None if len(face_distances) == 0 else face_distances.argmin()

                if matches[best_match_index]:
                    student_id = known_student_ids[best_match_index]
                    print(f"Recognized student ID: {student_id}")

                    # Check the latest attendance record for this student
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor(dictionary=True)

                        # Retrieve the most recent attendance record for this student where face_confirmation is False
                        cursor.execute("""
                            SELECT * FROM attendance 
                            WHERE student_id = %s AND face_confirmation = FALSE 
                            ORDER BY entry_time DESC 
                            LIMIT 1
                        """, (student_id,))

                        record = cursor.fetchone()

                        if record:
                            # Update the face_confirmation to TRUE
                            cursor.execute("""
                                UPDATE attendance 
                                SET face_confirmation = TRUE 
                                WHERE attendance_id = %s
                            """, (record['attendance_id'],))

                            conn.commit()
                            print(f"Updated face_confirmation for student ID: {student_id}")

                    except mysql.connector.Error as err:
                        print(f"Database error: {err}")
                    finally:
                        if conn.is_connected():
                            cursor.close()
                            conn.close()

            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the video feed with rectangles around detected faces
    cv2.imshow("Live Face Recognition", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close windows
video_capture.release()
cv2.destroyAllWindows()
