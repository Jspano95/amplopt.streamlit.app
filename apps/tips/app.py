import os
import sys
import streamlit as st
from .content import tip1, tip2, tip3, tip4, tip5, tip6, tip7


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def main():
    tips = [(t.title, t.run) for t in [tip1, tip2, tip3, tip4, tip5, tip6, tip7]]
    tip_titles = [title for title, _ in tips]

    def update_params():
        st.experimental_set_query_params(
            tip=tip_titles.index(st.session_state.title) + 1
        )

    st.markdown("# AMPL Modeling Tips")

    query_params = st.experimental_get_query_params()

    tip_index = len(tip_titles) - 1
    if query_params:
        if "tip" in query_params and query_params["tip"][0].isnumeric():
            tip = int(query_params["tip"][0])
            tip_index = min(max(tip, 1), len(tip_titles)) - 1
    st.session_state.title = tip_titles[tip_index]

    selected_tip = st.selectbox(
        "Pick the tip 👇", tip_titles, key="title", on_change=update_params
    )
    tip_index = tip_titles.index(selected_tip)

    title, run = tips[tip_index]
    st.markdown(f"### 💡 {title}")
    run()
