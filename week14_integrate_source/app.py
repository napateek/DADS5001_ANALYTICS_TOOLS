# Connect to snowflake database

import streamlit as st
import altair as alt
import pandas as pd
import time
import os
import joblib
import google.generativeai as genai
from json import loads, dumps


# -------------------------------
# Connection and page settings
# -------------------------------

st.set_page_config(layout="wide")
st.cache_data.clear()
st.cache_resource.clear()
conn = st.connection("snowflake")

MY_INVENTORY_DATA = ''

# -------------------------------
# Utils
# -------------------------------
def load_product_data() -> pd.DataFrame:
    """Loads the inventory data from the database."""

    data = conn.query(
        """SELECT
               ID,
               IMAGE,
               ITEM_NAME,
               PRICE,
               UNITS_SOLD,
               UNITS_LEFT,
               COST_PRICE,
               REORDER_POINT,
               DESCRIPTION
           FROM
               INVENTORY
            ORDER BY ID ASC;"""
    )

    data.rename(
        columns={
            "ID": "ID",
            "IMAGE": "Image",
            "ITEM_NAME": "Item Name",
            "PRICE": "Price",
            "UNITS_SOLD": "Units Sold",
            "UNITS_LEFT": "Units Left",
            "COST_PRICE": "Cost Price",
            "REORDER_POINT": "Reorder Point",
            "DESCRIPTION": "Description",
        },
        inplace=True,
    )
    
    result = data.to_json(orient="split")
    MY_INVENTORY_DATA = loads(result)
    
    return data


def update_product_data(dataframe, changes) -> None:
    """Updates the inventory data in the database."""

    if changes["edited_rows"]:
        deltas = st.session_state.inventory_table["edited_rows"]

        for i, delta in deltas.items():
            row_value = dataframe.iloc[i].to_dict()
            row_value.update(delta)
            try:
                conn.query(
                    f"""
                    UPDATE
                        INVENTORY
                    SET
                        ITEM_NAME = '{row_value['Item Name']}',
                        PRICE = {row_value['Price']},
                        UNITS_SOLD = {row_value['Units Sold']},
                        UNITS_LEFT = {row_value['Units Left']},
                        COST_PRICE = {row_value['Cost Price']},
                        REORDER_POINT = {row_value['Reorder Point']},
                        DESCRIPTION = '{row_value['Description']}',
                        IMAGE = '{row_value['Image']}'
                    WHERE
                        ID = {row_value['ID']}
                    """
                ).collect()
                st.toast("Data have being updated!")
            except:
                st.toast("Something went wrong while updating the data, try again.")

    if changes["added_rows"]:
        # try:
            for row_value in changes["added_rows"]:
                conn.query(
                    f"""
                            INSERT INTO
                                INVENTORY (
                                    ITEM_NAME,
                                    PRICE,
                                    UNITS_SOLD,
                                    UNITS_LEFT,
                                    COST_PRICE,
                                    REORDER_POINT,
                                    DESCRIPTION
                                )
                            VALUES
                                (
                                    '{row_value['Item Name']}',
                                    {row_value['Price']},
                                    {row_value['Units Sold']},
                                    {row_value['Units Left']},
                                    {row_value['Cost Price']},
                                    {row_value['Reorder Point']},
                                    '{row_value['Description']}'
                                )
                            """
                ).collect()
                
            st.toast("Data have being added!")
        # except:
        #     st.toast("Something went wrong while adding the data, try again.")

    if changes["deleted_rows"]:
        # try:
            for row_value in changes["deleted_rows"]:
                conn.query(
                    f"""
                    DELETE FROM
                        INVENTORY
                    WHERE
                        ID = {dataframe.iloc[row_value]['ID']}
                    """
                ).collect()
            st.toast("Data have being delete!")
        # except:
        #     st.toast("Something went wrong while deleting the data, try again.")


# -----------------------------------------------------------------------------
# Draw the actual page, starting with the inventory table.
# -----------------------------------------------------------------------------

st.title("Inventory Tracker 📊")
st.write("This page reads and writes directly from/to our inventory database.")
st.info(
    """
    Use the table below to add, remove, and edit items.
    And don't forget to commit your changes when you're done.
    """,
    icon="ℹ️"
)

product_data = load_product_data()
edited_product_data = st.data_editor(
    product_data,
    disabled=["ID"],  # Don't allow editing the 'id' column.
    num_rows="dynamic",  # Allow appending/deleting rows.
    column_config={
        # Show dollar sign before price columns.
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "Cost Price": st.column_config.NumberColumn(format="$%.2f"),
        "Image": st.column_config.ImageColumn(),
    },
    key="inventory_table",
    use_container_width=True,
)

