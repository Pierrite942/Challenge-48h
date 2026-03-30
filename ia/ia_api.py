import google.generativeai as genai

# Configuration de la clé API
API_KEY = "AIzaSyCuzEOE7JDRqczWZMNZt6iacP_lR1cbJu0"
genai.configure(api_key=API_KEY)

def chat_simple(user_message):
    """Chatbot général - discussion libre"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"Erreur: {e}"

def generer_resume_profil(infos):
    """Générer un résumé de profil professionnel"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Tu es un expert professionnel RH. Rédige un résumé de profil professionnel concis, valorisant et accrocheur en quelques phrases à partir des informations suivantes : {infos}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur: {e}"

def moderer_publication(post):
    """Modérer une publication"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Tu es le modérateur automatisé du réseau. Analyse le message suivant. Indique si le contenu est 'APPROPRIÉ' ou 'REJETÉ' (ex: insultes, violence, haine, spam) et donne une explication courte : '{post}'"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur: {e}"

def main():
    print("=== Assistant IA Gemini ===")
    print("1. Chatbot général (discussion libre)")
    print("2. Générer un résumé de profil")
    print("3. Modérer une publication")
    print("Tapez 'exit' pour quitter.")

    while True:
        mode = input("\n[Menu Principal] Choisissez un mode (1, 2, 3 ou exit): ")

        if mode.lower() == 'exit':
            print("Au revoir !")
            break
            
        elif mode == '1':
            print("\n--- Mode Chatbot Normal activé (tapez 'retour' pour le menu) ---")
            while True:
                user_input = input("Vous: ")
                if user_input.lower() == 'retour':
                    break
                response = chat_simple(user_input)
                print(f"Gemini: {response}")
                    
        elif mode == '2':
            print("\n--- Mode Générateur de Résumé de Profil ---")
            infos = input("Quelles sont les informations du profil ? (ex: Développeur web 3 ans exp, cherche alternance) :\n> ")
            print("Génération en cours...")
            response = generer_resume_profil(infos)
            print(f"Résumé :\n{response}")
                
        elif mode == '3':
            print("\n--- Mode Modérateur de Fil d'Actualité ---")
            post = input("Collez le contenu du message à analyser :\n> ")
            print("Analyse en cours...")
            response = moderer_publication(post)
            print(f"Avis de modération :\n{response}")
                
        else:
            print("Choix invalide. Veuillez entrer 1, 2, 3 ou exit.")

if __name__ == "__main__":
    main()
