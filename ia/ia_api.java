package ai;

import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;
import java.util.Scanner;

public class GenerateTextFromTextInput {
  public static void main(String[] args) {
    Client client = Client.builder().apiKey("YAIzaSyBrYM2z5U6k5-zSBuliFFmEdPkHQPC9MlY").build();
    Scanner scanner = new Scanner(System.in);

    System.out.println("Chatbot Gemini démarré. Tapez 'exit' pour quitter.");

    while (true) {
        System.out.print("Vous: ");
        String userInput = scanner.nextLine();

        if ("exit".equalsIgnoreCase(userInput)) {
            break;
        }

        try {
            GenerateContentResponse response =
                client.models.generateContent(
                    "gemini-3-flash-preview",
                    userInput,
                    null);

            System.out.println("Gemini: " + response.text());
        } catch (Exception e) {
            System.out.println("Erreur: " + e.getMessage());
        }
    }
    
    scanner.close();
  }
}
