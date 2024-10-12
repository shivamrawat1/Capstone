from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/run', methods=['POST'])
def run_code():
    code = request.json.get('code')
    try:
        # Execute the Python code and capture the output
        result = subprocess.run(['python3', '-c', code], capture_output=True, text=True, check=True)
        return jsonify(output=result.stdout, error="")
    except subprocess.CalledProcessError as e:
        return jsonify(output="", error=e.stderr)

if __name__ == '__main__':
    app.run(debug=True)
