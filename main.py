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
            evaluate_conversation = data.get("evaluate_conversation", "")  # Load the evaluation prompt
            characters_data = data.get("characters", {})

            for character in characters_data:
                characters_data[character]["description"] = baseline_description + characters_data[character]["description"]

            return characters_data, evaluate_conversation  # Return both characters data and the evaluation prompt

    except FileNotFoundError:
        print(f"{file_path} file not found.")
        return {}, ""
    except json.JSONDecodeError:
        print(f"Error reading the {file_path} file.")
        return {}, ""

def select_character(characters):
    print("Choose the character to have a conversation with:")
    for character in characters:
        print(f"- {character}")
    
    selected_character = ""
    while selected_character not in characters:
        selected_character = input("Your choice: ")
        if selected_character not in characters:
            print("Character not found. Please choose from the list.")

    current_character_object = characters[selected_character]
    print(f"Character's current emotion: {current_character_object.emotion}\n")
    
    return selected_character

class Character:
    def __init__(self, name, description, emotion):
        self.name = name
        self.description = description
        self.emotion = emotion
        self.conversation_history = []
        self.add_to_conversation("system", description)

        # emotion_types = ["neutral", "happy", "excited", "stressed"]

    def add_to_conversation(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self):
        return self.conversation_history
    
    def update_emotion_based_on_conversation(self, conversation_type):
        conversions = {
            "inspiring": "excited",
            "fun": "happy",
            "stressful": "stressed",
            "boring": "neutral"
        }

        self.emotion = conversions[conversation_type]

def chat_with_gpt3(character, user_message, model="gpt-4-1106-preview"):
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
    character_descriptions, evaluate_conversation_prompt = load_character_descriptions()

    # Create character instances with descriptions and starting emotions
    characters = {
        name: Character(name, char_data["description"], char_data["emotion"]) 
        for name, char_data in character_descriptions.items()
    }

    current_character_name = select_character(characters)
    current_character = characters[current_character_name]

    print(f"Starting conversation with {current_character_name}. Type 'quit' to exit or 'switch' to change character.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'switch':
            conversation_assessment = chat_with_gpt3(current_character, user_message=evaluate_conversation_prompt)
            current_character.update_emotion_based_on_conversation(conversation_assessment)
            print(f"Conversation Type: {conversation_assessment} \n")

            current_character_name = select_character(characters)
            current_character = characters[current_character_name]
            continue
        
        # get agent response
        emotion_prefixed_user_input = f"Your current emotion is {current_character.emotion}. It should affect your responses to following input. {user_input}"
        response = chat_with_gpt3(current_character, emotion_prefixed_user_input)
        print(f"{current_character_name}:", response)

        # store conversation history
        current_character.add_to_conversation("user", user_input)
        current_character.add_to_conversation("assistant", response)

if __name__ == "__main__":
    main()