from sat_core.config import GOOGLE_GENAI_API_KEY


class _ShimModels:
    def __init__(self, api_key: str):
        # Lazy import to avoid hard dependency if not installed
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai

    def generate_content(self, model: str, contents: str):
        model_obj = self._genai.GenerativeModel(model)
        return model_obj.generate_content(contents)


class _ShimClient:
    def __init__(self, api_key: str):
        self.models = _ShimModels(api_key)


def get_gemini_client():
    if not GOOGLE_GENAI_API_KEY:
        raise RuntimeError("GOOGLE_GENAI_API_KEY is not set")

    # Prefer new SDK if available
    try:
        from google import genai as new_genai  # type: ignore
        if hasattr(new_genai, "Client"):
            return new_genai.Client(api_key=GOOGLE_GENAI_API_KEY)
    except Exception:
        pass

    # Fallback to older google.generativeai with a shimmed interface
    try:
        import google.generativeai  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "Neither google.genai.Client nor google.generativeai is available."
        ) from exc

    return _ShimClient(GOOGLE_GENAI_API_KEY)


if __name__ == "__main__":
    client = get_gemini_client()
    print("✅ Gemini client ready (new SDK or shim)")


