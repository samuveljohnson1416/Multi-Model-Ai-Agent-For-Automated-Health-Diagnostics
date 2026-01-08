"""
Goal-Oriented Workflow Manager
Translates inferred user intent into appropriate multi-step actions and workflows
"""

import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import uuid


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(Enum):
    """Types of actions in workflows"""
    DATA_RETRIEVAL = "data_retrieval"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    CLARIFICATION = "clarification"
    PRESENTATION = "presentation"
    EXPORT = "export"
    VALIDATION = "validation"


class WorkflowAction:
    """Individual action within a workflow"""
    
    def __init__(self, action_id: str, action_type: ActionType, description: str,
                 function: Callable, parameters: Dict = None, dependencies: List[str] = None):
        self.action_id = action_id
        self.action_type = action_type
        self.description = description
        self.function = function
        self.parameters = parameters or {}
        self.dependencies = dependencies or []
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the action with given context"""
        try:
            self.status = WorkflowStatus.IN_PROGRESS
            self.started_at = datetime.now()
            
            # Merge context with parameters
            execution_params = {**self.parameters, **context}
            
            # Execute the function
            self.result = self.function(**execution_params)
            
            self.status = WorkflowStatus.COMPLETED
            self.completed_at = datetime.now()
            
            return self.result
        
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            self.completed_at = datetime.now()
            raise e


class GoalOrientedWorkflow:
    """A complete workflow to achieve a user goal"""
    
    def __init__(self, workflow_id: str, goal_description: str, user_intent: str):
        self.workflow_id = workflow_id
        self.goal_description = goal_description
        self.user_intent = user_intent
        self.actions: List[WorkflowAction] = []
        self.status = WorkflowStatus.PENDING
        self.context = {}
        self.results = {}
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
    
    def add_action(self, action: WorkflowAction):
        """Add an action to the workflow"""
        self.actions.append(action)
    
    def execute(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the complete workflow"""
        self.status = WorkflowStatus.IN_PROGRESS
        self.started_at = datetime.now()
        
        if initial_context:
            self.context.update(initial_context)
        
        try:
            # Execute actions in dependency order
            executed_actions = set()
            
            while len(executed_actions) < len(self.actions):
                progress_made = False
                
                for action in self.actions:
                    if (action.action_id not in executed_actions and 
                        all(dep in executed_actions for dep in action.dependencies)):
                        
                        # Execute action
                        result = action.execute(self.context)
                        
                        # Store result in context for dependent actions
                        self.context[f"result_{action.action_id}"] = result
                        self.results[action.action_id] = result
                        
                        executed_actions.add(action.action_id)
                        progress_made = True
                
                if not progress_made:
                    raise Exception("Circular dependency or missing dependency in workflow")
            
            self.status = WorkflowStatus.COMPLETED
            self.completed_at = datetime.now()
            
            return self.results
        
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.completed_at = datetime.now()
            raise e


