import os
import google.generativeai as genai

# Suppress grpc warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"

# Attempt to load from .env file if it exists
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEYS="):
                os.environ["GEMINI_API_KEYS"] = line.split("=", 1)[1].strip().strip('"\'')
            if line.startswith("GEMINI_MODEL="):
                os.environ["GEMINI_MODEL"] = line.split("=", 1)[1].strip().strip('"\'')

raw_keys = os.environ.get("GEMINI_API_KEYS", "").strip()
if raw_keys:
    if raw_keys.startswith("[") and raw_keys.endswith("]"):
        raw_keys = raw_keys[1:-1]
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not keys:
    print("❌ Error: GEMINI_API_KEYS environment variable is not set.")
    exit(1)

if len(keys) < 3:
    print(f"⚠️  Only {len(keys)} key(s) provided. Provide 3 for full rotation testing.")

model_name = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

print("Testing Gemini API keys...")
for idx, api_key in enumerate(keys, start=1):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, reply with exactly one word: 'Success'")

        if response.text:
            print(f"✅ Key {idx}: Success! (Response: {response.text.strip()})")
        else:
            print(f"❌ Key {idx}: Empty response.")
    except Exception as e:
        print(f"❌ Key {idx}: Error: {e}")
        if "429" in str(e) or "Quota" in str(e):
            print("\n⚠️  You have hit the Quota Limit for this API key.")
            print("   This means your Google account has used up its free tier requests,")
            print("   or billing is not configured.")
