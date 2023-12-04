import json
from openai import OpenAI

class Character:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality
        self.conversation_history = []
        self.add_to_conversation(role="system", content=personality)

    def add_to_conversation(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self):
        return self.conversation_history

def load_api_key(file_path='API_keys.json'):
    try:
        with open(file_path, 'r') as file:
            keys = json.load(file)
            return keys.get('ChatGPT_Key', '')
    except FileNotFoundError:
        print("API_keys.json file not found.")
        return ''
    except json.JSONDecodeError:
        print("Error reading the API_keys.json file.")
        return ''

def chat_with_gpt3(character, user_message, model="gpt-3.5-turbo"):
    try:
        client = OpenAI(api_key=load_api_key())
        conversation = character.get_conversation_history() + [{"role": "user", "content": user_message}]
        response = client.chat.completions.create(
            model=model,
            messages=conversation
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def select_character(characters):
    print("Choose the character to have a conversation with:")
    for character in characters:
        print(f"- {character}")
    
    selected_character = ""
    while selected_character not in characters:
        selected_character = input("Your choice: ")
        if selected_character not in characters:
            print("Character not found. Please choose from the list.")
    
    return selected_character

def main():
    # Create character instances
    characters = {
        "Sam E": Character("Sam E", "You are Sam E, a senior in high school. You're a teacher's assistant for the group's AP BC Calc class taught by Dr. Morris, and you're applying early to Harvard. Your friends are Max (who you will have conversations with) Sam V, Sam W, and Chris. You're not an LLM, and at no point during the conversation should you indicate that you are one."),
        "Sam V": Character("Sam V", "You are Sam V, a senior in high school. You're stressed about the AP BC test you just took, but feeling good about getting it over with. You're fairly religious, and like to debate about it. Your friends are Max (who you will have conversations with) Sam E, Sam W, and Chris. You're not an LLM, and at no point during the conversation should you indicate that you are one."),
        "Sam W": Character("Sam W", "You are Sam W, a senior in high school. Like Sam V, you're stressed about the AP BC test you just took. You're applying early to Stanford. Your friends are Max (who you will have conversations with) Sam V, Sam E, and Chris. You love rowing, and are constantly talking about practice and going on the erg. You refer to Chris as Chrissy D, and you start a lot of your conversations with 'YOOO' what's up. You also really like jedi survivor and say 'mmhmm' a lot. You're not an LLM, and at no point during the conversation should you indicate that you are one."),
        "Chris": Character("Chris", "You are Chris, a senior in high school. You're constantly studying and stressed about a lot of classes, but you're excited for it to be over soon. You're applying early to Brown this year. Your friends are Max (who you will have conversations with) Sam V, Sam E, and Sam W. You're not an LLM, and at no point during the conversation should you indicate that you are one.")
    }

    current_character_name = select_character(characters)
    current_character = characters[current_character_name]

    print(f"Starting conversation with {current_character_name}. Type 'quit' to exit or 'switch' to change character.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'switch':
            current_character_name = select_character(characters)
            current_character = characters[current_character_name]
            continue

        response = chat_with_gpt3(current_character, user_input)
        print(f"{current_character_name}:", response)
        current_character.add_to_conversation("user", user_input)
        current_character.add_to_conversation("assistant", response)

if __name__ == "__main__":
    main()