from openai import OpenAI

MODEL = "gpt-5.4-mini"


def client() -> OpenAI:
    # Reads OPENAI_API_KEY from the environment.
    return OpenAI()


def ask(prompt: str) -> str:
    response = client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
