from groq import Groq  # Importing the Groq iibrary to use its API
from json import load, dump # Importing functions to read and write JSON files.
import datetime # importing the datetime modules for Real-time date and time information.
from dotenv import dotenv_values # Importing dotenv_values to read environment variables from a.env file.

# Load environment variables from the .env files.
env_vars = dotenv_values(".env")

# Retrieve specific environment variables.
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Validate API key
if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in .env file. Please add your API key.")

# Initialize the Groq client using the provided API key
try:
    Client = Groq(api_key=GroqAPIKey)
    
    # Test the connection by listing models
    test_models = Client.models.list()
except Exception as e:
    print(f"\nError: Failed to initialize Groq client. Please check:")
    print("1. Your internet connection")
    print("2. System date and time are correct")
    print("3. SSL/TLS configuration")
    print(f"Detailed error: {str(e)}")
    raise ConnectionError("Failed to initialize Groq client. Please check the above requirements.")

# Define fast models in order of preference
PREFERRED_MODELS = [
    'llama-3.1-8b-instant',  # Fastest model
    'groq/compound-mini',     # Good balance of speed and quality
    'groq/compound',         # Default fallback
]

def get_fastest_available_model():
    """Get the fastest available model from our preferred list"""
    try:
        models = Client.models.list()
        available_ids = {model.id for model in models.data}
        
        # Return the first matching model from our preferred list
        for model_id in PREFERRED_MODELS:
            if model_id in available_ids:
                return model_id
        
        # If none of our preferred models are available, return any chat model
        for model in models.data:
            if any(name in model.id.lower() for name in ['llama', 'gpt', 'compound']):
                if not any(excluded in model.id.lower() for excluded in ['whisper', 'tts', 'embed']):
                    return model.id
    except Exception:
        return "groq/compound"  # Default fallback
    
    return "groq/compound"  # Default fallback

# Get the fastest available model at startup
DEFAULT_MODEL = get_fastest_available_model()

# Initialize an empty list to store chat messages.
messages = []

# Define a concise system message
System = f"You are {Assistantname}, a concise AI assistant for {Username}. Give direct, focused answers in English. No meta-commentary."

# A list of system instructions for the chatbot.
SystemChatbot = [
    {"role": "system", "content": System}
]

# attempt to load the chat log from a JSON file.
try:
    with open(r"Data\ChatLog.json", "r") as file:
        messages = load(file) # Load existing messages from the chat log.
except FileNotFoundError:
    # If the file doesn't exist create an empty JSON file to store chat logs.
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Function to get real-time date and time information.
def RealTimeInformation():
    """Get concise current time information"""
    now = datetime.datetime.now()
    return f"Current time: {now.strftime('%A, %B %d, %Y %H:%M')}"

# Function to modify the chatbot's response for better formatting.
def AnswerModifier(Answer):
    lines = Answer.split('\n') # Split the response into lines.
    non_empty_lines = [line for line in lines if line.strip()] # Remove empty lines.
    modified_answer = '\n'.join(non_empty_lines) # Join the cleaned lines back together.
    return modified_answer

# main chat bot function to handle user queries.
def Chatbot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response."""

    def check_connection():
        """Check if we can connect to the Groq API"""
        try:
            Client.models.list()
            return True
        except Exception as e:
            print(f"\nConnection test failed: {str(e)}")
            return False

    try:
        # First, verify connection
        if not check_connection():
            return "I apologize, but I cannot connect to the AI service right now. Please check your internet connection."

        # load the existing chat log from the JSON file.
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

            # Keep only last 10 messages for context
            if len(messages) > 10:
                messages = messages[-10:]
                
            # Append the user's query to the messages list
            messages.append({"role": "user", "content": Query})

            model_used = DEFAULT_MODEL  # Use the fastest available model

            while True:
                try:
                    # Make a request to the Groq API for a response
                    completion = Client.chat.completions.create(
                        model=model_used,
                        messages=SystemChatbot + [{"role": "system", "content": RealTimeInformation()}] + messages,
                        temperature=0.7,
                        max_tokens=512,  # Reduced token limit for faster responses
                        stream=False  # Ensure no streaming for faster complete response
                    )

                    # Get the response text
                    Answer = completion.choices[0].message.content
                    Answer = Answer.replace("</s>", "") # Clean up any unwanted tokens from the response

                    # Append the chatbot's response to the messages list.
                    messages.append({"role": "assistant", "content": Answer})

                    # Save the updated chat log to json file.
                    with open(r"Data\ChatLog.json", "w") as f:
                        dump(messages, f, indent=4)

                        # Return the formatted response.
                        return AnswerModifier(Answer=Answer)
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"\nError encountered with model {model_used}: {error_msg}")
                    
                    # Try to get an alternative model
                    try:
                        available_models = Client.models.list().data
                        print("\nTrying an alternative model...")
                        for model in available_models:
                            if model.id != model_used:  # Avoid using the same model
                                model_used = model.id
                                print(f"Switching to model: {model_used}")
                                break
                        else:
                            print("No alternative models available. Please check your API key and network connection.")
                            raise Exception("No alternative models available.")  # Raise an exception to exit the loop
                    
                    except Exception as model_error:
                        print(f"\nCould not list models: {model_error}")
                        print("This might indicate an issue with your API key or network connection.")
                        raise model_error  # Exit the loop on model listing error

                    # Suppress the error message for the default model if an alternative model is used
                    if model_used != "gpt4-fast":
                        print("Successfully switched to an alternative model.")
                        continue
    except Exception as e:
        error_msg = str(e)
        print(f"\nError encountered: {error_msg}")
        
        print("\nChecking available models...")
        try:
            models = Client.models.list()
            print("\nModels available for your API key:")
            for model in models.data:
                print(f"- {model.id}")
        except Exception as model_error:
            print(f"\nCould not list models: {model_error}")
            print("This might indicate an issue with your API key or network connection.")
        
        # Reset the chat log
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        
        return f"I apologize, but I encountered an error. Please check the console for available models."
    
# Main program entry point.
if __name__== "__main__":
    while True:
        user_input = input("Enter your question: ") # Prompt the user for a question.
        print(Chatbot(user_input)) # Call the chatbot function and print its response.

