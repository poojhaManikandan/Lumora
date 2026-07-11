import utils


def test_get_api_key_extracts_value_from_prefixed_input(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "GEMINI_API_KEY=literal-key")

    assert utils.get_api_key() == "literal-key"


def test_call_gemini_uses_current_genai_client(monkeypatch):
    calls = {}

    class FakeInteraction:
        output_text = "Tutoring response"

    class FakeInteractions:
        def create(self, **kwargs):
            calls.update(kwargs)
            return FakeInteraction()

    class FakeClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.interactions = FakeInteractions()

    def fail_legacy_path(*args, **kwargs):
        raise AssertionError("legacy google-generativeai path should not be used")

    monkeypatch.setattr(utils.genai, "Client", FakeClient, raising=False)
    monkeypatch.setattr(utils.genai, "configure", fail_legacy_path, raising=False)
    monkeypatch.setattr(utils.genai, "GenerativeModel", fail_legacy_path, raising=False)

    result = utils.call_gemini("Explain binary search", api_key="test-key")

    assert result == "Tutoring response"
    assert calls["api_key"] == "test-key"
    assert calls["model"] == "gemini-3.5-flash"
    assert calls["input"] == "Explain binary search"


def test_call_gemini_reports_last_model_error(monkeypatch):
    class FakeInteractions:
        def create(self, **kwargs):
            raise Exception(f"{kwargs['model']} is not found for API version")

    class FakeClient:
        def __init__(self, api_key):
            self.interactions = FakeInteractions()

    monkeypatch.setattr(utils.genai, "Client", FakeClient, raising=False)

    try:
        utils.call_gemini("Explain binary search", api_key="test-key")
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected call_gemini to fail")

    assert "All Gemini models are currently unavailable" in message
    assert "gemini-2.5-flash-lite is not found for API version" in message


def test_call_gemini_falls_back_to_generate_content(monkeypatch):
    calls = {}

    class FakeInteractionClient:
        def create(self, **kwargs):
            raise Exception(f"{kwargs['model']} is not found for API version")

    class FakeModelResponse:
        text = "Fallback response"

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.update(kwargs)
            return FakeModelResponse()

    class FakeClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.interactions = FakeInteractionClient()
            self.models = FakeModels()

    monkeypatch.setattr(utils.genai, "Client", FakeClient, raising=False)

    result = utils.call_gemini("Explain binary search", api_key="test-key")

    assert result == "Fallback response"
    assert calls["api_key"] == "test-key"
    assert calls["model"] == "gemini-3.5-flash"
    assert calls["contents"] == "Explain binary search"


def test_call_gemini_reports_invalid_key_from_generate_content(monkeypatch):
    class FakeInteractions:
        def create(self, **kwargs):
            raise Exception(f"{kwargs['model']} is not found for API version")

    class FakeModels:
        def generate_content(self, **kwargs):
            raise Exception("401 UNAUTHENTICATED. ACCESS_TOKEN_TYPE_UNSUPPORTED")

    class FakeClient:
        def __init__(self, api_key):
            self.interactions = FakeInteractions()
            self.models = FakeModels()

    monkeypatch.setattr(utils.genai, "Client", FakeClient, raising=False)

    try:
        utils.call_gemini("Explain binary search", api_key="bad-key")
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected call_gemini to fail")

    assert "Invalid API Key" in message
    assert "aistudio.google.com/apikey" in message


def test_call_gemini_does_not_send_json_mime_type_to_interactions(monkeypatch):
    calls = {}

    class FakeInteraction:
        output_text = '{"questions": []}'

    class FakeInteractions:
        def create(self, **kwargs):
            calls.update(kwargs)
            return FakeInteraction()

    class FakeClient:
        def __init__(self, api_key):
            self.interactions = FakeInteractions()

    monkeypatch.setattr(utils.genai, "Client", FakeClient, raising=False)

    result = utils.call_gemini("Return JSON", api_key="test-key", is_json=True)

    assert result == '{"questions": []}'
    assert calls == {
        "model": "gemini-3.5-flash",
        "input": "Return JSON",
    }
