import json
import os

import pandas
import streamlit as st
from groq import Groq

if not os.environ.get("GROQ_API_KEY"):
    st.error(
        "Please set the GROQ_API_KEY environment variable in order to categorize entries."
    )
    st.stop()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
model = "llama3-70b-8192"


@st.cache_data
def get_topic_classes(unique_topics: list[str], num_classes: int) -> list[str]:
    """Generate classes based on a list of unique topics."""

    chat_classes = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                    You are a highly accurate and context-aware classifier of timetracking entries.
                    Given a list of of labels assigned to timetracking entries by the user,
                    you generate the specified number of classes that best represent the topics the user worked on.
                    Only output the classname (do not e.g. include details in brackets).
                    You output the classes in JSON, following this pattern:
                    { "classes": ["Topic Class 1", "Topic Class 2", ...] }
                """,
            },
            {
                "role": "user",
                "content": f"""
                    Generate {num_classes} classes based on these topics I worked on:
                    {'\n '.join(unique_topics)}
                """,
            },
        ],
        model=model,
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    result_classes = json.loads(chat_classes.choices[0].message.content)
    return result_classes["classes"]


@st.cache_data
def get_topic_class_mapping(
    classes: list[str], entries: pandas.DataFrame
) -> dict[int, str]:
    """Generate a mapping of topics to classes based on a list of classes and timetracking entries."""

    labels = entries["notes"].fillna("other").unique()

    # Make sure the model includes the original label in its output to improve class prediction:
    chat_mapping = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                    You are a highly accurate and context-aware classifier of timetracking entries.
                    Given a list of timetracking labels of the user, and a list of classes,
                    you assign each label to the class that best represents the topic the label is about.
                    You must only use the classes provided by the user. If a label does not fit any class,
                    choose a class that is the closest match. 
                    You output the mapping in JSON, following this pattern:
                    {
                        "label 1": "topic class 3",
                        "label 2": "topic class 3",
                        "label 2": "topic class 1",
                        ...
                    }
                """,
            },
            {
                "role": "user",
                "content": f"""
                    Here are the classes to be used:
                    {'\n '.join(classes)}

                    Here are the labels to be classified:
                    {'\n '.join(labels)}
                """,
            },
        ],
        model=model,
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    return json.loads(chat_mapping.choices[0].message.content)
