import streamlit as st
import requests
import json
import datetime as dt

# API Keys
NEWS_API_KEY = 'a936d138328d49d0b165cd93d477131b'
GROQ_API_KEY = "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"
MODEL = 'llama-3.3-70b-versatile'

def get_sources():
    data = newsapi.get_sources()
    for source in data['sources']:
        print(source['id'])

def get_news(topic):
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': topic,
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'relevancy',
        'pageSize': 5,
        'excludeDomains': 'bbc.co.uk,'

    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['articles']
    else:
        st.error(f"Error fetching news: {response.status_code}")
        return []

def run_conversation(user_input):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": """
            You are a tool calling News Bot, you will be given a topic and you will need to call the get_news function to get the news related to the topic.
            You will need to call the get_news function to get the news related to the topic.
            
            When giving an answer give a brief summary of all the articles and then list the articles in the format below
            Each article should be displayed in this structured format
            - Provide an answers to the questions asked by the user 
            - Provide a short title
            - Provide a short summary
            - Provide the URL
            - Provide the publishedAt date
            Try to be as concise and provide the information in a readable format, each article should be displayed in a new line with its URL
            Add a "----------------------------------------" after each article
            """
        },
        {
            "role": "user",
            "content": user_input
        }
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_news",
                "description": "Get the news related to the topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Decide what the best Keyword is to get the news related to"
                        }
                    },
                    "required": ["auto"]
                }
            }
        }
    ]
    
    payload = {
        "messages": messages,
        "model": MODEL,
        "tool_choice": "auto",
        "tools": tools
    }
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    
    response_data = response.json()
    response_message = response_data['choices'][0]['message']
    tool_calls = response_message.get('tool_calls', [])
    
    if tool_calls:
        messages.append(response_message)
        tool_call = tool_calls[0]
        function_args = json.loads(tool_call['function']['arguments'])
        news = get_news(function_args['topic'])
        
        news_content = ""
        for i, article in enumerate(news, 1):
            news_content += f"""
            Article {i}:
            Title: {article['title']}
            Description: {article['description']}
            URL: {article['url']}
            Published At: {article['publishedAt']}
            Content: {article['content']}
            Source: {article['source']['name']}'
            publishedAt: {article['publishedAt']}s
            ----------------------------------------
            """
        
        messages.append({
            "tool_call_id": tool_call['id'],
            "role": "tool",
            "content": news_content,
            "name": "get_news"
        })
        
        second_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json={"messages": messages, "model": MODEL}
        )
        
        if second_response.status_code != 200:
            return f"Error in second response: {second_response.status_code} - {second_response.text}"
            
        return second_response.json()['choices'][0]['message']['content']
    else:
        return response_message['content']

# Streamlit UI
st.title("News Chat Assistant 📰")

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your news assistant. Ask me about any news topic!"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Get user input using chat_input instead of text_input
if prompt := st.chat_input("What news would you like to know about?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_conversation(prompt)
            st.write('printing reponse: ')
            st.write(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
