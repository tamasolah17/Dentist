import csv
import os
from flask import Flask, request, jsonify, render_template



app17 = Flask(__name__)

@app17.route("/login",methods=['POST'])

def login():

    username = request.form.get('username')
    password = request.form.get('password')

    if len(username) > 0 and len(password) > 0:

        # Minimum length check
        if len(username) >= 4 and len(password) >= 4:

            # Special character check
            special_chars = "%!@#$"

            if any(char in password for char in special_chars):

                return jsonify({"message": "Success login!"})

            else:
                return jsonify({"message": "Password must contain a special character!"})

        else:
            return jsonify({"message": "Username and password must be at least 4 characters!"})

    else:
        return jsonify({"message": "Invalid username or password!"})

@app17.route("/")
def index17():

    return render_template("index17.html")

if __name__== "__main__":
    app17.run(host="0.0.0.0",port=2000)