has_uncommitted_changes = any(len(v) for v in st.session_state.inventory_table.values())

st.button(
    "Commit changes",
    type="secondary",
    disabled=not has_uncommitted_changes,
    on_click=update_product_data,
    args=(product_data, st.session_state.inventory_table),
)


# -----------------------------------------------------------------------------
# Now some cool charts
# -----------------------------------------------------------------------------

st.subheader("Units left", divider="green")

need_to_reorder = product_data[
    product_data["Units Left"] < product_data["Reorder Point"]
].loc[:, "Item Name"]

if len(need_to_reorder) > 0:
    items = "\n".join(f"* {name}" for name in need_to_reorder)
    st.warning(f"We're running dangerously low on the items below:\n {items}")

st.altair_chart(
    alt.Chart(product_data)
    .mark_bar(orient="horizontal", color="#52c234")
    .encode(
        x="Units Left",
        y="Item Name",
    )
    + alt.Chart(product_data)
    .mark_point(
        shape="diamond",
        filled=True,
        size=50,
        color="#061700",
        opacity=1,
    )
    .encode(
        x="Reorder Point",
        y="Item Name",
    ),
    use_container_width=True,
)

st.caption("NOTE: The :diamonds: location shows the reorder point.")

st.subheader("Best sellers", divider="green")

st.altair_chart(
    alt.Chart(product_data)
    .mark_bar(orient="horizontal", color="#1D976C")
    .encode(
        x="Units Sold",
        y=alt.Y("Item Name").sort("-x"),
    ),
    use_container_width=True,
)

# -----------------------------------------------------------------------------
# Integrate Gemini AI 
# -----------------------------------------------------------------------------

GOOGLE_API_KEY='AIzaSyACHHCOwRML8WnizHQzu7_Eqv2Kmqm7Eog'
genai.configure(api_key=GOOGLE_API_KEY)

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '✨'

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir('data/')
except:
    # data/ folder already exists
    pass

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

# Sidebar allows a list of past chats
with st.sidebar:
    st.write('# Past Chats')
    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            placeholder='_',
        )
    else:
        # This will happen the first time AI response comes in
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
            placeholder='_',
        )
    # Save new chats after a message has been sent to AI
    # TODO: Give user a chance to name chat
    st.session_state.chat_title = f'ChatSession-{st.session_state.chat_id}'

st.write('# Chat with Gemini')

# Chat history (allows to ask multiple questions)
try:
    st.session_state.messages = joblib.load(
        f'data/{st.session_state.chat_id}-st_messages'
    )
    st.session_state.gemini_history = joblib.load(
        f'data/{st.session_state.chat_id}-gemini_messages'
    )
    # print('old cache')
except:
    st.session_state.messages = []
    st.session_state.gemini_history = []
    # print('new_cache made')
st.session_state.model = genai.GenerativeModel('gemini-pro')
st.session_state.chat = st.session_state.model.start_chat(
    history=st.session_state.gemini_history,
)

# inventory_data = load_product_data() 
# result = inventory_data.to_json(orient="split")
# parsed = loads(result)
# st.session_state.chat.send_message(f"Generate my inventory data based on {MY_INVENTORY_DATA}. Act as my personal ")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        name=message['role'],
        avatar=message.get('avatar'),
    ):
        st.markdown(message['content'])

# React to user input
if prompt := st.chat_input('Your message here...'):
    # Save this as a chat for later
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')
    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append(
        dict(
            role='user',
            content=prompt,
        )
    )
    ## Send message to AI
    response = st.session_state.chat.send_message(
        prompt,
        stream=True,
    )
    # Display assistant response in chat message container
    with st.chat_message(
        name=MODEL_ROLE,
        avatar=AI_AVATAR_ICON,
    ):
        message_placeholder = st.empty()
        full_response = ''
        assistant_response = response
        # Streams in a chunk at a time
        for chunk in response:
            # Simulate stream of chunk
            # TODO: Chunk missing `text` if API stops mid-stream ("safety"?)
            for ch in chunk.text.split(' '):
                full_response += ch + ' '
                time.sleep(0.05)
                # Rewrites with a cursor at end
                message_placeholder.write(full_response + '▌')
        # Write full message with placeholder
        message_placeholder.write(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append(
        dict(
            role=MODEL_ROLE,
            content=st.session_state.chat.history[-1].parts[0].text,
            avatar=AI_AVATAR_ICON,
        )
    )
    st.session_state.gemini_history = st.session_state.chat.history
    # Save to file
    joblib.dump(
        st.session_state.messages,
        f'data/{st.session_state.chat_id}-st_messages',
    )
    joblib.dump(
        st.session_state.gemini_history,
        f'data/{st.session_state.chat_id}-gemini_messages',
    )