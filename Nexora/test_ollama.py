import ollama

try:
    print("Connecting to Ollama...")
    response = ollama.chat(
        model='qwen2.5:3b',
        messages=[
            {'role': 'system', 'content': 'You are a helpful maritime assistant.'},
            {'role': 'user', 'content': 'Say "SeaSentry AI is active!" in one short sentence.'}
        ]
    )
    print(" SUCCESS:")
    print(response['message']['content'])

except Exception as e:
    print(" ERROR:", e)