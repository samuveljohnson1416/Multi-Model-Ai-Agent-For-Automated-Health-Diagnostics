"""Questions — ask about the open report."""

# pyrefly: ignore [missing-import]
import streamlit as st

import api_client
from session import init_session_state
from theme import apply_chrome, rendered

apply_chrome()
init_session_state()

st.title("Questions")

if not st.session_state.get("report_id"):
    st.write("Questions are answered about an open report. Analyze a report first.")
    if st.button("Analyze a report", type="primary"):
        st.switch_page("pages/upload.py")
    st.stop()

report_id = st.session_state.report_id
st.caption(f"Answering questions about {st.session_state.get('report_name', 'your report')}.")


def ask(question: str) -> None:
    st.session_state.chat_history.append({"role": "user", "content": question})
    answer = api_client.send_chat_message(
        report_id=report_id, message=question, user_id=st.session_state.user_id,
    )
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer or (
            "The answer service did not respond. Check that the backend is running, then ask again."
        ),
    })


for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(rendered(msg["content"]))

if not st.session_state.chat_history:
    st.write("A few things people often ask:")
    for q in (
        "Which values are outside the normal range?",
        "What could my low hemoglobin be caused by?",
        "Which of these should I follow up on first?",
        "What tests might my doctor suggest next?",
    ):
        if st.button(q, use_container_width=True):
            with st.spinner("Finding an answer…"):
                ask(q)
            st.rerun()

if prompt := st.chat_input("Ask about your report"):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"), st.spinner("Finding an answer…"):
        ask(prompt)
        st.markdown(rendered(st.session_state.chat_history[-1]["content"]))
