# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bonus Features for DQ Management System.

Implements:
1. Time Travel Diff View - Side-by-side comparison before/after fixes
2. Agent Debate Mode - Live logs of agent reasoning and collaboration
3. Root Cause Clustering - Group similar issues by metadata
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re


class TimeTravelDiff:
    """Generate side-by-side diff views for data quality fixes."""
    
    @staticmethod
    def generate_diff(
        original_df: pd.DataFrame,
        fixed_df: pd.DataFrame,
        confidence_scores: Dict[str, float] = None
    ) -> pd.DataFrame:
        """Generate a diff DataFrame showing before/after comparison.
        
        Args:
            original_df: Original data with issues
            fixed_df: Fixed data after remediation
            confidence_scores: Optional confidence scores for each fix
            
        Returns:
            DataFrame with columns: Row, Column, Original, Fixed, Status, Confidence
        """
        diff_records = []
        
        # Ensure same index
        if not original_df.index.equals(fixed_df.index):
            fixed_df = fixed_df.reindex(original_df.index)
        
        # Compare each cell
        for idx in original_df.index:
            for col in original_df.columns:
                orig_val = original_df.loc[idx, col]
                fixed_val = fixed_df.loc[idx, col]
                
                # Check if values differ
                if pd.isna(orig_val) and pd.isna(fixed_val):
                    continue  # Both NaN, no change
                elif orig_val != fixed_val:
                    confidence = confidence_scores.get(f"{idx}_{col}", 0.0) if confidence_scores else 0.0
                    
                    diff_records.append({
                        "Row": idx,
                        "Column": col,
                        "Original": str(orig_val),
                        "Fixed": str(fixed_val),
                        "Status": "Modified",
                        "Confidence": f"{confidence*100:.1f}%"
                    })
        
        return pd.DataFrame(diff_records)
    
    @staticmethod
    def format_for_display(diff_df: pd.DataFrame) -> str:
        """Format diff DataFrame as markdown table for Streamlit.
        
        Args:
            diff_df: Diff DataFrame from generate_diff
            
        Returns:
            Markdown formatted table
        """
        if diff_df.empty:
            return "✅ No changes detected"
        
        # Add color indicators
        diff_df["Original"] = diff_df["Original"].apply(lambda x: f"🔴 {x}")
        diff_df["Fixed"] = diff_df["Fixed"].apply(lambda x: f"🟢 {x}")
        
        return diff_df.to_markdown(index=False)


class AgentDebateLogger:
    """Log and display agent reasoning for transparency."""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
    
    def log_agent_thought(
        self,
        agent_name: str,
        thought: str,
        action: str = None,
        result: str = None
    ):
        """Log a single agent thought/action.
        
        Args:
            agent_name: Name of the agent (Identifier, Treatment, etc.)
            thought: The agent's reasoning
            action: Action taken (optional)
            result: Result of action (optional)
        """
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": agent_name,
            "thought": thought,
            "action": action,
            "result": result
        }
        self.logs.append(entry)
    
    def log_agent_debate(
        self,
        agent1: str,
        statement1: str,
        agent2: str,
        statement2: str,
        resolution: str = None
    ):
        """Log a debate/disagreement between agents.
        
        Args:
            agent1: First agent name
            statement1: First agent's position
            agent2: Second agent name
            statement2: Second agent's position
            resolution: How the conflict was resolved
        """
        debate = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": "debate",
            "participants": [agent1, agent2],
            "statements": {
                agent1: statement1,
                agent2: statement2
            },
            "resolution": resolution
        }
        self.logs.append(debate)
    
    def get_formatted_logs(self) -> str:
        """Get formatted logs as markdown.
        
        Returns:
            Markdown formatted log entries
        """
        if not self.logs:
            return "No agent activity logged yet."
        
        output = "## 🤖 Agent Thought Process\n\n"
        
        for entry in self.logs:
            if entry.get("type") == "debate":
                output += f"### 💬 Agent Debate ({entry['timestamp']})\n"
                output += f"**{entry['participants'][0]}:** {entry['statements'][entry['participants'][0]]}\n\n"
                output += f"**{entry['participants'][1]}:** {entry['statements'][entry['participants'][1]]}\n\n"
                if entry.get("resolution"):
                    output += f"**Resolution:** {entry['resolution']}\n\n"
            else:
                output += f"### {entry['agent']} ({entry['timestamp']})\n"
                output += f"**Thought:** {entry['thought']}\n\n"
                if entry.get("action"):
                    output += f"**Action:** {entry['action']}\n\n"
                if entry.get("result"):
                    output += f"**Result:** {entry['result']}\n\n"
            
            output += "---\n\n"
        
        return output
    
    def clear(self):
        """Clear all logs."""
        self.logs = []


