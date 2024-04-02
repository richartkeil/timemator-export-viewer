import llm
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

st.title("Timemator Export Viewer")

uploaded_file = st.file_uploader("Timemator CSV Export", type=["csv"])
if uploaded_file is None:
    st.stop()

data = pd.read_csv(uploaded_file, sep=";")

if (
    "unix_begin" not in data.columns
    or "unix_end" not in data.columns
    or "notes" not in data.columns
    or "duration_decimal" not in data.columns
):
    st.error(
        "The uploaded file must contain 'unix_begin', 'unix_end', 'duration_decimal' and 'notes' columns."
    )
    st.stop()

data["datetime_begin"] = pd.to_datetime(data["unix_begin"], unit="s")
data["datetime_end"] = pd.to_datetime(data["unix_end"], unit="s")

min_date = data["datetime_begin"].min()
max_date = data["datetime_end"].max()

st.write("#### Filter by Date Range")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", min_value=min_date, value=min_date)
with col2:
    end_date = st.date_input("End Date", max_value=max_date, value=max_date)

data = data[
    (data["datetime_begin"] >= pd.Timestamp(start_date))
    & (data["datetime_end"] <= pd.Timestamp(end_date))
]

st.write(f"Number of Entries: {len(data)}")

st.write("#### Cumulative Hours")

cumulative_hours = 0
cumulative_data = []

for _, row in data.iterrows():
    cumulative_data.append(
        {
            "timestamp": row["datetime_begin"],
            "cumulative_hours": cumulative_hours,
            "topic": row["notes"],
        },
    )

    duration_hours = (row["unix_end"] - row["unix_begin"]) / 3600
    cumulative_hours += duration_hours

    cumulative_data.append(
        {
            "timestamp": row["datetime_end"],
            "cumulative_hours": cumulative_hours,
            "topic": row["notes"],
        },
    )

cumulative_data_df = pd.DataFrame(cumulative_data)
cumulative_data_df["topic"] = cumulative_data_df["topic"].fillna("—")
cumulative_data_df["timestamp"] = pd.to_datetime(cumulative_data_df["timestamp"])
cumulative_data_df.set_index("timestamp", inplace=True)

fig = px.line(
    cumulative_data_df,
    x=cumulative_data_df.index,
    y="cumulative_hours",
    custom_data=["topic"],
    markers=True,
)
fig.update_layout(hovermode="x unified")
fig.update_traces(hovertemplate="Acc. Hours: %{y}<br>Topic: %{customdata[0]}")
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Hours Worked (Cumulative)")

st.plotly_chart(fig)

st.write("#### Topic Breakdown")

with st.expander("Show Individual Entries"):
    topic_sum = data.groupby("notes")["duration_decimal"].sum()
    topic_sum = topic_sum.sort_values(ascending=False)
    st.dataframe(topic_sum, use_container_width=True)

col1, col2 = st.columns([1, 3])

with col1:
    num_classes = st.number_input("Number of Topics", 2, 8, 3)

unique_topics = data["notes"].fillna("other").unique()
classes = llm.get_topic_classes(unique_topics, num_classes)

with col2:
    # Allow user to adjust generated classes
    classes_to_use = st.text_area(
        "Topics worked on (adjustable)", value="\n".join(classes), height=200
    )

result_mapping = llm.get_topic_class_mapping(classes_to_use.split("\n"), data)

# Add mapping back to data as "topic" column:
data["topic"] = data["notes"].apply(lambda x: result_mapping.get(x, "–"))

# Combine entries with same "notes" and sum "duration_decimal" for them:
data = data.groupby(["topic", "notes", "date"])["duration_decimal"].sum().reset_index()

fig = px.bar(
    data,
    x="topic",
    y="duration_decimal",
    color="notes",
    color_discrete_sequence=px.colors.qualitative.T10,
    custom_data=["topic", "date", "notes"],
)
fig.update_layout(showlegend=False)
fig.update_traces(
    hovertemplate="Hours: %{y}<br>Notes: %{customdata[2]}<br>Date: %{customdata[1]}<extra></extra>"
)
fig.update_xaxes(title_text="Hours")
fig.update_yaxes(title_text=None)

st.plotly_chart(fig)

topic_total = data.groupby("topic")["duration_decimal"].sum()
topic_total = topic_total.sort_values(ascending=False)
st.dataframe(topic_total, use_container_width=True)
