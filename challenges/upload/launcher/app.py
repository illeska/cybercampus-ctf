from flask import Flask, render_template, jsonify, session, request
import docker
import os
import uuid
import time
import random
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
MAX_CONTAINERS = int(os.getenv('MAX_CONTAINERS', 20))
CONTAINER_LIFETIME = int(os.getenv('CONTAINER_LIFETIME', 900))  # 15 minutes
PORT_RANGE_START = int(os.getenv('PORT_RANGE_START', 50000))
PORT_RANGE_END = int(os.getenv('PORT_RANGE_END', 60000))

# Stockage en mémoire des instances actives
# Format: {session_id: {'container_id': str, 'port': int, 'created_at': datetime, 'expiry': datetime}}
active_instances = {}
used_ports = set()

# Client Docker
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"❌ Erreur connexion Docker: {e}")
    docker_client = None

def get_available_port():
    """Trouve un port disponible de manière aléatoire"""
    available_ports = [p for p in range(PORT_RANGE_START, PORT_RANGE_END) 
                       if p not in used_ports]
    
    if not available_ports:
        return None
    
    return random.choice(available_ports)

def cleanup_expired_containers():
    """Thread de nettoyage automatique des conteneurs expirés"""
    while True:
        try:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, instance in list(active_instances.items()):
                if now >= instance['expiry']:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                stop_container(session_id)
                print(f"🧹 Conteneur expiré nettoyé: {session_id}")
            
            time.sleep(30)  # Vérifier toutes les 30 secondes
        except Exception as e:
            print(f"❌ Erreur cleanup: {e}")
            time.sleep(30)

# Lancer le thread de nettoyage
cleanup_thread = threading.Thread(target=cleanup_expired_containers, daemon=True)
cleanup_thread.start()

def stop_container(session_id):
    """Arrête et supprime un conteneur"""
    if session_id not in active_instances:
        return False
    
    instance = active_instances[session_id]
    container_id = instance['container_id']
    port = instance['port']
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()
        used_ports.discard(port)
        del active_instances[session_id]
        return True
    except Exception as e:
        print(f"❌ Erreur arrêt conteneur: {e}")
        # Nettoyer quand même les données
        used_ports.discard(port)
        if session_id in active_instances:
            del active_instances[session_id]
        return False

@app.route('/')
def index():
    """Page principale avec iframe"""
    session_id = session.get('session_id')
    instance = active_instances.get(session_id) if session_id else None
    
    return render_template('launcher.html', 
                         instance=instance,
                         session_id=session_id,
                         max_containers=MAX_CONTAINERS,
                         active_count=len(active_instances))

@app.route('/start', methods=['POST'])
def start_challenge():
    """Démarre un nouveau conteneur de challenge"""
    
    # Vérifier quota global
    if len(active_instances) >= MAX_CONTAINERS:
        return jsonify({
            'success': False,
            'error': f'Quota atteint : {MAX_CONTAINERS} conteneurs maximum en cours'
        }), 429
    
    # Créer ou récupérer session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    # Vérifier si l'utilisateur a déjà une instance
    if session_id in active_instances:
        return jsonify({
            'success': False,
            'error': 'Vous avez déjà une instance en cours'
        }), 400
    
    # Trouver un port disponible aléatoirement
    port = get_available_port()
    if not port:
        return jsonify({
            'success': False,
            'error': 'Aucun port disponible'
        }), 503
    
    try:
        # Créer le conteneur
        container = docker_client.containers.run(
            'upload-challenge:latest',
            name=f'upload_challenge_{session_id[:8]}',
            ports={'80/tcp': port},
            detach=True,
            remove=False,  # On gère manuellement la suppression
            environment={
                'FLAG': 'CTF{Upl04d_PHP_Sh3ll_M4st3r}'
            },
            mem_limit='256m',
            cpu_period=100000,
            cpu_quota=50000,  # 50% d'un CPU
            network_mode='bridge'
        )
        
        # Enregistrer l'instance
        now = datetime.now()
        expiry = now + timedelta(seconds=CONTAINER_LIFETIME)
        
        active_instances[session_id] = {
            'container_id': container.id,
            'port': port,
            'created_at': now,
            'expiry': expiry
        }
        used_ports.add(port)
        
        return jsonify({
            'success': True,
            'port': port,
            'expiry': expiry.isoformat(),
            'lifetime_seconds': CONTAINER_LIFETIME
        })
        
    except Exception as e:
        print(f"❌ Erreur création conteneur: {e}")
        used_ports.discard(port)
        return jsonify({
            'success': False,
            'error': f'Erreur de création: {str(e)}'
        }), 500

@app.route('/stop', methods=['POST'])
def stop_challenge():
    """Arrête le conteneur de l'utilisateur"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in active_instances:
        return jsonify({
            'success': False,
            'error': 'Aucune instance active'
        }), 404
    
    success = stop_container(session_id)
    
    return jsonify({
        'success': success
    })

@app.route('/status')
def status():
    """Retourne le statut de l'instance de l'utilisateur"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in active_instances:
        return jsonify({
            'active': False
        })
    
    instance = active_instances[session_id]
    now = datetime.now()
    remaining = (instance['expiry'] - now).total_seconds()
    
    return jsonify({
        'active': True,
        'port': instance['port'],
        'remaining_seconds': int(remaining),
        'expiry': instance['expiry'].isoformat()
    })

@app.route('/stats')
def stats():
    """Statistiques globales (admin)"""
    return jsonify({
        'active_containers': len(active_instances),
        'max_containers': MAX_CONTAINERS,
        'available_slots': MAX_CONTAINERS - len(active_instances),
        'instances': [
            {
                'session_id': sid[:8] + '...',
                'port': inst['port'],
                'created_at': inst['created_at'].isoformat(),
                'expiry': inst['expiry'].isoformat(),
                'remaining_seconds': int((inst['expiry'] - datetime.now()).total_seconds())
            }
            for sid, inst in active_instances.items()
        ]
    })

if __name__ == '__main__':
    print("🚀 Upload Challenge Launcher démarré")
    print(f"📊 Quota: {MAX_CONTAINERS} conteneurs max")
    print(f"⏱️  Durée de vie: {CONTAINER_LIFETIME}s ({CONTAINER_LIFETIME//60} minutes)")
    print(f"🔌 Ports: {PORT_RANGE_START}-{PORT_RANGE_END}")
    app.run(host='0.0.0.0', port=5000, debug=False)