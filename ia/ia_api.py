from google import genai

def main():
    # Remplacement de la clé API et configuration du client
    client = genai.Client(api_key="YAIzaSyBrYM2z5U6k5-zSBuliFFmEdPkHQPC9MlY")

    print("Chatbot Gemini démarré. Tapez 'exit' pour quitter.")

    while True:
        user_input = input("Vous: ")

        if user_input.lower() == 'exit':
            break

        try:
            # Génération de la réponse
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=user_input
            )
            print(f"Gemini: {response.text}")
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    main()