import streamlit as st
from newsapi import NewsApiClient
# import pandas as pd
import datetime as dt
from groq import Groq
import requests

newsapi=""
newsapi = NewsApiClient(api_key='a936d138328d49d0b165cd93d477131b')
GROQ_API_KEY = "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"
MODEL = 'llama-3.3-70b-versatile'

client = Groq(api_key=GROQ_API_KEY)

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your news assistant. Ask me about any news topic!"}
    ]

def get_sources():
    data = newsapi.get_sources()
    for source in data['sources']:
        print(source['id'])

def get_news(topic):
    data = newsapi.get_everything(q=topic, language='en', sort_by='relevancy', page_size=5)
    # for article in data['articles']:
        # print('Title: ',article['title'])
        # print('Description: ',article['description'])
        # print('URL: ',article['url'])
        # print('Published At: ',article['publishedAt'])
        # print('Content: ',article['content'])
        # print("sources:", article['source'])
        # print("--------------------------------")
    return data['articles']

def run_conversation(user_input):
    messages=[
            {
                "role": "system",
                "content": """
                You are a tool calling News Bot, you will be given a topic and you will need to call the get_news function to get the news related to the topic.
                You will need to call the get_news function to get the news related to the topic.
                Each article should be displayed inthis structured format
                - Provide an answers to the questions asked by the user 
                - Provide a short title
                - Provide a short summary
                - Provide the URL
                Try to be as concise and provide the information in a readable format, each article should be displayed in a new line with its URL
                Add a "----------------------------------------" after each article
                """
            },
            {
                "role": "user",
                "content": user_input, 
            }
        ]
    tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_news",
                    "description": "Get the news related to the topic",
                    "parameters": {
                        "type": "object",
                        "properties":{
                            "topic":{
                                "type": "string",
                                "description": "Decide what the best Keyword is to get the news related to"
                            }
                        },
                        "required": ["auto"]
                    }
                }
            }
        ]
    response = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        tool_choice="auto",
        tools=tools
    )
    response_message = response.choices[0].message
    # print('Initial response: ', response_message,'\n')
    tool_calls = response_message.tool_calls
    # print('Tool calls: ', tool_calls,'\n')

    if tool_calls:
        messages.append(response_message)
    
        tool_call = tool_calls[0]  # Get the first tool call
        function_args = eval(tool_call.function.arguments)  # Parse the JSON arguments
        print(function_args['topic'])
        news = get_news(function_args['topic'])
        # Combine all articles into one string
        news_content = ""
        # news_content = "Here are the latest articles:\n\n"
        for i, article in enumerate(news, 1):
            news_content += f"""
            Article {i}:
            Title: {article['title']}
            Description: {article['description']}
            URL: {article['url']}
            Published At: {article['publishedAt']}
            Content: {article['content']}
            Source: {article['source']['name']}
            ----------------------------------------
        """
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": news_content,
                "name": "get_news"
            }
        )
        second_response = client.chat.completions.create(
            messages=messages,
            model=MODEL
        )
        print(second_response.choices[0].message.content)
        return second_response.choices[0].message.content
    else:
        print(response_message.content)
        return response_message.content

# Streamlit UI
st.title("News Chat Assistant 📰")

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
            st.write(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
