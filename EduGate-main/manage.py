import pymysql
import time
from datetime import datetime
from smartcard.System import readers
from smartcard.util import toHexString

# Database connection
db = pymysql.connect(host='localhost', user='root', password='', database='school_access')
cursor = db.cursor()


# Main NFC tracking function
def track_nfc():
    last_uid = None  # Track the last detected UID
    last_read_time = 0  # Track the last read time

    while True:
        uid = read_nfc_card()

        # Check if a card was detected and apply 2-second timeout
        if uid and (uid != last_uid or (time.time() - last_read_time) >= 2):
            student_id = get_student_id_by_uid(uid)
            if student_id:
                # Log entry if student ID exists
                log_attendance_entry(student_id, uid)
                print(f"User with UID {uid} entered the system.")
                last_uid = uid  # Update the last UID
                last_read_time = time.time()  # Update the last read time
            else:
                print(f"No student associated with UID {uid}. Please register.")
        else:
            if uid:
                print(f"UID {uid} detected, but cooldown is active.")

        # Sleep for a short period to avoid excessive CPU usage
        time.sleep(0.1)


# Function to check if a student with a given UID exists in the database
def get_student_id_by_uid(uid):
    sql = "SELECT student_id FROM students WHERE uid = %s"
    cursor.execute(sql, (uid,))
    result = cursor.fetchone()
    return result[0] if result else None

# Function to log the NFC entry into the database
def log_attendance_entry(student_id, uid):
    sql = """
        INSERT INTO attendance (student_id, uid, entry_time, exit_time, session_number, face_confirmation)
        VALUES (%s, %s, NOW(), NULL, 1, FALSE)
    """
    cursor.execute(sql, (student_id, uid))
    db.commit()

# NFC reading function
def read_nfc_card():
    r = readers()
    if len(r) == 0:
        print("No NFC reader detected")
        return None

    reader = r[0]
    connection = reader.createConnection()

    try:
        connection.connect()
        GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # Command to get UID from card
        data, sw1, sw2 = connection.transmit(GET_UID)

        if sw1 == 0x90 and sw2 == 0x00:
            uid = toHexString(data)
            return uid
        else:
            print("Failed to read card UID.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Main NFC tracking function
def track_nfc():
    last_uid = None  # Track the last detected UID
    last_read_time = 0  # Track the last read time

    while True:
        uid = read_nfc_card()

        if uid and (uid != last_uid or (time.time() - last_read_time) >= 10):
            student_id = get_student_id_by_uid(uid)
            if student_id:
                # Log entry if student ID exists
                log_attendance_entry(student_id, uid)
                print(f"User with UID {uid} entered the system.")
                last_uid = uid  # Update the last UID
                last_read_time = time.time()  # Update the last read time
            else:
                print(f"No student associated with UID {uid}. Please register.")
        else:
            if uid:
                print(f"UID {uid} detected, but cooldown is active.")

if __name__ == "__main__":
    try:
        track_nfc()
    except KeyboardInterrupt:
        print("Session ended.")
    finally:
        cursor.close()
        db.close()
