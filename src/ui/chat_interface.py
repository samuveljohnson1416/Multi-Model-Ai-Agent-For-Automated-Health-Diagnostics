"""
Modern Chat Interface for Medical Q&A Assistant
Provides a GPT-like chat experience for blood report analysis
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional
from datetime import datetime


class MedicalChatInterface:
    """Modern chat interface for medical Q&A"""
    
    def __init__(self, qa_assistant, session_key: str = "medical_chat"):
        self.qa_assistant = qa_assistant
        self.session_key = session_key
        self.initialize_chat()
    
    def initialize_chat(self):
        """Initialize chat history with welcome message"""
        chat_key = f"{self.session_key}_history"
        
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
            
            # Add welcome message
            welcome_msg = """👋 **Hello! I'm your AI Medical Assistant.**

I can help you understand your blood report analysis using only your actual medical data.

**What I can help with:**
• 🔬 Test results and their meanings
• ⚠️ Risk levels and health patterns  
• 💡 Lifestyle recommendations
• 👤 Age/gender context in your analysis
• 🔍 Abnormal findings explanations

**Important:** I only use information from your blood report analysis - no external medical knowledge or diagnosis."""
            
            st.session_state[chat_key].append({
                "role": "assistant",
                "content": welcome_msg,
                "timestamp": time.time(),
                "type": "welcome"
            })
    
    def render_message(self, message: Dict[str, Any], index: int):
        """Render a single chat message with modern styling"""
        
        if message["role"] == "user":
            # User message (right-aligned, blue bubble)
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 15px 0;">
                <div style="
                    background: linear-gradient(135deg, #0084ff, #0066cc);
                    color: white;
                    padding: 12px 18px;
                    border-radius: 20px 20px 5px 20px;
                    max-width: 70%;
                    word-wrap: break-word;
                    box-shadow: 0 2px 10px rgba(0, 132, 255, 0.3);
                    font-size: 14px;
                    line-height: 1.4;
                ">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # Assistant message (left-aligned, gray bubble)
            timestamp = datetime.fromtimestamp(message["timestamp"]).strftime("%H:%M")
            
            # Check if message indicates unavailable information
            is_unavailable = "not available in your blood report analysis" in message["content"]
            bubble_color = "#fff3cd" if is_unavailable else "#f8f9fa"
            border_color = "#ffeaa7" if is_unavailable else "#e9ecef"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 15px 0;">
                <div style="
                    background-color: {bubble_color};
                    color: #333;
                    padding: 12px 18px;
                    border-radius: 20px 20px 20px 5px;
                    max-width: 85%;
                    word-wrap: break-word;
                    border: 1px solid {border_color};
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    font-size: 14px;
                    line-height: 1.5;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 600; color: #1f77b4; font-size: 12px;">
                            🤖 AI Medical Assistant
                        </span>
                        <span style="color: #666; font-size: 11px; margin-left: auto;">
                            {timestamp}
                        </span>
                    </div>
                    <div style="white-space: pre-wrap;">
                        {message["content"]}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_chat_history(self):
        """Render the complete chat history"""
        chat_key = f"{self.session_key}_history"
        
        # Chat container with scrolling
        with st.container():
            st.markdown("""
            <div style="
                max-height: 500px;
                overflow-y: auto;
                padding: 10px;
                background: linear-gradient(to bottom, #fafafa, #ffffff);
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                margin-bottom: 20px;
            ">
            """, unsafe_allow_html=True)
            
            # Render messages
            for i, message in enumerate(st.session_state[chat_key]):
                self.render_message(message, i)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("**💡 Quick Questions:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        quick_questions = [
            ("📊 Overall Status", "What is my overall health status based on the analysis?"),
            ("⚠️ Risk Assessment", "What is my risk level and what does it mean?"),
            ("💡 Recommendations", "What lifestyle recommendations do you have for me?"),
            ("🔬 Abnormal Results", "Which of my test results are abnormal and why?")
        ]
        
        for i, (button_text, question) in enumerate(quick_questions):
            with [col1, col2, col3, col4][i]:
                if st.button(button_text, key=f"quick_{i}", use_container_width=True):
                    self.add_user_message(question)
                    self.get_ai_response(question)
                    st.rerun()
    
    def render_chat_input(self):
        """Render the chat input form"""
        with st.form(key=f"{self.session_key}_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input(
                    "Message",
                    placeholder="Ask me anything about your blood report analysis...",
                    label_visibility="collapsed",
                    key=f"{self.session_key}_input"
                )
            
            with col2:
                send_button = st.form_submit_button(
                    "Send 📤", 
                    use_container_width=True,
                    type="primary"
                )
            
            if send_button and user_input.strip():
                self.add_user_message(user_input.strip())
                self.get_ai_response(user_input.strip())
                st.rerun()
    
    def render_chat_controls(self):
        """Render chat control buttons"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ Clear Chat", key=f"{self.session_key}_clear"):
                self.clear_chat()
                st.rerun()
        
        with col2:
            if st.button("📋 Available Topics", key=f"{self.session_key}_topics"):
                self.show_available_topics()
                st.rerun()
        
        with col3:
            if st.button("💾 Export Chat", key=f"{self.session_key}_export"):
                self.export_chat()
        
        with col4:
            st.markdown("*💡 Ask specific questions for detailed explanations*")
    
    def add_user_message(self, content: str):
        """Add user message to chat history"""
        chat_key = f"{self.session_key}_history"
        
        st.session_state[chat_key].append({
            "role": "user",
            "content": content,
            "timestamp": time.time(),
            "type": "question"
        })
    
    def get_ai_response(self, question: str):
        """Get AI response with progress indicators"""
        chat_key = f"{self.session_key}_history"
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        def update_progress(message):
            progress_placeholder.info(f"⚡ {message}")
        
        # Get response with progress updates
        try:
            # Check if we have the new progress method
            if hasattr(self.qa_assistant, 'answer_question_with_progress'):
                answer = self.qa_assistant.answer_question_with_progress(question, update_progress)
            else:
                # Fallback to regular method with simple progress
                update_progress("Processing your question...")
                answer = self.qa_assistant.answer_question(question)
        except Exception as e:
            answer = f"Error processing question: {str(e)}"
        finally:
            # Clear progress indicator
            progress_placeholder.empty()
        
        # Add response to chat history
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": answer,
            "timestamp": time.time(),
            "type": "response"
        })
    
    def clear_chat(self):
        """Clear chat history and reinitialize"""
        chat_key = f"{self.session_key}_history"
        if chat_key in st.session_state:
            del st.session_state[chat_key]
        
        # Also clear Q&A assistant cache for fresh start
        if hasattr(self.qa_assistant, 'clear_cache'):
            self.qa_assistant.clear_cache()
        self.initialize_chat()
    
    def show_available_topics(self):
        """Show available topics as assistant message"""
        chat_key = f"{self.session_key}_history"
        
        topics = self.qa_assistant.get_available_topics()
        topics_text = "**Here's what I can help you with based on your analysis:**\n\n"
        topics_text += "\n".join([f"• {topic}" for topic in topics])
        topics_text += "\n\n*Feel free to ask specific questions about any of these areas!*"
        
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": topics_text,
            "timestamp": time.time(),
            "type": "topics"
        })
    
    def export_chat(self):
        """Export chat history as downloadable text"""
        chat_key = f"{self.session_key}_history"
        
        if chat_key not in st.session_state or not st.session_state[chat_key]:
            st.warning("No chat history to export")
            return
        
        # Generate chat export
        export_text = "Blood Report Q&A Chat Export\n"
        export_text += "=" * 40 + "\n"
        export_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for message in st.session_state[chat_key]:
            timestamp = datetime.fromtimestamp(message["timestamp"]).strftime("%H:%M:%S")
            role = "You" if message["role"] == "user" else "AI Assistant"
            export_text += f"[{timestamp}] {role}:\n{message['content']}\n\n"
        
        export_text += "\nDisclaimer: This information is for educational purposes only and is not a substitute for professional medical advice."
        
        # Provide download button
        st.download_button(
            label="📥 Download Chat History",
            data=export_text,
            file_name=f"medical_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key=f"{self.session_key}_download"
        )
    
    def render_complete_interface(self):
        """Render the complete chat interface"""
        # Chat history
        self.render_chat_history()
        
        # Quick actions
        self.render_quick_actions()
        
        st.markdown("---")
        
        # Chat input
        self.render_chat_input()
        
        # Chat controls
        st.markdown("---")
        self.render_chat_controls()


def create_medical_chat_interface(qa_assistant, session_key: str = "medical_chat") -> MedicalChatInterface:
    """Factory function to create a medical chat interface"""
    return MedicalChatInterface(qa_assistant, session_key)