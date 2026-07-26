"""
Chat Page — interactive Q&A about blood reports.
"""

import streamlit as st
import api_client


st.header("💬 Ask Questions About Your Report")

# ── Check for active report ───────────────────────────────────
if not st.session_state.get("report_id"):
    st.info("No report loaded. Please upload and analyze a report first.")
    st.stop()

report_id = st.session_state.report_id
st.caption(f"Chatting about report: `{report_id[:8]}...`")

# ── Chat History Display ──────────────────────────────────────
for msg in st.session_state.chat_history:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])

# ── Chat Input ────────────────────────────────────────────────
if prompt := st.chat_input("Ask about your blood report..."):
    # Show user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = api_client.send_chat_message(
                report_id=report_id,
                message=prompt,
                user_id=st.session_state.user_id,
            )

        if response:
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            error_msg = "Sorry, I couldn't process that. Please check the backend connection."
            st.error(error_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

# ── Suggested Questions ───────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("### Suggested questions:")
    suggestions = [
        "What are the abnormal values in my report?",
        "Give me an overall summary of my results.",
        "What does my hemoglobin level indicate?",
        "Should I be concerned about any values?",
        "What follow-up tests should I consider?",
    ]
    for suggestion in suggestions:
        if st.button(suggestion, use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": suggestion})
            with st.spinner("Getting answer..."):
                response = api_client.send_chat_message(
                    report_id=report_id,
                    message=suggestion,
                    user_id=st.session_state.user_id,
                )
            if response:
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
