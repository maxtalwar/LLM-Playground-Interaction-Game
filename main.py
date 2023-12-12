import json
from openai import OpenAI

def load_api_key(file_path='API_keys.json') -> str:
    # load API key from JSON file
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
    
def load_character_descriptions(file_path='character_descriptions.json') -> (dict, str):
    # load character descriptions from JSON file
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

def select_character(characters: list) -> str:
    # let the user choose a character
    
    # print a character
    print("Choose the character to have a conversation with:")
    for character in characters:
        print(f"- {character}")
    
    # repeat until the user chooses a valid character from the list
    selected_character = ""
    while selected_character not in characters:
        selected_character = input("Your choice: ")
        if selected_character not in characters:
            print("Character not found. Please choose from the list.")

    # print the selected character's current emotion
    current_character_object = characters[selected_character]
    print(f"Character's current emotion: {current_character_object.emotion}\n")
    
    return selected_character

class FSM:
    # our pre-defined FSM class
    def __init__(self, initial_state):
        # Dictionary (input_symbol, current_state) --> (action, next_state).
        self.state_transitions = {}
        self.current_state = initial_state

    def add_transition(self, input_symbol, state, action=None, next_state=None):
        """
        Adds a transition to the instance variable state_transitions
        that associates:
            (input_symbol, current_state) --> (action, next_state)

        The action may be set to None in which case the process() method will
        ignore the action and only set the next_state.

        The next_state may be set to None in which case the current state will be unchanged.
        
        Args:
            input_symbol (anything): The input received
            state (anything): The current state
            action (function, optional): The action to take/function to run. Defaults to None.
            next_state (anything, optional): The next state to transition to. Defaults to None.
        """
        self.state_transitions[(input_symbol, state)] = (action, next_state)

    def get_transition(self, input_symbol, state):
        """
        Returns tuple (action, next state) given an input_symbol and state.
        Normally you do not call this method directly. It is called by
        process().

        Args:
            input_symbol (anything): The given input symbol
            state (anything): The current state

        Returns:
            tuple: Returns the tuple (action, next_state)
        """
        return self.state_transitions[(input_symbol, state)]

    def process(self, input_symbol):
        """
        The main method that you call to process input. This may
        cause the FSM to change state and call an action. This method calls
        get_transition() to find the action and next_state associated with the
        input_symbol and current_state. If the action is None then the action
        is not called and only the current state is changed. This method
        processes one complete input symbol.
        Args:
            input_symbol (anything): The input to process
        """
        transition = self.get_transition(input_symbol, self.current_state)
        action = transition[0]
        next_state = transition[1]

        if action: action()
        if next_state: self.current_state = next_state

class Character:
    def __init__(self, name, description, emotion) -> None:
        self.name = name
        self.description = description
        self.emotion = emotion
        self.conversation_history = []
        self.add_to_conversation("system", description)

        self.fsm = FSM(emotion)
        self.setup_fsm_transitions()

        # emotion_types = ["neutral", "happy", "excited", "stressed"]

    def add_to_conversation(self, role, content) -> None:
        # store message in LLM's conversation history
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self):
        # get past messages
        return self.conversation_history
    
    def update_emotion_based_on_conversation(self, conversation_type) -> None:
        # adjust the LLM's emotion based on the conversation type they assessed
        self.fsm.process(conversation_type)
        self.emotion = self.fsm.current_state

    def setup_fsm_transitions(self) -> None:
        # Example transitions (add more as needed)
        # states: happy, stressed, neutral
        # transitions: fun, stressful, boring
        # the FSM for this would be triangular -- each of the three emotions can map to any other emotion

        # transitions for fun conversations
        self.fsm.add_transition("fun", "happy", next_state="happy")
        self.fsm.add_transition("fun", "neutral", next_state="happy")
        self.fsm.add_transition("fun", "stressed", next_state="happy")

        # transitions for boring conversations
        self.fsm.add_transition("boring", "neutral", next_state="neutral")
        self.fsm.add_transition("boring", "happy", next_state="neutral")
        self.fsm.add_transition("boring", "stressed", next_state="neutral")
        
        # transitions for stressful conversations
        self.fsm.add_transition("stressful", "stressed", next_state="stressed")
        self.fsm.add_transition("stressful", "happy", next_state="stressed")
        self.fsm.add_transition("stressful", "neutral", next_state="stressed")

def chat_with_gpt3(character: Character, user_message: str, model="gpt-4-1106-preview") -> str:
    # function to get response from LLM based on user input
    try:
        # restart the OpenAI Client
        client = OpenAI(api_key=load_api_key())

        # give the model its past conversation history with the user
        conversation = character.get_conversation_history() + [{"role": "user", "content": user_message}]

        # get the response from the LLM
        response = client.chat.completions.create(
            model=model,
            messages=conversation
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def main() -> None:
    # load pre-defined character descriptions from file
    character_descriptions, evaluate_conversation_prompt = load_character_descriptions()

    # Create character instances with descriptions and starting emotions
    characters = {
        name: Character(name, char_data["description"], char_data["emotion"]) 
        for name, char_data in character_descriptions.items()
    }

    # let the user pick a character
    current_character_name = select_character(characters)
    current_character = characters[current_character_name]

    # start the conversation
    print(f"Starting conversation with {current_character_name}. Type 'quit' to exit or 'switch' to change character.")

    # repeat until the game ends
    while True:
        # get the user's input, process their response
        user_input = input("You: ")

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'switch':
            # if the user switches the character assess the conversation, update the LLM's emotion
            conversation_assessment = chat_with_gpt3(current_character, user_message=evaluate_conversation_prompt)
            current_character.update_emotion_based_on_conversation(conversation_assessment)
            print(f"Conversation Type: {conversation_assessment} \n")

            # let the user pick a new character
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