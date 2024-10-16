import time
import threading
import requests
from smartcard.System import readers
from smartcard.util import toHexString

# Flag to control the NFC listening loop
listening = True

# Define the backend server URL
SERVER_URL = 'http://127.0.0.1:5000'

def send_uid_to_server(uid):
    """Send the UID to the Flask server for processing."""
    try:
        # Send the UID to the /process_access endpoint
        api_url = f"{SERVER_URL}/process_access"
        response = requests.post(api_url, json={'uid': uid})

        # Handle server response
        if response.status_code == 200:
            print("Record processed successfully.")
            print(response.json())  # Display the message from server.py
        else:
            print(f"Failed to process record. Status Code: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"Error sending UID to server: {e}")

def listen_for_stop_signal():
    """Thread to listen for the user input to stop NFC listening."""
    global listening
    while True:
        user_input = input("Press 'q' to stop listening: \n\n")
        if user_input.lower() == 'q':
            listening = False
            print("Stopping NFC listening...")
            break

def listen_for_cards():
    """Continuously listen for NFC cards and send UID to server."""
    r = readers()
    if len(r) < 1:
        print("\nError: No NFC readers available!")
        return

    print("\nAvailable readers: ", r)
    reader = r[0]
    print("Using: ", reader)

    connection = reader.createConnection()

    last_scanned = {}
    BLOCK_DURATION = 1  # Block duration in seconds

    print("Scanning active...")

    # Start a separate thread for user input to stop listening
    stop_signal_thread = threading.Thread(target=listen_for_stop_signal)
    stop_signal_thread.daemon = True  # This ensures the thread will exit when the main thread does
    stop_signal_thread.start()

    try:
        while listening:  # Keep listening until 'q' is pressed
            try:
                # Try connecting to the card (this will fail if no card is present)
                connection.connect()
                # Get UID Command
                get_uid_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                data, sw1, sw2 = connection.transmit(get_uid_cmd)
                if (sw1, sw2) == (0x90, 0x0):  # If operation completed successfully
                    uid = toHexString(data)
                    current_time = time.time()

                    # Check if the UID has been scanned in the last BLOCK_DURATION seconds
                    if uid in last_scanned:
                        time_diff = current_time - last_scanned[uid]
                        if time_diff < BLOCK_DURATION:
                            continue

                    # Send UID to the server to process access
                    send_uid_to_server(uid)
                    last_scanned[uid] = current_time

                # After reading the card, disconnect to allow for new card
                connection.disconnect()

            except Exception as e:
                # Wait for the next card if no card is present
                time.sleep(0.1)  # Polling interval (adjust as needed)

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        print("\nNFC listening stopped.")


# Main function
if __name__ == "__main__":
    listen_for_cards()