class GoalOrientedWorkflowManager:
    """
    Manages goal-oriented workflows based on user intent
    Translates high-level goals into executable action sequences
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, GoalOrientedWorkflow] = {}
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Available action functions (to be injected)
        self.action_functions = {}
    
    def register_action_function(self, name: str, function: Callable):
        """Register an action function for use in workflows"""
        self.action_functions[name] = function
    
    def create_workflow_for_intent(self, intent_analysis: Dict, user_context: Dict = None) -> str:
        """
        Create and return a workflow based on user intent analysis
        
        Args:
            intent_analysis: Results from intent inference engine
            user_context: Available context about user and system state
            
        Returns:
            Workflow ID for tracking execution
        """
        primary_intent = intent_analysis.get('primary_intent')
        emotional_context = intent_analysis.get('emotional_context', 'calm')
        action_plan = intent_analysis.get('action_plan', [])
        
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Create workflow based on intent
        workflow = self._create_workflow_from_intent(
            workflow_id, primary_intent, intent_analysis, user_context
        )
        
        # Customize workflow based on emotional context and action plan
        self._customize_workflow_for_context(workflow, emotional_context, action_plan, user_context)
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow and return results"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        return workflow.execute(initial_context or {})
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            return {'error': 'Workflow not found'}
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'status': workflow.status.value,
            'goal_description': workflow.goal_description,
            'user_intent': workflow.user_intent,
            'actions_total': len(workflow.actions),
            'actions_completed': len([a for a in workflow.actions if a.status == WorkflowStatus.COMPLETED]),
            'actions_failed': len([a for a in workflow.actions if a.status == WorkflowStatus.FAILED]),
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
        }
    
    def _create_workflow_from_intent(self, workflow_id: str, primary_intent: str, 
                                   intent_analysis: Dict, user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow based on primary intent"""
        
        if primary_intent == 'analyze_report':
            return self._create_analyze_report_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'compare_reports':
            return self._create_compare_reports_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'explain_parameter':
            return self._create_explain_parameter_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'health_advice':
            return self._create_health_advice_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'risk_assessment':
            return self._create_risk_assessment_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'trend_analysis':
            return self._create_trend_analysis_workflow(workflow_id, intent_analysis, user_context)
        
        elif primary_intent == 'clarification_needed':
            return self._create_clarification_workflow(workflow_id, intent_analysis, user_context)
        
        else:
            return self._create_general_workflow(workflow_id, intent_analysis, user_context)
    
    def _create_analyze_report_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                      user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for analyzing blood reports"""
        workflow = GoalOrientedWorkflow(
            workflow_id, 
            "Analyze blood report and provide comprehensive interpretation",
            "analyze_report"
        )
        
        # Check if reports are available
        if not user_context or user_context.get('report_count', 0) == 0:
            # No reports available - request upload
            workflow.add_action(WorkflowAction(
                "request_upload",
                ActionType.CLARIFICATION,
                "Request user to upload blood report",
                self.action_functions.get('request_report_upload', self._dummy_function),
                {'message': 'Please upload a blood report to analyze'}
            ))
            return workflow
        
        # Reports available - proceed with analysis
        workflow.add_action(WorkflowAction(
            "retrieve_reports",
            ActionType.DATA_RETRIEVAL,
            "Retrieve available blood reports",
            self.action_functions.get('get_user_reports', self._dummy_function)
        ))
        
        workflow.add_action(WorkflowAction(
            "analyze_parameters",
            ActionType.ANALYSIS,
            "Analyze individual parameters against reference ranges",
            self.action_functions.get('analyze_parameters', self._dummy_function),
            dependencies=["retrieve_reports"]
        ))
        
        workflow.add_action(WorkflowAction(
            "pattern_analysis",
            ActionType.ANALYSIS,
            "Perform pattern recognition and risk assessment",
            self.action_functions.get('pattern_analysis', self._dummy_function),
            dependencies=["analyze_parameters"]
        ))
        
        workflow.add_action(WorkflowAction(
            "generate_summary",
            ActionType.PRESENTATION,
            "Generate comprehensive report summary",
            self.action_functions.get('generate_report_summary', self._dummy_function),
            dependencies=["pattern_analysis"]
        ))
        
        return workflow
    
    def _create_compare_reports_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                       user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for comparing multiple reports"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Compare multiple blood reports and identify trends",
            "compare_reports"
        )
        
        # Check if multiple reports are available
        if not user_context or user_context.get('report_count', 0) < 2:
            workflow.add_action(WorkflowAction(
                "explain_requirements",
                ActionType.CLARIFICATION,
                "Explain that multiple reports are needed for comparison",
                self.action_functions.get('explain_comparison_requirements', self._dummy_function)
            ))
            return workflow
        
        # Multiple reports available
        workflow.add_action(WorkflowAction(
            "retrieve_reports",
            ActionType.DATA_RETRIEVAL,
            "Retrieve all available reports",
            self.action_functions.get('get_user_reports', self._dummy_function)
        ))
        
        workflow.add_action(WorkflowAction(
            "align_parameters",
            ActionType.VALIDATION,
            "Align parameters across reports for comparison",
            self.action_functions.get('align_report_parameters', self._dummy_function),
            dependencies=["retrieve_reports"]
        ))
        
        workflow.add_action(WorkflowAction(
            "calculate_changes",
            ActionType.COMPARISON,
            "Calculate parameter changes and trends",
            self.action_functions.get('calculate_parameter_changes', self._dummy_function),
            dependencies=["align_parameters"]
        ))
        
        workflow.add_action(WorkflowAction(
            "trend_analysis",
            ActionType.ANALYSIS,
            "Analyze trends and identify patterns",
            self.action_functions.get('analyze_trends', self._dummy_function),
            dependencies=["calculate_changes"]
        ))
        
        workflow.add_action(WorkflowAction(
            "generate_comparison",
            ActionType.PRESENTATION,
            "Generate comparative analysis report",
            self.action_functions.get('generate_comparison_report', self._dummy_function),
            dependencies=["trend_analysis"]
        ))
        
        return workflow
    
    def _create_explain_parameter_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                         user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for explaining specific parameters"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Explain specific blood parameters and their significance",
            "explain_parameter"
        )
        
        workflow.add_action(WorkflowAction(
            "identify_parameters",
            ActionType.VALIDATION,
            "Identify which parameters user is asking about",
            self.action_functions.get('identify_target_parameters', self._dummy_function),
            {'user_message': intent_analysis.get('original_message', '')}
        ))
        
        workflow.add_action(WorkflowAction(
            "retrieve_parameter_data",
            ActionType.DATA_RETRIEVAL,
            "Get parameter values from user reports",
            self.action_functions.get('get_parameter_values', self._dummy_function),
            dependencies=["identify_parameters"]
        ))
        
        workflow.add_action(WorkflowAction(
            "explain_parameters",
            ActionType.ANALYSIS,
            "Generate detailed parameter explanations",
            self.action_functions.get('explain_parameters', self._dummy_function),
            dependencies=["retrieve_parameter_data"]
        ))
        
        workflow.add_action(WorkflowAction(
            "provide_context",
            ActionType.PRESENTATION,
            "Provide medical context and significance",
            self.action_functions.get('provide_medical_context', self._dummy_function),
            dependencies=["explain_parameters"]
        ))
        
        return workflow
    
    def _create_health_advice_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                     user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for providing health advice"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Provide personalized health advice based on blood report findings",
            "health_advice"
        )
        
        workflow.add_action(WorkflowAction(
            "analyze_findings",
            ActionType.ANALYSIS,
            "Analyze current blood report findings",
            self.action_functions.get('analyze_current_findings', self._dummy_function)
        ))
        
        workflow.add_action(WorkflowAction(
            "identify_concerns",
            ActionType.ANALYSIS,
            "Identify areas of concern or improvement",
            self.action_functions.get('identify_health_concerns', self._dummy_function),
            dependencies=["analyze_findings"]
        ))
        
        workflow.add_action(WorkflowAction(
            "generate_recommendations",
            ActionType.RECOMMENDATION,
            "Generate personalized health recommendations",
            self.action_functions.get('generate_health_recommendations', self._dummy_function),
            dependencies=["identify_concerns"]
        ))
        
        workflow.add_action(WorkflowAction(
            "add_disclaimers",
            ActionType.VALIDATION,
            "Add appropriate medical disclaimers",
            self.action_functions.get('add_medical_disclaimers', self._dummy_function),
            dependencies=["generate_recommendations"]
        ))
        
        return workflow
    
    def _create_risk_assessment_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                       user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for risk assessment"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Assess health risks based on blood report parameters",
            "risk_assessment"
        )
        
        workflow.add_action(WorkflowAction(
            "calculate_risk_scores",
            ActionType.ANALYSIS,
            "Calculate various health risk scores",
            self.action_functions.get('calculate_risk_scores', self._dummy_function)
        ))
        
        workflow.add_action(WorkflowAction(
            "assess_patterns",
            ActionType.ANALYSIS,
            "Assess risk patterns and correlations",
            self.action_functions.get('assess_risk_patterns', self._dummy_function),
            dependencies=["calculate_risk_scores"]
        ))
        
        workflow.add_action(WorkflowAction(
            "contextualize_risks",
            ActionType.ANALYSIS,
            "Provide context for identified risks",
            self.action_functions.get('contextualize_risks', self._dummy_function),
            dependencies=["assess_patterns"]
        ))
        
        workflow.add_action(WorkflowAction(
            "present_risk_assessment",
            ActionType.PRESENTATION,
            "Present comprehensive risk assessment",
            self.action_functions.get('present_risk_assessment', self._dummy_function),
            dependencies=["contextualize_risks"]
        ))
        
        return workflow
    
    def _create_trend_analysis_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                      user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for trend analysis"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Analyze trends in blood parameters over time",
            "trend_analysis"
        )
        
        # Similar to compare_reports but focused on trends
        if not user_context or user_context.get('report_count', 0) < 2:
            workflow.add_action(WorkflowAction(
                "explain_trend_requirements",
                ActionType.CLARIFICATION,
                "Explain that multiple reports are needed for trend analysis",
                self.action_functions.get('explain_trend_requirements', self._dummy_function)
            ))
            return workflow
        
        workflow.add_action(WorkflowAction(
            "retrieve_historical_data",
            ActionType.DATA_RETRIEVAL,
            "Retrieve historical blood report data",
            self.action_functions.get('get_historical_reports', self._dummy_function)
        ))
        
        workflow.add_action(WorkflowAction(
            "calculate_trends",
            ActionType.ANALYSIS,
            "Calculate parameter trends over time",
            self.action_functions.get('calculate_parameter_trends', self._dummy_function),
            dependencies=["retrieve_historical_data"]
        ))
        
        workflow.add_action(WorkflowAction(
            "identify_patterns",
            ActionType.ANALYSIS,
            "Identify significant trend patterns",
            self.action_functions.get('identify_trend_patterns', self._dummy_function),
            dependencies=["calculate_trends"]
        ))
        
        workflow.add_action(WorkflowAction(
            "present_trends",
            ActionType.PRESENTATION,
            "Present trend analysis with insights",
            self.action_functions.get('present_trend_analysis', self._dummy_function),
            dependencies=["identify_patterns"]
        ))
        
        return workflow
    
    def _create_clarification_workflow(self, workflow_id: str, intent_analysis: Dict, 
                                     user_context: Dict) -> GoalOrientedWorkflow:
        """Create workflow for handling clarification needs"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Clarify user intent and gather necessary information",
            "clarification_needed"
        )
        
        workflow.add_action(WorkflowAction(
            "generate_questions",
            ActionType.CLARIFICATION,
            "Generate clarifying questions for user",
            self.action_functions.get('generate_clarifying_questions', self._dummy_function),
            {'intent_analysis': intent_analysis, 'user_context': user_context}
        ))
        
        workflow.add_action(WorkflowAction(
            "present_questions",
            ActionType.PRESENTATION,
            "Present questions to user in friendly manner",
            self.action_functions.get('present_clarifying_questions', self._dummy_function),
            dependencies=["generate_questions"]
        ))
        
        return workflow
    
    def _create_general_workflow(self, workflow_id: str, intent_analysis: Dict, 
                               user_context: Dict) -> GoalOrientedWorkflow:
        """Create general workflow for unclear intents"""
        workflow = GoalOrientedWorkflow(
            workflow_id,
            "Handle general medical report questions",
            "general_question"
        )
        
        workflow.add_action(WorkflowAction(
            "analyze_context",
            ActionType.ANALYSIS,
            "Analyze available context and user needs",
            self.action_functions.get('analyze_general_context', self._dummy_function),
            {'intent_analysis': intent_analysis, 'user_context': user_context}
        ))
        
        workflow.add_action(WorkflowAction(
            "provide_general_help",
            ActionType.PRESENTATION,
            "Provide general assistance and guidance",
            self.action_functions.get('provide_general_help', self._dummy_function),
            dependencies=["analyze_context"]
        ))
        
        return workflow
    
    def _customize_workflow_for_context(self, workflow: GoalOrientedWorkflow, 
                                      emotional_context: str, action_plan: List[Dict], 
                                      user_context: Dict):
        """Customize workflow based on emotional context and action plan"""
        
        # Add emotional support actions if user seems anxious
        if emotional_context in ['anxious', 'urgent']:
            # Insert reassurance action at the beginning
            reassurance_action = WorkflowAction(
                "provide_reassurance",
                ActionType.PRESENTATION,
                "Provide emotional support and reassurance",
                self.action_functions.get('provide_emotional_support', self._dummy_function),
                {'emotional_context': emotional_context}
            )
            workflow.actions.insert(0, reassurance_action)
        
        # Add medical disclaimer for risk-related workflows
        if workflow.user_intent in ['risk_assessment', 'health_advice']:
            disclaimer_action = WorkflowAction(
                "medical_disclaimer",
                ActionType.VALIDATION,
                "Provide medical disclaimer",
                self.action_functions.get('add_medical_disclaimer', self._dummy_function)
            )
            workflow.add_action(disclaimer_action)
        
        # Add export options if user might want to save results
        if workflow.user_intent in ['analyze_report', 'compare_reports', 'trend_analysis']:
            export_action = WorkflowAction(
                "offer_export",
                ActionType.EXPORT,
                "Offer to export results",
                self.action_functions.get('offer_export_options', self._dummy_function),
                dependencies=[workflow.actions[-1].action_id] if workflow.actions else []
            )
            workflow.add_action(export_action)
    
    def _initialize_workflow_templates(self) -> Dict[str, Any]:
        """Initialize workflow templates for common patterns"""
        return {
            'medical_analysis': {
                'steps': ['retrieve_data', 'analyze', 'interpret', 'present'],
                'required_context': ['user_reports'],
                'optional_context': ['user_demographics', 'medical_history']
            },
            'comparison_analysis': {
                'steps': ['retrieve_data', 'align_data', 'compare', 'analyze_trends', 'present'],
                'required_context': ['multiple_reports'],
                'optional_context': ['time_ranges', 'specific_parameters']
            }
        }
    
    def _dummy_function(self, **kwargs):
        """Dummy function for actions without registered implementations"""
        return f"Action executed with parameters: {kwargs}"


# Convenience function for easy integration
def create_goal_oriented_workflow(intent_analysis: Dict, user_context: Dict = None) -> str:
    """
    Create a goal-oriented workflow based on user intent
    
    Args:
        intent_analysis: Results from intent inference engine
        user_context: Available context about user and system state
        
    Returns:
        Workflow ID for tracking execution
    """
    manager = GoalOrientedWorkflowManager()
    return manager.create_workflow_for_intent(intent_analysis, user_context)