import json
from openai import OpenAI

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
    
def load_character_descriptions(file_path='character_descriptions.json'):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            baseline_description = data.get("baseline_description", "")
            characters_data = data.get("characters", {})

            # Concatenate baseline description with each character's description
            for character in characters_data:
                characters_data[character] = baseline_description + characters_data[character]

            return characters_data

    except FileNotFoundError:
        print(f"{file_path} file not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error reading the {file_path} file.")
        return {}


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

class Character:
    def __init__(self, name, personality):
        self.name = name
        self.personality = personality
        self.conversation_history = []
        self.emotion = "neutral"
        self.add_to_conversation(role="system", content=personality)

        emotion_types = ["happy", "excited", "stressed"] # + "sad"

    def add_to_conversation(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self):
        return self.conversation_history
    
    def update_emotion_based_on_conversation(self, conversation_type):
        conversions = {
            "inspiring": "excited",
            "fun": "happy",
            "stressful": "stressed"
        }

        self.emotion = conversions[conversation_type]

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

def main():
    # Create character instances
    character_descriptions = load_character_descriptions()
    characters = {name: Character(name, description) for name, description in character_descriptions.items()}

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