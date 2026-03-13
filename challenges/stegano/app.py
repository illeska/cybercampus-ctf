from flask import Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'stegano_carto_challenge_ctf_2025'

FLAG = "CTF{C4rt0_st3g4_ROT13_pwn3d}"

@app.route('/')
def index():
    return render_template('stegano.html', message=None, success=False)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/submit', methods=['POST'])
def submit():
    flag_input = request.form.get('flag', '').strip()
    if flag_input == FLAG:
        return render_template('stegano.html',
                               message=f"🎉 Félicitations ! Flag correct : {FLAG}",
                               success=True)
    else:
        return render_template('stegano.html',
                               message="❌ Flag incorrect. Continuez d'explorer...",
                               success=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)