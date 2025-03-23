from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-python", methods=["GET"])
def run_python():
    try:
        result = subprocess.run(["python3", "script.py"], capture_output=True, text=True, check=True)
        return jsonify({"output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)