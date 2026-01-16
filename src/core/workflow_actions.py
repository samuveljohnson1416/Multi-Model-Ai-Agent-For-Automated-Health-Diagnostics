"""
Workflow Action Functions
Implementation of all action functions used by the Goal-Oriented Workflow Manager
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class WorkflowActions:
    """
    Collection of action functions that can be executed by workflows
    """
    
    def __init__(self, context_manager=None):
        self.context_manager = context_manager
        self.current_report_data = {}  # Store current report data
    
    def set_report_data(self, report_data: Dict[str, Any]):
        """Set current report data for analysis"""
        self.current_report_data = report_data
    
    # Data Retrieval Actions
    def get_user_reports(self, **kwargs) -> Dict[str, Any]:
        """Get user's available reports"""
        if self.current_report_data:
            return {
                'status': 'success',
                'reports': {'current': self.current_report_data},
                'analysis_results': {'current': self.current_report_data},
                'report_count': 1
            }
        return {
            'status': 'no_reports',
            'message': 'No reports available. Please upload a blood report to begin analysis.',
            'reports': {},
            'report_count': 0
        }
    
    def get_historical_reports(self, **kwargs) -> Dict[str, Any]:
        """Get historical blood report data"""
        reports = self.get_user_reports(**kwargs)
        
        if reports['report_count'] > 1:
            return {
                'status': 'success',
                'historical_data': reports['reports'],
                'timeline': self._extract_report_timeline(reports['reports'])
            }
        
        return {
            'status': 'insufficient_data',
            'message': 'Multiple reports needed for historical analysis',
            'available_reports': reports['report_count']
        }
    
    def get_parameter_values(self, target_parameters=None, **kwargs) -> Dict[str, Any]:
        """Get parameter values from user reports"""
        reports = self.get_user_reports(**kwargs)
        
        if reports['report_count'] == 0:
            return {'status': 'no_data', 'message': 'No reports available'}
        
        parameter_data = {}
        
        for report_id, analysis_data in reports.get('analysis_results', {}).items():
            validated_data = analysis_data.get('validated_data', {})
            
            for param_name, param_info in validated_data.items():
                if not target_parameters or param_name in target_parameters:
                    if param_name not in parameter_data:
                        parameter_data[param_name] = []
                    
                    parameter_data[param_name].append({
                        'report_id': report_id,
                        'value': param_info.get('value'),
                        'unit': param_info.get('unit'),
                        'status': param_info.get('status'),
                        'reference_range': param_info.get('reference_range')
                    })
        
        return {
            'status': 'success',
            'parameter_data': parameter_data,
            'parameters_found': len(parameter_data)
        }
    
    # Analysis Actions
    def analyze_parameters(self, **kwargs) -> Dict[str, Any]:
        """Analyze individual parameters against reference ranges"""
        reports_data = kwargs.get('result_retrieve_reports', self.get_user_reports(**kwargs))
        
        if reports_data.get('report_count', 0) == 0:
            return {'status': 'no_data', 'message': 'No reports to analyze'}
        
        analysis_summary = {
            'total_parameters': 0,
            'normal_parameters': 0,
            'abnormal_parameters': 0,
            'abnormal_details': []
        }
        
        for report_id, analysis_data in reports_data.get('analysis_results', {}).items():
            validated_data = analysis_data.get('validated_data', {})
            
            for param_name, param_info in validated_data.items():
                analysis_summary['total_parameters'] += 1
                
                status = param_info.get('status', 'UNKNOWN')
                if status == 'NORMAL':
                    analysis_summary['normal_parameters'] += 1
                elif status in ['HIGH', 'LOW']:
                    analysis_summary['abnormal_parameters'] += 1
                    analysis_summary['abnormal_details'].append({
                        'parameter': param_name,
                        'value': param_info.get('value'),
                        'status': status,
                        'reference': param_info.get('reference_range'),
                        'report_id': report_id
                    })
        
        return {
            'status': 'success',
            'analysis_summary': analysis_summary,
            'recommendation': self._generate_parameter_recommendations(analysis_summary)
        }
    
    def pattern_analysis(self, **kwargs) -> Dict[str, Any]:
        """Perform pattern recognition and risk assessment"""
        parameter_analysis = kwargs.get('result_analyze_parameters', self.analyze_parameters(**kwargs))
        
        if parameter_analysis.get('status') != 'success':
            return parameter_analysis
        
        abnormal_details = parameter_analysis['analysis_summary']['abnormal_details']
        
        # Identify patterns
        patterns = self._identify_health_patterns(abnormal_details)
        
        # Calculate risk scores
        risk_scores = self._calculate_risk_scores(abnormal_details)
        
        return {
            'status': 'success',
            'patterns_identified': patterns,
            'risk_assessment': risk_scores,
            'pattern_count': len(patterns)
        }
    
    def analyze_current_findings(self, **kwargs) -> Dict[str, Any]:
        """Analyze current blood report findings"""
        return self.analyze_parameters(**kwargs)
    
    def identify_health_concerns(self, findings_data=None, **kwargs) -> Dict[str, Any]:
        """Identify areas of concern or improvement"""
        if not findings_data:
            findings_data = kwargs.get('result_analyze_findings', self.analyze_current_findings(**kwargs))
        
        if findings_data.get('status') != 'success':
            return findings_data
        
        concerns = []
        improvements = []
        
        abnormal_details = findings_data.get('analysis_summary', {}).get('abnormal_details', [])
        
        for detail in abnormal_details:
            param = detail['parameter'].lower()
            status = detail['status']
            
            if 'cholesterol' in param and status == 'HIGH':
                concerns.append({
                    'area': 'Cardiovascular Health',
                    'parameter': detail['parameter'],
                    'concern': 'Elevated cholesterol may increase heart disease risk',
                    'priority': 'medium'
                })
            
            elif 'glucose' in param and status == 'HIGH':
                concerns.append({
                    'area': 'Metabolic Health',
                    'parameter': detail['parameter'],
                    'concern': 'High blood sugar may indicate diabetes risk',
                    'priority': 'high'
                })
            
            elif 'hemoglobin' in param and status == 'LOW':
                concerns.append({
                    'area': 'Blood Health',
                    'parameter': detail['parameter'],
                    'concern': 'Low hemoglobin may indicate anemia',
                    'priority': 'medium'
                })
        
        return {
            'status': 'success',
            'health_concerns': concerns,
            'improvement_areas': improvements,
            'priority_concerns': [c for c in concerns if c['priority'] == 'high']
        }
    
    # Recommendation Actions
    def generate_health_recommendations(self, concerns_data=None, **kwargs) -> Dict[str, Any]:
        """Generate personalized health recommendations"""
        if not concerns_data:
            concerns_data = kwargs.get('result_identify_concerns', self.identify_health_concerns(**kwargs))
        
        if concerns_data.get('status') != 'success':
            return concerns_data
        
        recommendations = {
            'dietary': [],
            'lifestyle': [],
            'monitoring': [],
            'medical': []
        }
        
        concerns = concerns_data.get('health_concerns', [])
        
        for concern in concerns:
            area = concern.get('area', '').lower()
            parameter = concern.get('parameter', '').lower()
            
            if 'cardiovascular' in area or 'cholesterol' in parameter:
                recommendations['dietary'].extend([
                    'Reduce saturated fat intake',
                    'Increase omega-3 rich foods (fish, walnuts)',
                    'Add more fiber-rich foods (oats, beans, fruits)'
                ])
                recommendations['lifestyle'].extend([
                    'Regular aerobic exercise (30 min, 5 days/week)',
                    'Maintain healthy weight',
                    'Quit smoking if applicable'
                ])
            
            elif 'metabolic' in area or 'glucose' in parameter:
                recommendations['dietary'].extend([
                    'Choose complex carbohydrates over simple sugars',
                    'Control portion sizes',
                    'Eat regular, balanced meals'
                ])
                recommendations['lifestyle'].extend([
                    'Regular physical activity',
                    'Maintain healthy weight',
                    'Manage stress levels'
                ])
            
            elif 'blood' in area or 'hemoglobin' in parameter:
                recommendations['dietary'].extend([
                    'Include iron-rich foods (lean meat, spinach, beans)',
                    'Combine iron foods with vitamin C sources',
                    'Consider B12 and folate rich foods'
                ])
        
        # Remove duplicates
        for category in recommendations:
            recommendations[category] = list(set(recommendations[category]))
        
        # Add general monitoring recommendations
        recommendations['monitoring'] = [
            'Regular follow-up blood tests as advised by doctor',
            'Track symptoms and changes',
            'Monitor blood pressure if relevant'
        ]
        
        recommendations['medical'] = [
            'Discuss results with healthcare provider',
            'Follow prescribed treatment plans',
            'Ask about additional testing if needed'
        ]
        
        return {
            'status': 'success',
            'recommendations': recommendations,
            'total_recommendations': sum(len(recs) for recs in recommendations.values())
        }
    
    # Comparison Actions
    def align_report_parameters(self, **kwargs) -> Dict[str, Any]:
        """Align parameters across reports for comparison"""
        reports_data = kwargs.get('result_retrieve_reports', self.get_user_reports(**kwargs))
        
        if reports_data.get('report_count', 0) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'At least 2 reports needed for comparison'
            }
        
        # Find common parameters across all reports
        all_parameters = set()
        report_parameters = {}
        
        for report_id, analysis_data in reports_data.get('analysis_results', {}).items():
            validated_data = analysis_data.get('validated_data', {})
            params = set(validated_data.keys())
            all_parameters.update(params)
            report_parameters[report_id] = params
        
        # Find parameters common to all reports
        common_parameters = all_parameters.copy()
        for params in report_parameters.values():
            common_parameters = common_parameters.intersection(params)
        
        return {
            'status': 'success',
            'common_parameters': list(common_parameters),
            'all_parameters': list(all_parameters),
            'alignment_ready': len(common_parameters) > 0
        }
    
    def calculate_parameter_changes(self, alignment_data=None, **kwargs) -> Dict[str, Any]:
        """Calculate parameter changes and trends"""
        if not alignment_data:
            alignment_data = kwargs.get('result_align_parameters', self.align_report_parameters(**kwargs))
        
        if alignment_data.get('status') != 'success':
            return alignment_data
        
        reports_data = self.get_user_reports(**kwargs)
        common_parameters = alignment_data.get('common_parameters', [])
        
        changes = {}
        
        # Get sorted report IDs (assuming chronological order)
        report_ids = sorted(reports_data.get('analysis_results', {}).keys())
        
        for param in common_parameters:
            param_changes = []
            values = []
            
            for report_id in report_ids:
                analysis_data = reports_data['analysis_results'][report_id]
                validated_data = analysis_data.get('validated_data', {})
                
                if param in validated_data:
                    param_info = validated_data[param]
                    try:
                        value = float(param_info.get('value', 0))
                        values.append({
                            'report_id': report_id,
                            'value': value,
                            'unit': param_info.get('unit', ''),
                            'status': param_info.get('status', 'UNKNOWN')
                        })
                    except (ValueError, TypeError):
                        continue
            
            # Calculate changes between consecutive reports
            for i in range(1, len(values)):
                prev_val = values[i-1]['value']
                curr_val = values[i]['value']
                
                if prev_val != 0:
                    percent_change = ((curr_val - prev_val) / prev_val) * 100
                else:
                    percent_change = 0
                
                change_type = 'stable'
                if percent_change > 5:
                    change_type = 'increase'
                elif percent_change < -5:
                    change_type = 'decrease'
                
                param_changes.append({
                    'from_report': values[i-1]['report_id'],
                    'to_report': values[i]['report_id'],
                    'from_value': prev_val,
                    'to_value': curr_val,
                    'absolute_change': curr_val - prev_val,
                    'percent_change': round(percent_change, 2),
                    'change_type': change_type
                })
            
            if param_changes:
                changes[param] = {
                    'parameter_name': param,
                    'values': values,
                    'changes': param_changes,
                    'overall_trend': self._determine_trend(param_changes)
                }
        
        return {
            'status': 'success',
            'parameter_changes': changes,
            'parameters_analyzed': len(changes)
        }
    
    # Presentation Actions
    def generate_report_summary(self, **kwargs) -> str:
        """Generate comprehensive report summary"""
        analysis_data = kwargs.get('result_pattern_analysis', self.pattern_analysis(**kwargs))
        
        if analysis_data.get('status') != 'success':
            return "Unable to generate summary - analysis data not available."
        
        summary_parts = []
        
        # Basic analysis summary
        if 'result_analyze_parameters' in kwargs:
            param_analysis = kwargs['result_analyze_parameters']
            summary = param_analysis.get('analysis_summary', {})
            
            total = summary.get('total_parameters', 0)
            normal = summary.get('normal_parameters', 0)
            abnormal = summary.get('abnormal_parameters', 0)
            
            summary_parts.append(f"📊 **Analysis Complete**: {total} parameters analyzed")
            summary_parts.append(f"✅ **Normal**: {normal} parameters")
            
            if abnormal > 0:
                summary_parts.append(f"⚠️ **Abnormal**: {abnormal} parameters require attention")
        
        # Pattern analysis
        patterns = analysis_data.get('patterns_identified', [])
        if patterns:
            summary_parts.append(f"🔍 **Patterns Identified**: {len(patterns)} health patterns detected")
        
        # Risk assessment
        risk_assessment = analysis_data.get('risk_assessment', {})
        if risk_assessment:
            summary_parts.append("🎯 **Risk Assessment**: Completed with personalized insights")
        
        summary_parts.append("\n💡 **Next Steps**: Review detailed findings and consider discussing results with your healthcare provider.")
        
        return "\n".join(summary_parts)
    
    def generate_comparison_report(self, **kwargs) -> str:
        """Generate comparative analysis report"""
        changes_data = kwargs.get('result_trend_analysis', self.calculate_parameter_changes(**kwargs))
        
        if changes_data.get('status') != 'success':
            return "Unable to generate comparison - insufficient data for analysis."
        
        parameter_changes = changes_data.get('parameter_changes', {})
        
        if not parameter_changes:
            return "No comparable parameters found between reports."
        
        report_parts = []
        report_parts.append("📊 **Comparative Analysis Results**\n")
        
        improving = []
        worsening = []
        stable = []
        
        for param_name, param_data in parameter_changes.items():
            trend = param_data.get('overall_trend', 'stable')
            
            if trend == 'improving':
                improving.append(param_name)
            elif trend == 'worsening':
                worsening.append(param_name)
            else:
                stable.append(param_name)
        
        if improving:
            report_parts.append(f"📈 **Improving Parameters**: {', '.join(improving)}")
        
        if worsening:
            report_parts.append(f"📉 **Parameters Needing Attention**: {', '.join(worsening)}")
        
        if stable:
            report_parts.append(f"➡️ **Stable Parameters**: {', '.join(stable)}")
        
        report_parts.append(f"\n🔍 **Total Parameters Compared**: {len(parameter_changes)}")
        report_parts.append("\n💡 **Recommendation**: Focus on parameters showing concerning trends and maintain healthy habits for stable values.")
        
        return "\n".join(report_parts)
    
    # Clarification Actions
    def request_report_upload(self, message="", **kwargs) -> str:
        """Request user to upload blood report"""
        base_message = "To provide personalized analysis, please upload your blood report."
        
        if message:
            return f"{message}\n\n{base_message}"
        
        return f"{base_message}\n\nSupported formats: PDF, PNG, JPG, JPEG, JSON, CSV"
    
    def explain_comparison_requirements(self, **kwargs) -> str:
        """Explain requirements for comparison"""
        current_reports = self.get_user_reports(**kwargs).get('report_count', 0)
        
        if current_reports == 0:
            return "To compare blood reports, I need at least two reports from different dates. Please upload your blood reports first."
        elif current_reports == 1:
            return f"I can see you have {current_reports} report uploaded. To perform a comparison, please upload at least one more blood report from a different date."
        else:
            return "You have sufficient reports for comparison analysis."
    
    def explain_trend_requirements(self, **kwargs) -> str:
        """Explain requirements for trend analysis"""
        return self.explain_comparison_requirements(**kwargs).replace("comparison", "trend analysis")
    
    # Support Actions
    def provide_emotional_support(self, emotional_context="calm", **kwargs) -> str:
        """Provide emotional support based on context"""
        if emotional_context == 'anxious':
            return "I understand that blood test results can be concerning. Remember that I'm here to help you understand your results clearly, and it's always best to discuss any concerns with your healthcare provider who knows your complete medical history."
        
        elif emotional_context == 'urgent':
            return "I can see this is important to you. Let me help you understand your results step by step. For any urgent medical concerns, please contact your healthcare provider directly."
        
        elif emotional_context == 'confused':
            return "Medical reports can be complex, and it's completely normal to have questions. I'm here to break down the information in a way that's easy to understand."
        
        return "I'm here to help you understand your blood test results clearly and thoroughly."
    
    def add_medical_disclaimer(self, **kwargs) -> str:
        """Add medical disclaimer"""
        return "⚠️ **Important Medical Disclaimer**: This analysis is for informational purposes only and should not replace professional medical advice. Please consult with your healthcare provider for medical decisions and treatment recommendations."
    
    def offer_export_options(self, **kwargs) -> str:
        """Offer to export results"""
        return "📄 **Export Options Available**: You can download your analysis results as a text report or CSV file using the download buttons in the interface."
    
    # Helper Methods
    def _extract_report_timeline(self, reports: Dict) -> List[Dict]:
        """Extract timeline from reports"""
        timeline = []
        for report_id, report_data in reports.items():
            metadata = report_data.get('metadata', {})
            timeline.append({
                'report_id': report_id,
                'date': metadata.get('test_date', 'Unknown'),
                'patient_name': metadata.get('patient_name', 'Unknown')
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def _generate_parameter_recommendations(self, analysis_summary: Dict) -> str:
        """Generate recommendations based on parameter analysis"""
        abnormal_count = analysis_summary.get('abnormal_parameters', 0)
        
        if abnormal_count == 0:
            return "All parameters are within normal ranges. Continue maintaining healthy lifestyle habits."
        elif abnormal_count <= 2:
            return "A few parameters need attention. Focus on targeted lifestyle improvements and follow up with your healthcare provider."
        else:
            return "Multiple parameters are outside normal ranges. It's important to discuss these results with your healthcare provider for comprehensive evaluation."
    
    def _identify_health_patterns(self, abnormal_details: List[Dict]) -> List[Dict]:
        """Identify health patterns from abnormal parameters"""
        patterns = []
        
        # Group parameters by health area
        cardiovascular_params = []
        metabolic_params = []
        blood_health_params = []
        
        for detail in abnormal_details:
            param_name = detail['parameter'].lower()
            
            if any(term in param_name for term in ['cholesterol', 'ldl', 'hdl', 'triglyceride']):
                cardiovascular_params.append(detail)
            elif any(term in param_name for term in ['glucose', 'hba1c', 'insulin']):
                metabolic_params.append(detail)
            elif any(term in param_name for term in ['hemoglobin', 'rbc', 'wbc', 'platelet']):
                blood_health_params.append(detail)
        
        if len(cardiovascular_params) >= 2:
            patterns.append({
                'pattern_type': 'cardiovascular_risk',
                'description': 'Multiple cardiovascular parameters are abnormal',
                'affected_parameters': [p['parameter'] for p in cardiovascular_params],
                'severity': 'moderate' if len(cardiovascular_params) == 2 else 'high'
            })
        
        if len(metabolic_params) >= 1:
            patterns.append({
                'pattern_type': 'metabolic_concern',
                'description': 'Metabolic parameters indicate potential issues',
                'affected_parameters': [p['parameter'] for p in metabolic_params],
                'severity': 'moderate'
            })
        
        return patterns
    
    def _calculate_risk_scores(self, abnormal_details: List[Dict]) -> Dict[str, Any]:
        """Calculate basic risk scores"""
        risk_factors = {
            'cardiovascular': 0,
            'metabolic': 0,
            'overall': 0
        }
        
        for detail in abnormal_details:
            param_name = detail['parameter'].lower()
            
            if 'cholesterol' in param_name and detail['status'] == 'HIGH':
                risk_factors['cardiovascular'] += 1
            elif 'glucose' in param_name and detail['status'] == 'HIGH':
                risk_factors['metabolic'] += 1
        
        # Calculate overall risk
        total_abnormal = len(abnormal_details)
        if total_abnormal == 0:
            risk_level = 'low'
        elif total_abnormal <= 2:
            risk_level = 'moderate'
        else:
            risk_level = 'elevated'
        
        return {
            'risk_factors': risk_factors,
            'overall_risk_level': risk_level,
            'total_abnormal_parameters': total_abnormal
        }
    
    def _determine_trend(self, changes: List[Dict]) -> str:
        """Determine overall trend from parameter changes"""
        if not changes:
            return 'stable'
        
        increases = sum(1 for c in changes if c['change_type'] == 'increase')
        decreases = sum(1 for c in changes if c['change_type'] == 'decrease')
        
        if increases > decreases:
            return 'increasing'
        elif decreases > increases:
            return 'decreasing'
        else:
            return 'stable'


# Convenience function to create workflow actions
def create_workflow_actions(context_manager=None) -> WorkflowActions:
    """Create workflow actions instance"""
    return WorkflowActions(context_manager)