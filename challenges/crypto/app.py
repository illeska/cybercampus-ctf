from flask import Flask, render_template, request, session, redirect
import hashlib

app = Flask(__name__)
app.secret_key = 'rainbow_tables_crypto_challenge_secret'

# Base de données compromise avec hash MD5
USERS_DATABASE = [
    {
        'id': 1,
        'username': 'admin',
        'password_hash': '5f4dcc3b5aa765d61d8327deb882cf99',  # password
        'hint': 'Le mot de passe le plus commun au monde...'
    },
    {
        'id': 2,
        'username': 'alice',
        'password_hash': 'e10adc3949ba59abbe56e057f20f883e',  # 123456
        'hint': '6 chiffres'
    },
    {
        'id': 3,
        'username': 'bob',
        'password_hash': '098f6bcd4621d373cade4e832627b4f6',  # test
        'hint': 'Un mot de 4 lettres'
    },
    {
        'id': 4,
        'username': 'secret_agent',
        'password_hash': '1c5442c0461e5186126aaba26edd6857',  # arsenal
        'hint': 'Un club de foot'
    },
    {
        'id': 5,
        'username': 'FLAG_HOLDER',
        'password_hash': '6ff9d539047fde159e88d2d1e11ef574',  # mrrobot
        'hint': 'Série populaire'
    }
]

# Stockage des hash crackés en session
def init_session():
    if 'cracked' not in session:
        session['cracked'] = {}
    if 'attempts' not in session:
        session['attempts'] = 0

@app.route('/', methods=['GET', 'POST'])
def index():
    init_session()
    
    message = None
    flag = None
    crack_result = None
    
    # Vérification d'un hash
    if request.method == 'POST' and 'crack_hash' in request.form:
        user_input = request.form.get('password', '').strip()
        hash_to_crack = request.form.get('hash', '')
        user_id = request.form.get('user_id', '')
        
        # NOUVEAU : Vérifier l'ordre séquentiel
        user_id_int = int(user_id)
        
        # Vérifier que tous les hash précédents sont crackés
        for i in range(1, user_id_int):
            if str(i) not in session.get('cracked', {}):
                crack_result = {
                    'success': False,
                    'message': f'⚠️ Vous devez d\'abord craquer les hash précédents (dans l\'ordre) !',
                    'user_id': user_id
                }
                return render_template(
                    'crypto.html',
                    users=USERS_DATABASE,
                    cracked=session.get('cracked', {}),
                    message=message,
                    flag=flag,
                    crack_result=crack_result,
                    attempts=session.get('attempts', 0),
                    progress=int((len(session.get('cracked', {})) / len(USERS_DATABASE)) * 100),
                    cracked_count=len(session.get('cracked', {})),
                    total_users=len(USERS_DATABASE)
                )
        
        session['attempts'] += 1
        
        # Calculer le hash MD5 de l'entrée utilisateur
        input_hash = hashlib.md5(user_input.encode()).hexdigest()
        
        if input_hash == hash_to_crack:
            session['cracked'][user_id] = user_input
            session.modified = True
            
            # Si c'est le niveau 5, afficher directement le flag
            if user_id_int == 5:
                flag = 'CTF{r41nb0w_t4bl3s_pwn3d}'
                message = f'🎉 Bravo ! Vous avez cracké tous les hash en {session["attempts"]} tentatives ! Voici le flag :'
            
            crack_result = {
                'success': True,
                'message': f'✅ Cracké ! Le mot de passe est : <strong>{user_input}</strong>',
                'user_id': user_id
            }
        else:
            crack_result = {
                'success': False,
                'message': f'❌ Incorrect. Hash obtenu : {input_hash[:16]}...',
                'user_id': user_id
            }
    
    # Soumission du FLAG final
    if request.method == 'POST' and 'submit_flag' in request.form:
        flag_input = request.form.get('flag', '').strip()
        
        # Vérifier si c'est le bon flag
        if flag_input == 'CTF{r41nb0w_t4bl3s_pwn3d}':
            flag = 'CTF{r41nb0w_t4bl3s_pwn3d}'
            message = f'🎉 Bravo ! Vous avez cracké tous les hash en {session["attempts"]} tentatives !'
            session['attempts'] = 0
        else:
            message = '❌ Flag incorrect. Crackez tous les hash pour trouver le flag.'
    
    # Calculer la progression
    total_users = len(USERS_DATABASE)
    cracked_count = len(session.get('cracked', {}))
    progress = int((cracked_count / total_users) * 100)
    
    return render_template(
        'crypto.html',
        users=USERS_DATABASE,
        cracked=session.get('cracked', {}),
        message=message,
        flag=flag,
        crack_result=crack_result,
        attempts=session.get('attempts', 0),
        progress=progress,
        cracked_count=cracked_count,
        total_users=total_users
    )

@app.route('/reset')
def reset():
    """Réinitialiser la progression"""
    session['cracked'] = {}
    session['attempts'] = 0
    session.modified = True
    return redirect('/')  # Redirection vers la page principale

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)