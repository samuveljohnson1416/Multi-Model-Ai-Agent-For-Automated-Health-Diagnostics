"""
Advanced Context Manager
Manages long-term user history, cross-session state, and conversation flow tracking
"""

import json
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class ContextType(Enum):
    """Types of context information"""
    USER_PROFILE = "user_profile"
    CONVERSATION_HISTORY = "conversation_history"
    MEDICAL_HISTORY = "medical_history"
    PREFERENCES = "preferences"
    SESSION_STATE = "session_state"
    WORKFLOW_HISTORY = "workflow_history"


@dataclass
class ConversationMessage:
    """Individual conversation message"""
    message_id: str
    session_id: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    intent: Optional[str] = None
    context_used: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class UserSession:
    """User session information"""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    session_type: str  # 'analysis', 'comparison', 'consultation'
    reports_processed: List[str]
    goals_achieved: List[str]
    context_snapshot: Dict[str, Any]


@dataclass
class UserProfile:
    """Long-term user profile"""
    user_id: str
    created_at: datetime
    last_seen: datetime
    total_sessions: int
    total_reports_analyzed: int
    preferred_detail_level: str  # 'summary', 'detailed', 'technical'
    common_concerns: List[str]
    medical_context: Dict[str, Any]
    preferences: Dict[str, Any]


