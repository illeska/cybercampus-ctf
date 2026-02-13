from flask import Flask, render_template, request, session, redirect
import hashlib

app = Flask(__name__)
app.secret_key = 'osint_challenge_secret_key_2024'

@app.route('/')
def index():
    return redirect('/osint/accueil')

@app.route('/osint/accueil')
def accueil():
    return render_template('accueil.html')

@app.route('/osint/villes')
def villes():
    return render_template('villes.html')

@app.route('/osint/lille')
def lille():
    return render_template('lille.html')

@app.route('/osint/roubaix')
def roubaix():
    return render_template('roubaix.html')

@app.route('/osint/tourcoing')
def tourcoing():
    return render_template('tourcoing.html')

@app.route('/osint/hem', methods=['GET', 'POST'])
def hem():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if code == 'HEM2024':
            return render_template('hem.html', unlocked=True)
        else:
            return render_template('hem.html', unlocked=False, error=True)
    return render_template('hem.html', unlocked=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)