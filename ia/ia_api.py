from google import genai
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def test_api_simple():
    """Fonction de test simple pour l'API Gemini"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Erreur: La clé API GEMINI_API_KEY n'est pas définie dans .env")
            return
            
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Explain how AI works in a few words",
        )
        
        print(response.text)
    except Exception as e:
        print(f"Erreur lors du test: {e}")

def main():
    # Configuration du client Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Erreur: La clé API GEMINI_API_KEY n'est pas définie.")
        print("Veuillez définir la variable d'environnement GEMINI_API_KEY dans .env")
        return
    
    client = genai.Client(api_key=api_key)

    print("=== Assistant IA Gemini ===")
    print("0. Test API Simple")
    print("1. Chatbot général (discussion libre)")
    print("2. Générer un résumé de profil")
    print("3. Modérer une publication")
    print("Tapez 'exit' pour quitter.")

    while True:
        mode = input("\n[Menu Principal] Choisissez un mode (0, 1, 2, 3 ou exit): ")

        if mode.lower() == 'exit':
            print("Au revoir !")
            break
            
        elif mode == '0':
            print("\n--- Test API Simple ---")
            test_api_simple()
            
        elif mode == '1':
            print("\n--- Mode Chatbot Normal activé (tapez 'retour' pour le menu) ---")
            chat = client.chats.create(model="gemini-2.0-flash")
            while True:
                user_input = input("Vous: ")
                if user_input.lower() == 'retour':
                    break
                try:
                    response = chat.send_message(user_input)
                    print(f"Gemini: {response.text}")
                except Exception as e:
                    print(f"Erreur: {e}")
                    
        elif mode == '2':
            print("\n--- Mode Générateur de Résumé de Profil ---")
            infos = input("Quelles sont les informations du profil ? (ex: Développeur web 3 ans exp, cherche alternance) :\n> ")
            prompt = f"Tu es un expert professionnel RH. Rédige un résumé de profil professionnel concis, valorisant et accrocheur en quelques phrases à partir des informations suivantes : {infos}"
            try:
                print("Génération en cours...")
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                print(f"Résumé :\n{response.text}")
            except Exception as e:
                print(f"Erreur: {e}")
                
        elif mode == '3':
            print("\n--- Mode Modérateur de Fil d'Actualité ---")
            post = input("Collez le contenu du message à analyser :\n> ")
            prompt = f"Tu es le modérateur automatisé du réseau. Analyse le message suivant. Indique si le contenu est 'APPROPRIÉ' ou 'REJETÉ' (ex: insultes, violence, haine, spam) et donne une explication courte : '{post}'"
            try:
                print("Analyse en cours...")
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                print(f"Avis de modération :\n{response.text}")
            except Exception as e:
                print(f"Erreur: {e}")
                
        else:
            print("Choix invalide. Veuillez entrer 1, 2, 3 ou exit.")

if __name__ == "__main__":
    main()