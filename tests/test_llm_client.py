from src.llm_client import generate_summary


def test_generate_summary_returns_string():
    result = generate_summary("Say hello in one short sentence.")

    assert isinstance(result, str)
    assert len(result) > 0
