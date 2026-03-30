from google import genai

def main():
    # Remplacement de la clé API et configuration du client
    client = genai.Client(api_key="YAIzaSyBrYM2z5U6k5-zSBuliFFmEdPkHQPC9MlY")

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
                try:
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=user_input
                    )
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
                    model="gemini-3-flash-preview",
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
                    model="gemini-3-flash-preview",
                    contents=prompt
                )
                print(f"Avis de modération :\n{response.text}")
            except Exception as e:
                print(f"Erreur: {e}")
                
        else:
            print("Choix invalide. Veuillez entrer 1, 2, 3 ou exit.")

if __name__ == "__main__":
    main()