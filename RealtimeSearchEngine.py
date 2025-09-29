import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import datetime
import difflib
from json import dump

# Defensive defaults for globals that may be set elsewhere in the project
try:
    System
except NameError:
    System = "You are a helpful assistant."

try:
    messages
except NameError:
    messages = []

def clean_text(text):
    """Remove extra whitespace and normalize text"""
    return ' '.join(text.split())


def correct_query(query):
    """Make simple typo corrections and return (corrected_query, did_change, suggestion_text)

    This intentionally performs small, deterministic fixes (like 'netwoth' -> 'net worth')
    rather than relying on external spellcheck packages so it works in plain environments.
    """
    original = query
    corrected = query

    # Common explicit fixes
    explicit = {
        r'\bnetwoth\b': 'net worth',
        r'\bnetwoth\b': 'net worth',
        r'\bnetworth\b': 'net worth',
        r'\bnet-worth\b': 'net worth',
    }
    for pat, repl in explicit.items():
        corrected = re.sub(pat, repl, corrected, flags=re.IGNORECASE)

    # Small token-level fuzzy fixes for likely single-word typos (keeps things conservative)
    vocab = ['net', 'worth', 'networth', 'net worth', 'wealth', 'elon', 'musk']
    tokens = corrected.split()
    new_tokens = []
    for t in tokens:
        # If token looks like a word (letters/digits) try a close match
        match = difflib.get_close_matches(t.lower(), vocab, n=1, cutoff=0.85)
        if match and match[0].lower() != t.lower():
            # preserve original casing where possible
            replacement = match[0]
            new_tokens.append(replacement)
        else:
            new_tokens.append(t)

    corrected = ' '.join(new_tokens)

    did_change = clean_text(corrected).lower() != clean_text(original).lower()
    suggestion_text = ''
    if did_change:
        suggestion_text = f"(Did you mean: '{corrected}'?)"

    return corrected, did_change, suggestion_text

def GoogleSearch(query):
    """Perform a web search and format the results"""
    try:
        # Clean and prepare the search query
        query = clean_text(query)
        corrected_query, did_change, suggestion = correct_query(query)

        search_terms = corrected_query.replace("what is", "").replace("tell me about", "").replace("search for", "").strip()
        # Keep the original user query for messaging
        original_query = query
        content = []
        
        # Add specific terms for net worth searches
        if 'net worth' in search_terms.lower():
            specific_query = f"{search_terms} forbes bloomberg 2025 current billionaire richest"
        else:
            specific_query = f"{search_terms} 2025 current"
            
        search_url = f"https://www.bing.com/search?q={urllib.parse.quote(specific_query)}&format=rss&count=20"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find results using multiple selectors
        results = []
        selectors = [
            ('li', 'b_algo'),
            ('div', 'b_ans'),
            ('div', 'b_special'),
            ('div', 'news-card')
        ]

        for tag, class_name in selectors:
            elements = soup.find_all(tag, class_=class_name)
            for element in elements:
                try:
                    # Look for title in different elements
                    title_elem = element.find(['h2', 'h3', 'h4']) or element.find(class_=['title', 'headline'])
                    caption_elem = element.find(['div', 'p'], class_=['b_caption', 'b_snippet', 'description']) or \
                                 element.find('div', class_='b_caption')

                    if title_elem and caption_elem:
                        title = title_elem.get_text().strip()
                        caption = caption_elem.get_text().strip()

                        # Special handling for net worth queries
                        if 'net worth' in search_terms.lower() or 'net worth' in corrected_query.lower():
                            worth_pattern = r'\$?\s*[\d,.]+\s*(?:billion|million|trillion|\$)'
                            if re.search(worth_pattern, caption, re.IGNORECASE):
                                content.append(f"{title}\n{caption}")
                        else:
                            content.append(f"{title}\n{caption}")
                except Exception:
                    # Ignore parsing issues for individual elements
                    continue

        if content:
            return "\n\n".join(content)

        # If we made a conservative correction to the query, suggest it to the user
        if did_change:
            return (f"I found some results for '{search_terms}', but they don't contain specific information. "
                    f"{suggestion} Could you try rephrasing your question or be more specific?")

        return f"I found some results, but they don't seem to contain specific information about {search_terms}. Could you try rephrasing your question?"

    except Exception as e:
        return f"I apologize, but I couldn't retrieve the information. Please try asking in a different way."

def main():
    while True:
        query = input("\nEnter your question (or 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            break
        print("\nSearching...\n")
        result = GoogleSearch(query)
        print(result)

if __name__ == "__main__":
    main()
    # End of interactive main; the searching logic lives in GoogleSearch().

def AnswerModifier(Answer):
    """Clean up the answer by removing empty lines"""
    if not Answer:
        return ""
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def GetRealTimeInfo():
    """Get current date and time information"""
    now = datetime.datetime.now()
    return (
        f"Current Time: {now.strftime('%A, %B %d, %Y %H:%M:%S')}"
    )

# Initialize system messages
SystemChatBot = [
    {"role": "system", "content": System}
]

def RealtimeSearchEngine(prompt):
    """Handle real-time search and response generation"""
    global SystemChatBot, messages

    try:
        # Add the user's query to messages
        messages.append({"role": "user", "content": prompt})

        # Get search results
        search_results = GoogleSearch(prompt)
        
        # Add specific instruction for this query
        query_instruction = {
            "role": "system",
            "content": f"Use the following search results to answer the question: '{prompt}'. "
                      f"Only use information from these results. If the search results don't "
                      f"contain relevant information, say that you need to search for more "
                      f"specific details."
        }
        
        # Create message list for this conversation
        conversation = (
            SystemChatBot +
            [query_instruction] +
            [{"role": "system", "content": search_results}] +
            [{"role": "system", "content": GetRealTimeInfo()}] +
            messages[-3:]  # Keep only last 3 messages for focused context
        )

        # If an LLM client is available, use it to refine the answer. Otherwise return search results.
        Answer = None
        if 'Client' in globals() and hasattr(Client, 'chat'):
            try:
                completion = Client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=conversation,
                    temperature=0.3,  # Lower temperature for more focused responses
                    max_tokens=512,   # Shorter responses
                    top_p=0.8,       # More focused token selection
                    stream=True
                )

                # Collect response chunks
                Answer = ""
                for chunk in completion:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        if chunk.choices[0].delta.content:
                            Answer += chunk.choices[0].delta.content

                # Clean up response
                Answer = Answer.strip().replace("</s>", "")

                # Add response to messages
                messages.append({"role": "assistant", "content": Answer})

                # Save chat log
                with open(r"Data/ChatLog.json", "w") as f:
                    dump(messages[-50:], f, indent=4)  # Keep last 50 messages max

                return AnswerModifier(Answer=Answer)
            except Exception as e:
                # If the client fails, fall back to returning search results
                print(f"LLM client error, falling back to raw search: {e}")

        # No LLM available: return the raw search results
        # Save chat log with the search_results as assistant content
        messages.append({"role": "assistant", "content": search_results})
        try:
            with open(r"Data/ChatLog.json", "w") as f:
                dump(messages[-50:], f, indent=4)
        except Exception:
            pass

        return AnswerModifier(Answer=search_results)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}"

# Main entry point of the program for interactive querying.
if __name__ == "__main__":
    while True:
        try:
            prompt = input(">>> ")
            if prompt.strip().lower() == 'exit':
                print("Goodbye!")
                break
                
            response = RealtimeSearchEngine(prompt)
            print(response)
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        
        except Exception as e:
            print(f"Error: {str(e)}")            