class AdvancedContextManager:
    """
    Advanced context management with persistent storage and intelligent retrieval
    """
    
    def __init__(self, db_path: str = "user_context.db"):
        self.db_path = db_path
        self.current_session_id = None
        self.current_user_id = None
        self.session_context = {}
        
        # Initialize database
        self._initialize_database()
        
        # Context retrieval strategies
        self.context_strategies = {
            'recent_conversation': self._get_recent_conversation_context,
            'user_preferences': self._get_user_preferences_context,
            'medical_history': self._get_medical_history_context,
            'workflow_patterns': self._get_workflow_patterns_context,
            'session_continuity': self._get_session_continuity_context
        }
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent context storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    last_seen TEXT,
                    total_sessions INTEGER DEFAULT 0,
                    total_reports_analyzed INTEGER DEFAULT 0,
                    preferred_detail_level TEXT DEFAULT 'detailed',
                    common_concerns TEXT,  -- JSON array
                    medical_context TEXT,  -- JSON object
                    preferences TEXT       -- JSON object
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    started_at TEXT,
                    last_activity TEXT,
                    session_type TEXT,
                    reports_processed TEXT,  -- JSON array
                    goals_achieved TEXT,     -- JSON array
                    context_snapshot TEXT,   -- JSON object
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Conversation history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    role TEXT,
                    content TEXT,
                    intent TEXT,
                    context_used TEXT,  -- JSON object
                    metadata TEXT,      -- JSON object
                    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
                )
            ''')
            
            # Medical history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_history (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    report_date TEXT,
                    report_type TEXT,
                    parameters TEXT,     -- JSON object
                    analysis_results TEXT,  -- JSON object
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Workflow history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_history (
                    workflow_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_id TEXT,
                    workflow_type TEXT,
                    intent TEXT,
                    actions_taken TEXT,  -- JSON array
                    success_rate REAL,
                    execution_time REAL,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
                )
            ''')
            
            conn.commit()
    
    def start_session(self, user_id: str = None, session_type: str = "analysis") -> str:
        """Start a new user session"""
        if not user_id:
            user_id = str(uuid.uuid4())
        
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.current_user_id = user_id
        
        # Create or update user profile
        self._ensure_user_profile(user_id)
        
        # Create session record
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            session_type=session_type,
            reports_processed=[],
            goals_achieved=[],
            context_snapshot={}
        )
        
        self._save_session(session)
        
        # Initialize session context
        self.session_context = {
            'session_id': session_id,
            'user_id': user_id,
            'session_type': session_type,
            'started_at': datetime.now().isoformat(),  # Convert to string for JSON serialization
            'conversation_count': 0,
            'current_workflow': None,
            'active_reports': [],
            'user_preferences': self._get_user_preferences(user_id)
        }
        
        return session_id
    
    def add_conversation_message(self, role: str, content: str, intent: str = None, 
                               context_used: Dict = None, metadata: Dict = None):
        """Add a message to conversation history"""
        if not self.current_session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        message = ConversationMessage(
            message_id=str(uuid.uuid4()),
            session_id=self.current_session_id,
            timestamp=datetime.now(),
            role=role,
            content=content,
            intent=intent,
            context_used=context_used,
            metadata=metadata
        )
        
        self._save_conversation_message(message)
        
        # Update session context
        self.session_context['conversation_count'] += 1
        self.session_context['last_message'] = {
            'role': role,
            'content': content,
            'intent': intent,
            'timestamp': datetime.now().isoformat()  # Convert to string for JSON serialization
        }
        
        # Update session activity
        self._update_session_activity()
    
    def get_contextual_information(self, strategies: List[str] = None, 
                                 max_context_age_hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive contextual information using specified strategies
        
        Args:
            strategies: List of context retrieval strategies to use
            max_context_age_hours: Maximum age of context to consider
            
        Returns:
            Comprehensive context dictionary
        """
        if not strategies:
            strategies = list(self.context_strategies.keys())
        
        context = {
            'session_info': self.session_context.copy(),
            'retrieval_timestamp': datetime.now().isoformat(),
            'strategies_used': strategies
        }
        
        # Apply each context retrieval strategy
        for strategy in strategies:
            if strategy in self.context_strategies:
                try:
                    strategy_context = self.context_strategies[strategy](max_context_age_hours)
                    context[strategy] = strategy_context
                except Exception as e:
                    context[f"{strategy}_error"] = str(e)
        
        return context
    
    def _get_recent_conversation_context(self, max_age_hours: int) -> Dict[str, Any]:
        """Get recent conversation context"""
        if not self.current_session_id:
            return {}
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, intent, timestamp, context_used, metadata
                FROM conversation_history
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (self.current_session_id, cutoff_time.isoformat()))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'intent': row[2],
                    'timestamp': row[3],
                    'context_used': json.loads(row[4]) if row[4] else None,
                    'metadata': json.loads(row[5]) if row[5] else None
                })
        
        # Analyze conversation patterns
        user_messages = [m for m in messages if m['role'] == 'user']
        intents = [m['intent'] for m in user_messages if m['intent']]
        
        return {
            'recent_messages': messages[:10],  # Last 10 messages
            'conversation_length': len(messages),
            'dominant_intents': self._get_dominant_intents(intents),
            'conversation_flow': self._analyze_conversation_flow(messages),
            'user_engagement_level': self._assess_engagement_level(messages)
        }
    
    def _get_user_preferences_context(self, max_age_hours: int) -> Dict[str, Any]:
        """Get user preferences and behavioral patterns"""
        if not self.current_user_id:
            return {}
        
        profile = self._get_user_profile(self.current_user_id)
        if not profile:
            return {}
        
        # Get recent session patterns
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours * 24)  # Extend for preferences
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_type, goals_achieved, context_snapshot
                FROM user_sessions
                WHERE user_id = ? AND started_at > ?
                ORDER BY started_at DESC
                LIMIT 10
            ''', (self.current_user_id, cutoff_time.isoformat()))
            
            recent_sessions = []
            for row in cursor.fetchall():
                recent_sessions.append({
                    'session_type': row[0],
                    'goals_achieved': json.loads(row[1]) if row[1] else [],
                    'context_snapshot': json.loads(row[2]) if row[2] else {}
                })
        
        return {
            'preferred_detail_level': profile.preferred_detail_level,
            'common_concerns': profile.common_concerns,
            'total_experience': {
                'sessions': profile.total_sessions,
                'reports_analyzed': profile.total_reports_analyzed
            },
            'recent_session_patterns': recent_sessions,
            'user_preferences': profile.preferences
        }
    
    def _get_medical_history_context(self, max_age_hours: int) -> Dict[str, Any]:
        """Get relevant medical history context"""
        if not self.current_user_id:
            return {}
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours * 24 * 30)  # 30 days for medical history
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT report_date, report_type, parameters, analysis_results
                FROM medical_history
                WHERE user_id = ? AND created_at > ?
                ORDER BY report_date DESC
                LIMIT 5
            ''', (self.current_user_id, cutoff_time.isoformat()))
            
            medical_records = []
            for row in cursor.fetchall():
                medical_records.append({
                    'report_date': row[0],
                    'report_type': row[1],
                    'parameters': json.loads(row[2]) if row[2] else {},
                    'analysis_results': json.loads(row[3]) if row[3] else {}
                })
        
        # Analyze medical trends
        trends = self._analyze_medical_trends(medical_records)
        
        return {
            'recent_reports': medical_records,
            'medical_trends': trends,
            'health_concerns': self._extract_health_concerns(medical_records),
            'parameter_history': self._build_parameter_history(medical_records)
        }
    
    def _get_workflow_patterns_context(self, max_age_hours: int) -> Dict[str, Any]:
        """Get workflow execution patterns and success rates"""
        if not self.current_user_id:
            return {}
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours * 24)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT workflow_type, intent, actions_taken, success_rate, execution_time
                FROM workflow_history
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 20
            ''', (self.current_user_id, cutoff_time.isoformat()))
            
            workflows = []
            for row in cursor.fetchall():
                workflows.append({
                    'workflow_type': row[0],
                    'intent': row[1],
                    'actions_taken': json.loads(row[2]) if row[2] else [],
                    'success_rate': row[3],
                    'execution_time': row[4]
                })
        
        # Analyze workflow patterns
        patterns = self._analyze_workflow_patterns(workflows)
        
        return {
            'recent_workflows': workflows[:10],
            'workflow_patterns': patterns,
            'preferred_workflows': self._get_preferred_workflows(workflows),
            'success_metrics': self._calculate_workflow_success_metrics(workflows)
        }
    
    def _get_session_continuity_context(self, max_age_hours: int) -> Dict[str, Any]:
        """Get context for maintaining session continuity"""
        return {
            'current_session': self.session_context,
            'session_duration': self._get_session_duration(),
            'interaction_frequency': self._calculate_interaction_frequency(),
            'context_switches': self._detect_context_switches(),
            'unresolved_queries': self._identify_unresolved_queries()
        }
    
    def _get_session_duration(self) -> float:
        """Get session duration in minutes"""
        started_at_str = self.session_context.get('started_at')
        if not started_at_str:
            return 0.0
        
        try:
            started_at = datetime.fromisoformat(started_at_str)
            return (datetime.now() - started_at).total_seconds() / 60
        except (ValueError, TypeError):
            return 0.0
    
    def save_medical_record(self, report_date: str, report_type: str, 
                          parameters: Dict, analysis_results: Dict):
        """Save medical record to history"""
        if not self.current_user_id:
            return
        
        record_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO medical_history 
                (record_id, user_id, report_date, report_type, parameters, analysis_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id,
                self.current_user_id,
                report_date,
                report_type,
                json.dumps(parameters),
                json.dumps(analysis_results),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        # Update user profile
        self._update_user_profile_stats()
    
    def save_workflow_execution(self, workflow_id: str, workflow_type: str, 
                              intent: str, actions_taken: List, success_rate: float, 
                              execution_time: float):
        """Save workflow execution to history"""
        if not self.current_user_id or not self.current_session_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO workflow_history 
                (workflow_id, user_id, session_id, workflow_type, intent, actions_taken, 
                 success_rate, execution_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow_id,
                self.current_user_id,
                self.current_session_id,
                workflow_type,
                intent,
                json.dumps(actions_taken),
                success_rate,
                execution_time,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def update_user_preferences(self, preferences: Dict):
        """Update user preferences"""
        if not self.current_user_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_profiles 
                SET preferences = ?, last_seen = ?
                WHERE user_id = ?
            ''', (
                json.dumps(preferences),
                datetime.now().isoformat(),
                self.current_user_id
            ))
            conn.commit()
        
        # Update session context
        self.session_context['user_preferences'] = preferences
    
    def end_session(self, goals_achieved: List[str] = None):
        """End current session and save final state"""
        if not self.current_session_id:
            return
        
        # Update session record
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_sessions 
                SET last_activity = ?, goals_achieved = ?, context_snapshot = ?
                WHERE session_id = ?
            ''', (
                datetime.now().isoformat(),
                json.dumps(goals_achieved or []),
                json.dumps(self.session_context),
                self.current_session_id
            ))
            conn.commit()
        
        # Clear session state
        self.current_session_id = None
        self.session_context = {}
    
    # Helper methods for context analysis
    def _ensure_user_profile(self, user_id: str):
        """Ensure user profile exists"""
        profile = self._get_user_profile(user_id)
        if not profile:
            self._create_user_profile(user_id)
    
    def _create_user_profile(self, user_id: str):
        """Create new user profile"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_profiles 
                (user_id, created_at, last_seen, common_concerns, medical_context, preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps([]),
                json.dumps({}),
                json.dumps({'detail_level': 'detailed', 'language': 'english'})
            ))
            conn.commit()
    
    def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return UserProfile(
                    user_id=row[0],
                    created_at=datetime.fromisoformat(row[1]),
                    last_seen=datetime.fromisoformat(row[2]),
                    total_sessions=row[3],
                    total_reports_analyzed=row[4],
                    preferred_detail_level=row[5],
                    common_concerns=json.loads(row[6]) if row[6] else [],
                    medical_context=json.loads(row[7]) if row[7] else {},
                    preferences=json.loads(row[8]) if row[8] else {}
                )
        return None
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences"""
        profile = self._get_user_profile(user_id)
        return profile.preferences if profile else {}
    
    def _save_session(self, session: UserSession):
        """Save session to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, started_at, last_activity, session_type, 
                 reports_processed, goals_achieved, context_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.user_id,
                session.started_at.isoformat(),
                session.last_activity.isoformat(),
                session.session_type,
                json.dumps(session.reports_processed),
                json.dumps(session.goals_achieved),
                json.dumps(session.context_snapshot)
            ))
            conn.commit()
    
    def _save_conversation_message(self, message: ConversationMessage):
        """Save conversation message to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_history 
                (message_id, session_id, timestamp, role, content, intent, context_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.message_id,
                message.session_id,
                message.timestamp.isoformat(),
                message.role,
                message.content,
                message.intent,
                json.dumps(message.context_used) if message.context_used else None,
                json.dumps(message.metadata) if message.metadata else None
            ))
            conn.commit()
    
    def _update_session_activity(self):
        """Update session last activity timestamp"""
        if not self.current_session_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_sessions 
                SET last_activity = ?
                WHERE session_id = ?
            ''', (datetime.now().isoformat(), self.current_session_id))
            conn.commit()
    
    def _update_user_profile_stats(self):
        """Update user profile statistics"""
        if not self.current_user_id:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_profiles 
                SET total_reports_analyzed = total_reports_analyzed + 1,
                    last_seen = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), self.current_user_id))
            conn.commit()
    
    # Analysis helper methods
    def _get_dominant_intents(self, intents: List[str]) -> List[Tuple[str, int]]:
        """Get most common intents from conversation"""
        intent_counts = {}
        for intent in intents:
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _analyze_conversation_flow(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        if len(messages) < 2:
            return {'pattern': 'insufficient_data'}
        
        # Analyze question-answer patterns
        qa_pairs = 0
        clarification_requests = 0
        
        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]
            
            if current['role'] == 'user' and next_msg['role'] == 'assistant':
                qa_pairs += 1
            
            if 'clarif' in current['content'].lower() or '?' in current['content']:
                clarification_requests += 1
        
        return {
            'qa_pairs': qa_pairs,
            'clarification_requests': clarification_requests,
            'conversation_coherence': qa_pairs / max(len(messages) // 2, 1),
            'user_engagement': len([m for m in messages if m['role'] == 'user']) / len(messages)
        }
    
    def _assess_engagement_level(self, messages: List[Dict]) -> str:
        """Assess user engagement level"""
        if not messages:
            return 'none'
        
        user_messages = [m for m in messages if m['role'] == 'user']
        avg_length = sum(len(m['content']) for m in user_messages) / max(len(user_messages), 1)
        
        if avg_length > 50 and len(user_messages) > 3:
            return 'high'
        elif avg_length > 20 and len(user_messages) > 1:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_medical_trends(self, records: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in medical records"""
        if len(records) < 2:
            return {'trend_analysis': 'insufficient_data'}
        
        # Simple trend analysis - can be enhanced
        parameter_trends = {}
        
        for record in records:
            for param, value in record.get('parameters', {}).items():
                if param not in parameter_trends:
                    parameter_trends[param] = []
                parameter_trends[param].append({
                    'date': record['report_date'],
                    'value': value
                })
        
        return {
            'parameters_tracked': len(parameter_trends),
            'trend_data': parameter_trends,
            'analysis_period': f"{records[-1]['report_date']} to {records[0]['report_date']}"
        }
    
    def _extract_health_concerns(self, records: List[Dict]) -> List[str]:
        """Extract health concerns from medical records"""
        concerns = set()
        
        for record in records:
            analysis = record.get('analysis_results', {})
            abnormal_params = analysis.get('abnormal_parameters', [])
            
            for param in abnormal_params:
                concerns.add(param.get('parameter', ''))
        
        return list(concerns)
    
    def _build_parameter_history(self, records: List[Dict]) -> Dict[str, List]:
        """Build parameter history from records"""
        history = {}
        
        for record in records:
            for param, value in record.get('parameters', {}).items():
                if param not in history:
                    history[param] = []
                
                history[param].append({
                    'date': record['report_date'],
                    'value': value,
                    'report_type': record['report_type']
                })
        
        return history
    
    def _analyze_workflow_patterns(self, workflows: List[Dict]) -> Dict[str, Any]:
        """Analyze workflow execution patterns"""
        if not workflows:
            return {'pattern_analysis': 'no_data'}
        
        workflow_types = [w['workflow_type'] for w in workflows]
        intents = [w['intent'] for w in workflows]
        
        return {
            'most_common_workflows': self._get_dominant_intents(workflow_types),
            'most_common_intents': self._get_dominant_intents(intents),
            'average_success_rate': sum(w['success_rate'] for w in workflows) / len(workflows),
            'average_execution_time': sum(w['execution_time'] for w in workflows) / len(workflows)
        }
    
    def _get_preferred_workflows(self, workflows: List[Dict]) -> List[str]:
        """Get user's preferred workflow types"""
        workflow_success = {}
        
        for workflow in workflows:
            wf_type = workflow['workflow_type']
            if wf_type not in workflow_success:
                workflow_success[wf_type] = []
            workflow_success[wf_type].append(workflow['success_rate'])
        
        # Calculate average success rate per workflow type
        avg_success = {}
        for wf_type, success_rates in workflow_success.items():
            avg_success[wf_type] = sum(success_rates) / len(success_rates)
        
        # Return workflows sorted by success rate
        return sorted(avg_success.keys(), key=lambda x: avg_success[x], reverse=True)
    
    def _calculate_workflow_success_metrics(self, workflows: List[Dict]) -> Dict[str, float]:
        """Calculate workflow success metrics"""
        if not workflows:
            return {}
        
        return {
            'overall_success_rate': sum(w['success_rate'] for w in workflows) / len(workflows),
            'completion_rate': len([w for w in workflows if w['success_rate'] > 0.8]) / len(workflows),
            'efficiency_score': 1.0 / (sum(w['execution_time'] for w in workflows) / len(workflows))
        }
    
    def _calculate_interaction_frequency(self) -> float:
        """Calculate interaction frequency in current session"""
        started_at_str = self.session_context.get('started_at')
        if not started_at_str:
            return 0.0
        
        try:
            started_at = datetime.fromisoformat(started_at_str)
            session_duration = (datetime.now() - started_at).total_seconds() / 60
            conversation_count = self.session_context.get('conversation_count', 0)
            
            return conversation_count / max(session_duration, 1)
        except (ValueError, TypeError):
            return 0.0
    
    def _detect_context_switches(self) -> List[str]:
        """Detect context switches in conversation"""
        # Simplified implementation - can be enhanced
        return []
    
    def _identify_unresolved_queries(self) -> List[str]:
        """Identify unresolved queries from conversation"""
        # Simplified implementation - can be enhanced
        return []


# Convenience functions for easy integration
def create_context_manager(db_path: str = "user_context.db") -> AdvancedContextManager:
    """Create and return a context manager instance"""
    return AdvancedContextManager(db_path)


def get_user_context(context_manager: AdvancedContextManager, 
                    strategies: List[str] = None) -> Dict[str, Any]:
    """Get comprehensive user context"""
    return context_manager.get_contextual_information(strategies)