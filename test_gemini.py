import google.generativeai as genai

# Apna API Key yahan dalein
genai.configure(api_key="AIzaSyDVysT5gXSi8pLSBosDzveBawTMUwwMADg")

# Model check karne ke liye logic
try:
    print("Checking available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found supported model: {m.name}")

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Testing 123. Say 'Hello World' if you can hear me.")
    print("\n--- API Response ---")
    print("Success:", response.text)
except Exception as e:
    print("\n--- Error Report ---")
    print("Failed:", e)