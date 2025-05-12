from flask import Flask, render_template, request, jsonify
import requests
import time
import threading

app = Flask(name)

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
    response = requests.post(message_url, headers=headers, data=payload)  
    time.sleep(delay)

@app.route("/", methods=["GET", "POST"])
def index():
if request.method == "POST":
global sending_thread, stop_sending
stop_sending = False
cookie = request.form.get("cookie")
group_id = request.form.get("group_id")
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

if name == "main":
app.run(debug=True)

<!DOCTYPE html>  <html lang="en">  
<head>  
    <meta charset="UTF-8">  
    <meta name="viewport" content="width=device-width, initial-scale=1.0">  
    <title>Instagram Messaging</title>  
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>  
    <style>  
        body {  
            font-family: Arial, sans-serif;  
            margin: 0;  
            padding: 0;  
            background: linear-gradient(to right, #6a11cb, #2575fc);  
            color: #fff;  
        } 
    .container {  
        max-width: 600px;  
        margin: 50px auto;  
        background: rgba(255, 255, 255, 0.1);  
        border-radius: 10px;  
        padding: 20px;  
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);  
    }  

    h1 {  
        text-align: center;  
        margin-bottom: 20px;  
    }  

    form {  
        display: flex;  
        flex-direction: column;  
    }  

    label {  
        margin-top: 10px;  
        font-weight: bold;  
    }  

    input, select, textarea {  
        margin-top: 5px;  
        padding: 10px;  
        border: none;  
        border-radius: 5px;  
        font-size: 16px;  
    }  

    input[type="file"] {  
        padding: 5px;  
        background: #fff;  
    }  

    button {  
        margin-top: 20px;  
        padding: 10px;  
        border: none;  
        border-radius: 5px;  
        background: #2575fc;  
        color: white;  
        font-size: 18px;  
        cursor: pointer;  
        transition: background 0.3s;  
    }  

    button:hover {  
        background: #6a11cb;  
    }  
</style>

</head>  
<body>  
    <div class="container">  
        <h1>Instagram Auto Messaging</h1>  
        <form id="messagingForm">  
            <label for="cookie">Instagram Cookie:</label>  
            <input type="text" id="cookie" name="cookie" placeholder="Enter Instagram Cookie" required>  <label for="target_type">Target Type:</label>  
        <select id="target_type" name="target_type" required>  
            <option value="inbox">Inbox</option>  
            <option value="group">Group</option>  
        </select>  

        <label for="target_id">Target Username/ID:</label>  
        <input type="text" id="target_id" name="target_id" placeholder="Enter Username or Group ID" required>  

        <label for="delay">Delay (seconds):</label>  
        <input type="number" id="delay" name="delay" placeholder="Enter delay between messages" required>  

        <label for="message_file">Message File (txt):</label>  
        <input type="file" id="message_file" name="message_file" accept=".txt" required>  

        <button type="submit">Start Messaging</button>  
    </form>  
</div>  

<script>  
    document.getElementById("messagingForm").addEventListener("submit", function (e) {  
        e.preventDefault();  

        const formData = new FormData();  
        const cookie = document.getElementById("cookie").value;  
        const targetType = document.getElementById("target_type").value;  
        const targetId = document.getElementById("target_id").value;  
        const delay = document.getElementById("delay").value;  
        const messageFile = document.getElementById("message_file").files[0];  

        if (!messageFile) {  
            Swal.fire("Error", "Please select a valid message file!", "error");  
            return;  
        }  

        formData.append("cookie", cookie);  
        formData.append("target_type", targetType);  
        formData.append("target_id", targetId);  
        formData.append("delay", delay);  
        formData.append("message_file", messageFile);  

        fetch("/", {  
            method: "POST",  
            body: formData,  
        })  
        .then((response) => response.json())  
        .then((data) => {  
            if (data.success) {  
                Swal.fire("Success", data.message, "success");  
            } else {  
                Swal.fire("Error", data.message, "error");  
            }  
        })  
        .catch((error) => {  
            Swal.fire("Error", "An unexpected error occurred!", "error");  
            console.error("Error:", error);  
        });  
    });  
</script>

</body>  
</html>
