"""
Comprehensive Report Generator
Creates detailed medical analysis reports including all AI insights, risk assessments, and recommendations
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class ComprehensiveReportGenerator:
    """
    Generates comprehensive medical analysis reports that include:
    - Multi-model AI analysis results
    - Risk assessment scores and explanations
    - Personalized recommendations with traceability
    - Contextual insights based on user profile
    - Pattern recognition findings
    """
    
    def __init__(self):
        self.report_sections = [
            "executive_summary",
            "patient_context", 
            "parameter_analysis",
            "risk_assessment",
            "pattern_recognition",
            "personalized_recommendations",
            "contextual_insights",
            "completeness_report"
        ]
    
    def generate_comprehensive_report(self, 
                                    validated_data: Dict,
                                    ai_analysis: Dict,
                                    contextual_analysis: Dict,
                                    user_context: Dict,
                                    filename: str,
                                    format_type: str = "text") -> str:
        """
        Generate a comprehensive medical analysis report
        
        Args:
            validated_data: Basic parameter data with values and status
            ai_analysis: Multi-model AI analysis results
            contextual_analysis: Contextual analysis with personalization
            user_context: User demographic and medical history
            filename: Original filename for reference
            format_type: Output format (text, json)
            
        Returns:
            Formatted report string
        """
        
        if format_type.lower() == "json":
            return self._generate_json_report(validated_data, ai_analysis, contextual_analysis, user_context, filename)
        else:
            return self._generate_text_report(validated_data, ai_analysis, contextual_analysis, user_context, filename)
    
    def _generate_text_report(self, validated_data, ai_analysis, contextual_analysis, user_context, filename) -> str:
        """Generate comprehensive text format report"""
        
        report_lines = []
        
        # Header
        report_lines.extend([
            "=" * 80,
            "COMPREHENSIVE BLOOD REPORT ANALYSIS",
            "=" * 80,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source File: {filename}",
            f"Analysis Engine: Multi-Model AI System v2.0",
            "",
        ])
        
        # Executive Summary
        report_lines.extend(self._create_executive_summary(validated_data, ai_analysis, contextual_analysis))
        
        # Patient Context
        if user_context and any(user_context.values()):
            report_lines.extend(self._create_patient_context_section(user_context))
        
        # Parameter Analysis (Basic + Enhanced)
        report_lines.extend(self._create_parameter_analysis_section(validated_data, ai_analysis))
        
        # Risk Assessment
        if ai_analysis and 'model3_risk_assessment' in ai_analysis:
            report_lines.extend(self._create_risk_assessment_section(ai_analysis['model3_risk_assessment']))
        
        # Pattern Recognition
        if ai_analysis and 'correlations' in ai_analysis:
            report_lines.extend(self._create_pattern_recognition_section(ai_analysis))
        
        # Personalized Recommendations
        if ai_analysis and 'recommendations' in ai_analysis:
            report_lines.extend(self._create_recommendations_section(ai_analysis['recommendations']))
        
        # Contextual Insights
        if contextual_analysis:
            report_lines.extend(self._create_contextual_insights_section(contextual_analysis))
        
        # Completeness Report
        report_lines.extend(self._create_completeness_section(validated_data, ai_analysis, contextual_analysis, user_context))
        
        return "\n".join(report_lines)
    
    def _create_executive_summary(self, validated_data, ai_analysis, contextual_analysis) -> List[str]:
        """Create executive summary section"""
        lines = [
            "📋 EXECUTIVE SUMMARY",
            "=" * 50,
            ""
        ]
        
        # Overall health score
        if ai_analysis and 'model3_risk_assessment' in ai_analysis:
            model3 = ai_analysis['model3_risk_assessment']
            overall_score = model3.get('overall_health_score', 0)
            overall_status = model3.get('overall_status', 'Unknown')
            
            lines.extend([
                f"🎯 Overall Health Score: {overall_score}/100 ({overall_status})",
                ""
            ])
        
        # Critical findings
        abnormal_count = sum(1 for p in validated_data.values() if p.get('status') in ['LOW', 'HIGH'])
        total_count = len(validated_data)
        
        lines.extend([
            f"📊 Parameters Analyzed: {total_count}",
            f"⚠️  Abnormal Parameters: {abnormal_count}",
            f"✅ Normal Parameters: {total_count - abnormal_count}",
            ""
        ])
        
        # Key findings
        if abnormal_count > 0:
            lines.append("🔍 KEY FINDINGS:")
            for param, info in validated_data.items():
                if info.get('status') in ['LOW', 'HIGH']:
                    value = info.get('value', 'N/A')
                    unit = info.get('unit', '')
                    status = info.get('status', '')
                    lines.append(f"   • {param}: {value} {unit} ({status})")
            lines.append("")
        
        # Priority recommendations
        if ai_analysis and 'recommendations' in ai_analysis:
            high_priority = [r for r in ai_analysis['recommendations'] if r.get('priority') == 'High']
            if high_priority:
                lines.append("🎯 PRIORITY ACTIONS:")
                for rec in high_priority[:3]:  # Top 3 high priority
                    lines.append(f"   • {rec.get('category', 'General')}: {rec.get('actions', ['No actions'])[0]}")
                lines.append("")
        
        lines.append("")
        return lines
    
    def _create_patient_context_section(self, user_context) -> List[str]:
        """Create patient context section"""
        lines = [
            "👤 PATIENT CONTEXT",
            "=" * 50,
            ""
        ]
        
        age = user_context.get('age')
        gender = user_context.get('gender')
        medical_history = user_context.get('medical_history', [])
        lifestyle = user_context.get('lifestyle', {})
        
        if age:
            lines.append(f"Age: {age} years")
        if gender:
            lines.append(f"Gender: {gender}")
        
        if medical_history and len(medical_history) > 0:
            lines.append(f"Medical History: {', '.join(medical_history)}")
        
        if lifestyle:
            lifestyle_items = []
            if lifestyle.get('smoker'):
                lifestyle_items.append("Smoker")
            if lifestyle.get('alcohol') and lifestyle.get('alcohol') != 'None':
                lifestyle_items.append(f"Alcohol: {lifestyle.get('alcohol')}")
            if lifestyle.get('exercise'):
                lifestyle_items.append(f"Exercise: {lifestyle.get('exercise')}")
            if lifestyle_items:
                lines.append(f"Lifestyle: {', '.join(lifestyle_items)}")
        
        lines.extend(["", ""])
        return lines
    
    def _create_parameter_analysis_section(self, validated_data, ai_analysis) -> List[str]:
        """Create detailed parameter analysis section"""
        lines = [
            "🔬 PARAMETER ANALYSIS",
            "=" * 50,
            ""
        ]
        
        # Basic parameters table
        lines.append("📊 MEASURED PARAMETERS:")
        lines.append("-" * 60)
        lines.append(f"{'Parameter':<20} {'Value':<12} {'Unit':<8} {'Status':<10} {'Reference'}")
        lines.append("-" * 60)
        
        for param, info in validated_data.items():
            value = str(info.get('value', 'N/A'))
            unit = info.get('unit', '')
            status = info.get('status', 'UNKNOWN')
            ref_range = info.get('reference_range', 'N/A')
            
            # Status indicator
            status_icon = "⚠️" if status in ['LOW', 'HIGH'] else "✅"
            
            lines.append(f"{param:<20} {value:<12} {unit:<8} {status_icon} {status:<8} {ref_range}")
        
        lines.extend(["", ""])
        
        # Severity analysis if available
        if ai_analysis and 'model1_parameter_analysis' in ai_analysis:
            model1 = ai_analysis['model1_parameter_analysis']
            severity_data = model1.get('severity_analysis', [])
            
            if severity_data:
                lines.append("📈 SEVERITY ANALYSIS:")
                lines.append("-" * 50)
                for item in severity_data:
                    param = item.get('parameter', 'Unknown')
                    deviation = item.get('deviation', 0)
                    severity = item.get('severity', 'Unknown')
                    status = item.get('status', 'Unknown')
                    
                    severity_icon = "🔴" if severity == "Severe" else "🟡" if severity == "Moderate" else "🟢"
                    lines.append(f"{severity_icon} {param}: {deviation}% deviation ({severity} {status})")
                
                lines.extend(["", ""])
        
        return lines
    
    def _create_risk_assessment_section(self, risk_data) -> List[str]:
        """Create risk assessment section"""
        lines = [
            "⚠️ RISK ASSESSMENT",
            "=" * 50,
            ""
        ]
        
        # Individual risk scores
        risk_categories = ['anemia_risk', 'infection_risk', 'bleeding_risk']
        
        for risk_type in risk_categories:
            if risk_type in risk_data:
                risk_info = risk_data[risk_type]
                score = risk_info.get('score', 0)
                level = risk_info.get('level', 'Unknown')
                
                # Risk level icon
                risk_icon = "🔴" if level == "High" else "🟡" if level == "Moderate" else "🟢"
                
                risk_name = risk_type.replace('_risk', '').title()
                lines.append(f"{risk_icon} {risk_name} Risk: {score}/100 ({level})")
        
        # Overall health score
        overall_score = risk_data.get('overall_health_score', 0)
        overall_status = risk_data.get('overall_status', 'Unknown')
        
        lines.extend([
            "",
            f"🎯 Overall Health Score: {overall_score}/100 ({overall_status})",
            "",
            ""
        ])
        
        return lines
    
    def _create_pattern_recognition_section(self, ai_analysis) -> List[str]:
        """Create pattern recognition section"""
        lines = [
            "🔍 PATTERN RECOGNITION",
            "=" * 50,
            ""
        ]
        
        correlations = ai_analysis.get('correlations', [])
        conditions = ai_analysis.get('conditions', [])
        
        if correlations:
            lines.append("📊 IDENTIFIED PATTERNS:")
            for i, pattern in enumerate(correlations, 1):
                pattern_name = pattern.get('pattern', 'Unknown Pattern')
                parameters = pattern.get('parameters_involved', [])
                findings = pattern.get('findings', [])
                
                lines.append(f"{i}. {pattern_name}")
                if parameters:
                    lines.append(f"   Parameters: {', '.join(parameters)}")
                if findings:
                    for finding in findings:
                        lines.append(f"   • {finding}")
                lines.append("")
        
        if conditions:
            lines.append("🏥 POTENTIAL CONDITIONS:")
            for condition in conditions:
                condition_name = condition.get('condition', 'Unknown')
                likelihood = condition.get('likelihood', 'Unknown')
                evidence = condition.get('evidence', 'No evidence provided')
                
                likelihood_icon = "🔴" if likelihood == "High" else "🟡" if likelihood == "Moderate" else "🟢"
                lines.append(f"{likelihood_icon} {condition_name} ({likelihood} likelihood)")
                lines.append(f"   Evidence: {evidence}")
                lines.append("")
        
        if not correlations and not conditions:
            lines.append("✅ No significant patterns or conditions detected.")
            lines.append("")
        
        lines.append("")
        return lines
    
    def _create_recommendations_section(self, recommendations) -> List[str]:
        """Create personalized recommendations section"""
        lines = [
            "💡 PERSONALIZED RECOMMENDATIONS",
            "=" * 50,
            ""
        ]
        
        # Group by priority
        high_priority = [r for r in recommendations if r.get('priority') == 'High']
        medium_priority = [r for r in recommendations if r.get('priority') == 'Medium']
        low_priority = [r for r in recommendations if r.get('priority') == 'Low']
        
        for priority_group, priority_name, icon in [
            (high_priority, "HIGH PRIORITY", "🔴"),
            (medium_priority, "MEDIUM PRIORITY", "🟡"),
            (low_priority, "LOW PRIORITY", "🟢")
        ]:
            if priority_group:
                lines.append(f"{icon} {priority_name} RECOMMENDATIONS:")
                lines.append("-" * 40)
                
                for rec in priority_group:
                    category = rec.get('category', 'General')
                    actions = rec.get('actions', [])
                    traceability = rec.get('traceability', {})
                    
                    lines.append(f"📋 {category}:")
                    
                    # Show traceability if available
                    if traceability:
                        finding = traceability.get('finding', '')
                        reasoning = traceability.get('reasoning', '')
                        if finding:
                            lines.append(f"   🔍 Finding: {finding}")
                        if reasoning:
                            lines.append(f"   💭 Why: {reasoning}")
                    
                    # Show actions
                    if actions:
                        lines.append("   📝 Actions:")
                        for action in actions:
                            lines.append(f"      • {action}")
                    
                    lines.append("")
                
                lines.append("")
        
        return lines
    
    def _create_contextual_insights_section(self, contextual_analysis) -> List[str]:
        """Create contextual insights section"""
        lines = [
            "🧑 CONTEXTUAL INSIGHTS",
            "=" * 50,
            ""
        ]
        
        # Age/Gender considerations
        age_gender_considerations = contextual_analysis.get('age_gender_considerations', [])
        if age_gender_considerations:
            lines.append("👥 AGE & GENDER CONSIDERATIONS:")
            for consideration in age_gender_considerations:
                lines.append(f"   • {consideration}")
            lines.append("")
        
        # Personalized insights
        personalized_insights = contextual_analysis.get('personalized_insights', [])
        if personalized_insights:
            lines.append("🎯 PERSONALIZED INSIGHTS:")
            for insight in personalized_insights:
                lines.append(f"   • {insight}")
            lines.append("")
        
        # Lifestyle impact
        lifestyle_impact = contextual_analysis.get('lifestyle_impact', [])
        if lifestyle_impact:
            lines.append("🏃 LIFESTYLE IMPACT:")
            for impact in lifestyle_impact:
                lines.append(f"   • {impact}")
            lines.append("")
        
        # Context-specific recommendations
        context_recommendations = contextual_analysis.get('recommendations', [])
        if context_recommendations:
            lines.append("💊 CONTEXT-SPECIFIC RECOMMENDATIONS:")
            for rec in context_recommendations:
                category = rec.get('category', 'General')
                actions = rec.get('actions', [])
                lines.append(f"   📋 {category}:")
                for action in actions:
                    lines.append(f"      • {action}")
            lines.append("")
        
        return lines
    
    def _create_completeness_section(self, validated_data, ai_analysis, contextual_analysis, user_context) -> List[str]:
        """Create completeness and limitations section"""
        lines = [
            "📊 REPORT COMPLETENESS",
            "=" * 50,
            ""
        ]
        
        # Calculate completeness
        sections_available = 0
        total_sections = 6  # Basic sections
        
        if validated_data:
            sections_available += 1
        if ai_analysis:
            sections_available += 1
        if contextual_analysis:
            sections_available += 1
        if user_context and any(user_context.values()):
            sections_available += 1
        
        completeness_percentage = (sections_available / total_sections) * 100
        
        lines.extend([
            f"✅ Analysis Completeness: {completeness_percentage:.1f}%",
            f"📊 Sections Included: {sections_available}/{total_sections}",
            ""
        ])
        
        # List what's included
        lines.append("📋 INCLUDED ANALYSIS:")
        if validated_data:
            lines.append("   ✅ Parameter Analysis")
        if ai_analysis:
            lines.append("   ✅ Multi-Model AI Analysis")
            lines.append("   ✅ Risk Assessment")
            lines.append("   ✅ Pattern Recognition")
        if contextual_analysis:
            lines.append("   ✅ Contextual Analysis")
        if user_context and any(user_context.values()):
            lines.append("   ✅ Personalized Insights")
        
        # List limitations
        limitations = []
        if not user_context or not any(user_context.values()):
            limitations.append("Limited personalization due to missing user context")
        if not ai_analysis:
            limitations.append("AI analysis not available")
        if not contextual_analysis:
            limitations.append("Contextual analysis not available")
        
        if limitations:
            lines.extend(["", "⚠️ LIMITATIONS:"])
            for limitation in limitations:
                lines.append(f"   • {limitation}")
        
        lines.extend([
            "",
            "=" * 80,
            "END OF COMPREHENSIVE ANALYSIS REPORT",
            "=" * 80,
            "",
            "⚠️ MEDICAL DISCLAIMER:",
            "This report is for informational purposes only and should not replace",
            "professional medical advice. Always consult with healthcare professionals",
            "for medical decisions and interpretations.",
            ""
        ])
        
        return lines
    
    def _generate_json_report(self, validated_data, ai_analysis, contextual_analysis, user_context, filename) -> str:
        """Generate comprehensive JSON format report"""
        
        report_data = {
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "source_file": filename,
                "analysis_engine": "Multi-Model AI System v2.0",
                "report_version": "1.0"
            },
            "patient_context": user_context if user_context else {},
            "parameters": validated_data,
            "ai_analysis": ai_analysis if ai_analysis else {},
            "contextual_analysis": contextual_analysis if contextual_analysis else {},
            "completeness": {
                "sections_available": sum([
                    1 if validated_data else 0,
                    1 if ai_analysis else 0,
                    1 if contextual_analysis else 0,
                    1 if user_context and any(user_context.values()) else 0
                ]),
                "total_sections": 4,
                "percentage": 0  # Will be calculated
            }
        }
        
        # Calculate completeness percentage
        report_data["completeness"]["percentage"] = (
            report_data["completeness"]["sections_available"] / 
            report_data["completeness"]["total_sections"]
        ) * 100
        
        return json.dumps(report_data, indent=2, default=str)


# Factory function for easy import
def create_comprehensive_report_generator():
    """Factory function to create a comprehensive report generator"""
    return ComprehensiveReportGenerator()