class RootCauseClusterer:
    """Analyze and cluster DQ issues by root cause."""
    
    @staticmethod
    def analyze_metadata(
        issues_df: pd.DataFrame,
        metadata_columns: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze issue metadata to find common root causes.
        
        Args:
            issues_df: DataFrame containing issues with metadata
            metadata_columns: Columns to analyze (created_by, source_system, etc.)
            
        Returns:
            Dictionary with root cause analysis
        """
        if metadata_columns is None:
            metadata_columns = [col for col in issues_df.columns 
                              if col not in ['policy_id', 'error_description', 'severity']]
        
        analysis = {
            "total_issues": len(issues_df),
            "clusters": [],
            "top_root_causes": []
        }
        
        # Analyze each metadata column
        for col in metadata_columns:
            if col in issues_df.columns:
                value_counts = issues_df[col].value_counts()
                
                if len(value_counts) > 0:
                    most_common = value_counts.iloc[0]
                    most_common_value = value_counts.index[0]
                    percentage = (most_common / len(issues_df)) * 100
                    
                    if percentage > 50:  # Significant clustering
                        analysis["top_root_causes"].append({
                            "attribute": col,
                            "value": most_common_value,
                            "affected_issues": int(most_common),
                            "percentage": f"{percentage:.1f}%"
                        })
        
        # Group by combinations
        if len(metadata_columns) >= 2:
            grouped = issues_df.groupby(metadata_columns[:2]).size().reset_index(name='count')
            grouped = grouped.sort_values('count', ascending=False).head(5)
            
            for _, row in grouped.iterrows():
                cluster = {
                    "attributes": {},
                    "count": int(row['count'])
                }
                for col in metadata_columns[:2]:
                    cluster["attributes"][col] = row[col]
                analysis["clusters"].append(cluster)
        
        return analysis
    
    @staticmethod
    def generate_root_cause_narrative(analysis: Dict[str, Any]) -> str:
        """Generate natural language narrative from root cause analysis.
        
        Args:
            analysis: Output from analyze_metadata
            
        Returns:
            Markdown formatted narrative
        """
        narrative = "## 🔍 Root Cause Analysis\n\n"
        
        if not analysis["top_root_causes"]:
            narrative += "No significant patterns detected in issue metadata.\n"
            return narrative
        
        narrative += f"**Total Issues Analyzed:** {analysis['total_issues']}\n\n"
        
        narrative += "### 🎯 Primary Root Causes\n\n"
        
        for i, cause in enumerate(analysis["top_root_causes"], 1):
            narrative += (
                f"{i}. **{cause['attribute'].replace('_', ' ').title()}:** "
                f"`{cause['value']}`\n"
                f"   - Affected Issues: **{cause['affected_issues']}** ({cause['percentage']})\n"
                f"   - 💡 *Recommendation: Focus remediation efforts on {cause['attribute']} = {cause['value']}*\n\n"
            )
        
        if analysis["clusters"]:
            narrative += "### 📊 Issue Clusters\n\n"
            narrative += "Issues are clustering around these combinations:\n\n"
            
            for i, cluster in enumerate(analysis["clusters"], 1):
                attrs = " + ".join([f"{k}={v}" for k, v in cluster["attributes"].items()])
                narrative += f"{i}. {attrs}: **{cluster['count']} issues**\n"
        
        return narrative


class ShadowValidation:
    """Shadow validation sandbox for testing fixes safely."""
    
    @staticmethod
    def create_shadow_table(
        original_table: str,
        project_id: str,
        dataset_id: str
    ) -> str:
        """Create a temporary shadow table for testing.
        
        Args:
            original_table: Name of the original table
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            
        Returns:
            Name of the shadow table
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shadow_table = f"{original_table}_shadow_{timestamp}"
        
        return shadow_table
    
    @staticmethod
    def validate_fix(
        shadow_table: str,
        original_table: str,
        fix_sql: str,
        validation_checks: List[str]
    ) -> Dict[str, Any]:
        """Validate a fix in shadow table before production.
        
        Args:
            shadow_table: Name of shadow table
            original_table: Name of original table
            fix_sql: SQL to apply the fix
            validation_checks: List of SQL validation queries
            
        Returns:
            Validation results
        """
        results = {
            "shadow_table": shadow_table,
            "fix_applied": False,
            "validation_passed": False,
            "checks": []
        }
        
        # This would be implemented with actual BigQuery operations
        # For now, return mock structure
        
        return results
