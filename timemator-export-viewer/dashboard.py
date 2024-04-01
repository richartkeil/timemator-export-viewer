import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Timemator Export Viewer")

uploaded_file = st.file_uploader("Timemator CSV Export", type=["csv"])
if uploaded_file is None:
    st.stop()

data = pd.read_csv(uploaded_file, sep=";")

if (
    "unix_begin" not in data.columns
    or "unix_end" not in data.columns
    or "notes" not in data.columns
):
    st.error(
        "The uploaded file must contain 'unix_begin', 'unix_end' and 'notes' columns."
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
cumulative_data_df["topic"].fillna("—", inplace=True)
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
