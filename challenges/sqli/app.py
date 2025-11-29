from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Création de la base vulnérable
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("DELETE FROM users")
    c.execute("INSERT INTO users VALUES (1, 'admin', 'super_secret_123')")
    c.execute("INSERT INTO users VALUES (2, 'guest', 'guest123')")
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    message = None
    flag = None
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # VULNÉRABLE : Injection SQL directe
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            c.execute(query)
            user = c.fetchone()
            
            if user:
                if user[1] == 'admin':
                    flag = "CTF{SQL_1nj3ct10n_m4st3r}"
                    message = f"Connexion réussie en tant que {user[1]} ! Voici le flag : {flag}"
                else:
                    message = f"Connecté en tant que {user[1]}, mais vous devez être admin pour obtenir le flag."
            else:
                message = "Identifiants incorrects."
        except Exception as e:
            message = f"Erreur SQL : {str(e)}"
        
        conn.close()
    
    return render_template('login.html', message=message, flag=flag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)