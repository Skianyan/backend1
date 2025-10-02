from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
@app.route('/api/user')
def get_user():
    user_data = {
        'student' : "Ricardo",
        'class' : "Backend",
        'grade' : 'B+',
        'languages' : ['python', 'javascript']
    }
    return jsonify(user_data)


