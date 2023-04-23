import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from apps import INFO_HEADER, INFO_FOOTER, badge

st.set_page_config(
    page_title="AMPL on Streamlit Cloud",
    page_icon="👋",
)


@st.cache_data
def activate_license():
    from amplpy import modules

    # Activate the license (e.g., a free https://ampl.com/ce license)
    uuid = os.environ.get("AMPLKEY_UUID", None)
    if uuid is not None:
        modules.activate(uuid)
    return uuid


activate_license()


# Banner
st.image("https://portal.ampl.com/dl/ads/python_ecosystem_badge.png")

st.write("# Welcome to AMPL on Streamlit! 👋")

st.sidebar.success("Select an app above.")


st.markdown(INFO_HEADER)

st.markdown(
    """
**👈 Select a demo from the sidebar** to see some examples
    of what you can do with AMPL on Streamlit!
"""
)

st.markdown(INFO_FOOTER)
st.markdown(badge(""))

st.markdown(
    """
[[App Source Code on GitHub](https://github.com/fdabrandao/amplopt.streamlit.app/tree/master/apps/tips)]
[[Build your own App with AMPL & Streamlit](https://dev.ampl.com/ampl/python/streamlit.html)]
"""
)
