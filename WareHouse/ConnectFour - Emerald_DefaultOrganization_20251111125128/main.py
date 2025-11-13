'''
A Flask dashboard application that dynamically displays a greeting message based on user selection, with added input validation and sanitization for enhanced security.
'''
from flask import Flask, render_template, request, escape
app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def home():
    valid_greetings = ["Good Morning", "Good Afternoon", "Welcome"]
    if request.method == 'POST':
        user_input = request.form['greeting']
        # Validate input
        if user_input in valid_greetings:
            safe_input = escape(user_input)  # Sanitize input
            message = f"{safe_input} to the Dashboard!"
        else:
            message = "Invalid greeting. Welcome to the Dashboard!"
    else:
        message = "Welcome to the Dashboard!"
    return render_template('index.html', message=message)
if __name__ == '__main__':
    app.run(debug=True)