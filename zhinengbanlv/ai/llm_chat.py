from ai import client


def deepseek_chat(message: list[dict]):
    return client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Flash",
        messages=message,
        temperature=0,
        max_tokens=2048,
        stream=False
    )
