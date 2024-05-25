import nltk
from nltk.chat.util import Chat, reflections

reflections = {
    "i am"       : "you are",
    "i was"      : "you were",
    "i"          : "you",
    "i'm"        : "you are",
    "i'd"        : "you would",
    "i've"       : "you have",
    "i'll"       : "you will",
    "my"         : "your",
    "you are"    : "I am",
    "you were"   : "I was",
    "you've"     : "I have",
    "you'll"     : "I will",
    "your"       : "my",
    "yours"      : "mine",
    "you"        : "me",
    "me"         : "you"
}

pairs = [
    [
        r"my name is (.*)",
        ["Hello %1, How are you today ?", "Nice to Ameet you %1!"]
    ],
    [
        r"how are you ?",
        ["I'm just an AI assistant, but thank you for asking.", "I'm here to help. How can I assist you?"]
    ],
    [
        r"what do you do ?",
        ["I'm a chatbot designed to answer your questions and assist you.", "Feel free to ask me anything!"]
    ],
    [

        r"i'm (.*)",
        ["Hi %1, How are you feeling today ?", "Nice to meet you %1!"]
    ],
    [

        r"im (.*)",
        ["Hi %1, How are you feeling today ?", "Nice to meet you %1!"]
    ],
    [
        r"quit",
        ["Bye Bye!! Take Care.", "See you later, have a nice day."]
    ],
    [
        r"thanks?",
        ["You are welcome.", "Anytime!"]
    ]
]

def chat():
    print("Chatbot: Hi there! I'm your friendly chatbot. How can I assist you?")
    chat_instance = Chat(pairs, reflections)
    chat_instance.converse()

chat()
