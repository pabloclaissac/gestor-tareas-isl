import streamlit as st

st.write("Hola mundo")

if st.button("Rerun"):
    st.experimental_rerun()
