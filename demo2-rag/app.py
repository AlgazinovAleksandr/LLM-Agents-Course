"""A small document browser and question-answering UI for Lecture 06."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import RagError, get_engine, load_corpus


APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")
DATA_DIR = Path(os.environ.get("BACKROOMS_DATA_DIR", APP_DIR / "data"))
STORAGE_DIR = Path(os.environ.get("BACKROOMS_STORAGE_DIR", APP_DIR / "storage"))

st.set_page_config(page_title="The Backrooms Archive", page_icon="🗂️", layout="wide")


@st.cache_resource(show_spinner=False)
def answer_service():
    return get_engine(DATA_DIR, STORAGE_DIR)


st.title("The Backrooms Archive")
st.caption("Read the records. Ask the archive.")

try:
    documents = load_corpus(DATA_DIR)
except (RagError, OSError, ValueError):
    st.error("The archive could not be loaded. Check that the corpus files are present.")
    st.stop()

ask_tab, documents_tab = st.tabs(["Ask the archive", "Documents"])

with ask_tab:
    with st.form("question_form"):
        question = st.text_input(
            "Your question", placeholder="What is Almond Water used for?", max_chars=2000
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted:
        st.session_state.pop("answer", None)
        st.session_state.pop("answered_question", None)
        if not question.strip():
            st.info("Enter a question about the archive.")
        else:
            try:
                with st.spinner("Reading the archive…"):
                    answer = answer_service().ask(question.strip())
                st.session_state.answer = answer
                st.session_state.answered_question = question.strip()
            except RagError as exc:
                st.error(str(exc))

    if "answer" in st.session_state:
        answer = st.session_state.answer
        st.subheader(st.session_state.answered_question)
        st.markdown(answer.text)
        if answer.sources:
            st.markdown("**Sources**")
            for source in answer.sources:
                st.markdown(f"[{source.number}. {source.title}]({source.url})")

with documents_tab:
    st.caption(f"{len(documents)} documents")
    labels = [doc.title for doc in documents]
    if len(set(labels)) != len(labels):
        labels = [f"{doc.title} · {doc.id}" for doc in documents]
    selected_label = st.selectbox("Document", options=labels, index=0, key="selected_document")
    if selected_label is not None:
        selected = documents[labels.index(selected_label)]
        st.markdown(f"[Read the original article]({selected.source_url})")
        st.markdown(selected.text)
        authors = ", ".join(selected.authors) if selected.authors else "See original article"
        st.caption(f"Authors: {authors} · {selected.license}")
