import importlib
import os


def _get_genai_module():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquante dans les variables d'environnement.")

    try:
        genai = importlib.import_module("google.generativeai")
    except Exception as exc:
        raise RuntimeError(
            "Le package google-generativeai n'est pas installé."
        ) from exc

    genai.configure(api_key=api_key)
    return genai


def _model_candidates() -> list[str]:
    configured = (os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash")
    defaults = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    candidates: list[str] = []
    for model_name in [configured, *defaults]:
        if model_name and model_name not in candidates:
            candidates.append(model_name)
    return candidates


def _generate_with_fallback(prompt: str) -> str:
    genai = _get_genai_module()
    last_error: Exception | None = None

    for model_name in _model_candidates():
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text or "(réponse vide)"
        except Exception as exc:
            last_error = exc
            raw = str(exc).upper()
            if "NOT FOUND" in raw or "NOT SUPPORTED" in raw or "404" in raw:
                continue
            raise

    if last_error is not None:
        raise last_error

    raise RuntimeError("Aucun modèle Gemini disponible.")


def _format_error(exc: Exception) -> str:
    raw = str(exc)
    upper = raw.upper()

    if "API_KEY_INVALID" in upper or "API KEY NOT FOUND" in upper:
        return "Clé API Gemini invalide. Vérifie GEMINI_API_KEY dans .env."

    if "REPORTED AS LEAKED" in upper or "PERMISSION_DENIED" in upper:
        return "Ta clé API Gemini a été bloquée (clé compromise). Génère une nouvelle clé dans Google AI Studio et remplace GEMINI_API_KEY dans .env."

    if "RESOURCE_EXHAUSTED" in upper or "QUOTA" in upper or "429" in upper:
        return "Quota Gemini dépassé. Réessaie plus tard ou active la facturation côté Google AI Studio."

    if "NOT FOUND" in upper or "NOT SUPPORTED" in upper or "404" in upper:
        return "Le modèle Gemini configuré n'est pas disponible pour ta clé. Mets GEMINI_MODEL=gemini-2.5-flash dans .env puis redémarre l'app."

    return f"Erreur: {raw}"


def test_api_simple() -> str:
    try:
        return _generate_with_fallback("Explain how AI works in a few words")
    except Exception as exc:
        return _format_error(exc)


def chat_simple(user_message: str) -> str:
    try:
        return _generate_with_fallback(user_message)
    except Exception as exc:
        return _format_error(exc)

