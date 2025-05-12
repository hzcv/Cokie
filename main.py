from flask import Flask, render_template, request, jsonify
import requests
import time
import threading

app = Flask(__name__)

BASE_URL = "https://i.instagram.com/api/v1/"
USER_AGENT = "Instagram 123.0.0.21.114 Android"
sending_thread = None
stop_sending = False

def login_with_cookie(cookie):
    """
    Log in to Instagram using a provided cookie.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": cookie,
    }
    response = requests.get(BASE_URL + "accounts/current_user/", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("user", {}).get("username", "Unknown"), headers
    else:
        return None, None

def send_group_message(headers, group_id, messages, delay):
    """
    Send messages to a specified Instagram group ID repeatedly with a delay.
    """
    global stop_sending
    message_url = BASE_URL + "direct_v2/threads/broadcast/text/"

    for message in messages:
        if stop_sending:
            break

        payload = {
            "thread_ids": f"[{group_id}]",
            "text": message,
        }
        requests.post(message_url, headers=headers, data=payload)
        time.sleep(delay)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        global sending_thread, stop_sending
        stop_sending = False
        cookie = request.form.get("cookie")
        group_id = request.form.get("target_id")
        delay = float(request.form.get("delay", 5))
        message_file = request.files.get("message_file")

        # Verify login
        username, headers = login_with_cookie(cookie)
        if not username:
            return jsonify({"success": False, "message": "Invalid cookie. Login failed."})

        # Parse message file
        messages = message_file.read().decode("utf-8").splitlines()

        # Start the messaging thread
        sending_thread = threading.Thread(
            target=send_group_message, args=(headers, group_id, messages, delay)
        )
        sending_thread.start()

        return jsonify({"success": True, "message": f"Logged in as {username}. Messaging started."})

    return render_template("index.html")

@app.route("/stop", methods=["POST"])
def stop_sending_messages():
    global stop_sending
    stop_sending = True
    return jsonify({"success": True, "message": "Message sending stopped."})

if __name__ == "__main__":
    app.run(debug=True)
