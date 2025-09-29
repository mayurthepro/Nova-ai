import cohere # import the Cohere library for ai services
from rich import print # import the Rich library to enhance terminal output
from dotenv import dotenv_values # import dotenv to load envirement varibles from a.env file.

# Load envirement variables from a .env file
env_vars = dotenv_values(".env")

# Retrieve API key.
CohereAPIKey = env_vars.get("COHERE_API_KEY")

# Create a cohere client using the provided API key.
co = cohere.Client(CohereAPIKey)

# Define a list of recognized function keywords for task categorization.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search" , "reminder"
] 

# Initialize an empty list to store user messages.
messages = []

# Define the preamble that guides the AI model on how to categorize queries.
preamble = """You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model and requires up to date information.
-> Respond with 'open (application name or website name)' if a query is asking to open any application.
-> Respond with 'close (application name)' if a query is asking to close any application.
-> Respond with 'play (song name)' if a query is asking to play any song.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate an image.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder.
-> Respond with 'system (task name)' if a query is asking to perform system tasks.
-> Respond with 'content (topic)' if a query is asking to write any type of content.
-> Respond with 'google search (topic)' if a query is asking to search on google.
-> Respond with 'youtube search (topic)' if a query is asking to search on youtube.
*** Respond with 'general (query)' if you can't decide the kind of query. ***
"""

# Define a chat history with predefined user-chatbot interactions for context.
ChatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi"},
    {"role": "chatbot", "message": "open chrome, general tell me about mahatma gandhi"},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have dancing performance on 5th aug at 11pm"},
    {"role": "chatbot", "message": "general what is today's date, reminder 11pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me"},
    {"role": "chatbot", "message": "general chat with me"}
]

# Define the main function for decision-making on queries.
def FirstLayerDMM(prompt: str = "test"):
    try:
        # Check if API key is available
        if not CohereAPIKey:
            return ["error: Cohere API key not found. Please check your .env file."]

        # Add the user's query to the messages list.
        messages.append({"role": "user", "content": f"{prompt}"})

        # Create a chat session with Cohere model.
        chat_response = co.chat(
            message=prompt,  # pass the user's query.
            model='c4ai-aya-expanse-8b',  # use the Aya Expanse model
            temperature=0.7,  # set the creativity level of the model.
            chat_history=[{"role": m["role"], "message": m["message"]} for m in ChatHistory],  # format chat history properly
            preamble=preamble,  # pass the detailed instructions preamble.
            prompt_truncation='AUTO'  # Let Cohere handle truncation automatically
        )
        
        if not chat_response or not hasattr(chat_response, 'text'):
            return ["error: Invalid response from Cohere API"]

        # Get the response text
        response = chat_response.text

        # Remove newline characters and split response into individual tasks.
        response = response.replace("\n", "")
        response = response.split(",")

        # Strip leading and trailing whitespace from each task.
        response = [i.strip() for i in response]

        # Initialize an empty list to filter valid tasks.
        temp = []

        # Filter the tasks based on recognized function keywords.
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)  # add valid task to the filtered list.

        # Update the response with the filtered list of tasks.
        response = temp

        # If empty response, treat as general query
        if not response:
            return [f"general {prompt}"]

        # If '(query)' in the response, recursively call the function for further clarification.
        if "(query)" in str(response):
            newresponse = FirstLayerDMM(prompt=prompt)
            return newresponse  # Return the clarified response.
        else:
            return response  # Return the filtered response.

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return ["error: " + error_msg]  # Return error message in the expected format
        
    return response  # Return the filtered response

# Entry point for the script.
if __name__ == "__main__":
    # Continuously prompt the user for input and process it.
    while True:
        print(FirstLayerDMM(input(">>> ")))  # Print the categorized response.
