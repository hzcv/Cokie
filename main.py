import requests
import time
import threading
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

BASE_URL = "https://i.instagram.com/api/v1/"
USER_AGENT = "Instagram 123.0.0.21.114 Android"

class InstagramBot:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Cookie": cookie
        })
        self.stop_monitoring = False

    def get_current_user(self):
        """Get the current logged-in user's details"""
        response = self.session.get(BASE_URL + "accounts/current_user/")
        if response.status_code == 200:
            user_data = response.json()
            return user_data["user"]["username"]
        return None

    def get_group_chats(self):
        """Fetch all group chat threads"""
        response = self.session.get(BASE_URL + "direct_v2/inbox/")
        if response.status_code == 200:
            threads = response.json().get('inbox', {}).get('threads', [])
            return threads
        return []

    def send_message(self, thread_id, message):
        """Send a message to the group chat"""
        message_url = BASE_URL + "direct_v2/threads/broadcast/text/"
        payload = {
            "thread_ids": f"[{thread_id}]",
            "text": message
        }
        response = self.session.post(message_url, data=payload)
        return response

    def monitor_and_reply(self):
        """Monitor and reply to messages in the group chats"""
        username = self.get_current_user()
        if not username:
            print("Login failed.")
            return

        print(f"Logged in as {username}")

        while not self.stop_monitoring:
            threads = self.get_group_chats()
            for thread in threads:
                if 'messages' in thread:
                    for message in thread['messages']:
                        # Skip messages sent by the bot or owner
                        if message['user']['username'] == username:
                            continue
                        if message['user']['is_private'] == True:  # Owner detection logic, adjust if needed
                            continue

                        # Send a reply
                        reply_message = f"@{message['user']['username']} OYY MSG MAT KR"
                        thread_id = thread['thread_id']
                        self.send_message(thread_id, reply_message)
                        print(f"Replied to @{message['user']['username']} in group {thread_id}")
            
            time.sleep(5)  # Sleep for 5 seconds before checking again

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.stop_monitoring = True


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cookie = request.form.get('cookie')
        if not cookie:
            return jsonify({"error": "Cookie is required."}), 400
        
        bot = InstagramBot(cookie)
        
        # Run the bot in a separate thread to avoid blocking the main thread
        thread = threading.Thread(target=bot.monitor_and_reply)
        thread.start()

        return render_template("index.html", message="Bot started monitoring group chats.")

    return render_template("index.html", message="Enter your Instagram cookie to start the bot.")


@app.route("/stop", methods=["POST"])
def stop_monitoring():
    cookie = request.form.get('cookie')
    if not cookie:
        return jsonify({"error": "Cookie is required."}), 400
    
    bot.stop_monitoring = True

    return jsonify({"message": "Bot stopped monitoring group chats."})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Change port to 5001 if needed
