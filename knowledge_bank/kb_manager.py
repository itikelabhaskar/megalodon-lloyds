"""
Knowledge Bank Manager for Treatment Agent

Handles loading, searching, and updating the Knowledge Bank
which stores historical DQ fix patterns and their success rates.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class KnowledgeBankManager:
    """Manages the Knowledge Bank JSON file for historical fix patterns."""
    
    def __init__(self, kb_path: str = "knowledge_bank/knowledge_bank.json"):
        self.kb_path = kb_path
        self._kb_data = None
    
    def load(self) -> Dict:
        """Load Knowledge Bank data from JSON file."""
        if self._kb_data is None:
            with open(self.kb_path, 'r') as f:
                self._kb_data = json.load(f)
        return self._kb_data
    
    def save(self) -> None:
        """Save current Knowledge Bank data to JSON file."""
        if self._kb_data is not None:
            self._kb_data['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            with open(self.kb_path, 'w') as f:
                json.dump(self._kb_data, f, indent=2)
    
    def search_similar_issue(self, issue_pattern: str, issue_description: str) -> Optional[Dict]:
        """
        Search for similar historical issue in Knowledge Bank.
        
        Args:
            issue_pattern: SQL pattern or regex describing the issue
            issue_description: Natural language description of the issue
        
        Returns:
            Dictionary with matching pattern and historical fixes, or None if no match
        """
        kb = self.load()
        
        # Simple keyword matching (in production, use embeddings/vector similarity)
        issue_keywords = set(issue_description.lower().split())
        
        best_match = None
        best_similarity = 0.0
        
        for pattern_id, pattern_data in kb['issue_patterns'].items():
            pattern_keywords = set(pattern_data['description'].lower().split())
            
            # Jaccard similarity
            intersection = issue_keywords.intersection(pattern_keywords)
            union = issue_keywords.union(pattern_keywords)
            similarity = len(intersection) / len(union) if union else 0.0
            
            if similarity > best_similarity and similarity > 0.3:  # 30% threshold
                best_similarity = similarity
                best_match = {
                    'pattern_id': pattern_id,
                    'pattern': pattern_data['pattern'],
                    'description': pattern_data['description'],
                    'similarity': similarity,
                    'historical_fixes': pattern_data['historical_fixes']
                }
        
        return best_match
    
    def get_fix_by_id(self, pattern_id: str, fix_id: str) -> Optional[Dict]:
        """Get specific fix by pattern ID and fix ID."""
        kb = self.load()
        
        if pattern_id not in kb['issue_patterns']:
            return None
        
        for fix in kb['issue_patterns'][pattern_id]['historical_fixes']:
            if fix['fix_id'] == fix_id:
                return fix
        
        return None
    
    def add_new_fix(self, pattern_id: str, fix_data: Dict) -> None:
        """
        Add a new fix to an existing pattern or create new pattern.
        
        Args:
            pattern_id: ID of the pattern (e.g., "DOB_FUTURE")
            fix_data: Dictionary with fix details
        """
        kb = self.load()
        
        if pattern_id not in kb['issue_patterns']:
            # Create new pattern
            kb['issue_patterns'][pattern_id] = {
                'pattern': fix_data.get('pattern', ''),
                'description': fix_data.get('description', ''),
                'dq_dimension': fix_data.get('dq_dimension', 'Unknown'),
                'historical_fixes': []
            }
        
        # Add fix to pattern
        kb['issue_patterns'][pattern_id]['historical_fixes'].append({
            'fix_id': fix_data['fix_id'],
            'fix_type': fix_data['fix_type'],
            'action': fix_data['action'],
            'description': fix_data['description'],
            'success_rate': fix_data.get('success_rate', 0.0),
            'approval_count': fix_data.get('approval_count', 0),
            'rejection_count': fix_data.get('rejection_count', 0),
            'auto_approve': fix_data.get('auto_approve', False),
            'last_used': datetime.now().strftime("%Y-%m-%d"),
            'sql_template': fix_data.get('sql_template', '')
        })
        
        # Update metadata
        kb['metadata']['total_patterns'] = len(kb['issue_patterns'])
        total_fixes = sum(len(p['historical_fixes']) for p in kb['issue_patterns'].values())
        kb['metadata']['total_fixes'] = total_fixes
        
        self._kb_data = kb
        self.save()
    
    def update_fix_stats(self, pattern_id: str, fix_id: str, approved: bool) -> None:
        """
        Update fix statistics after usage.
        
        Args:
            pattern_id: ID of the pattern
            fix_id: ID of the fix
            approved: Whether the fix was approved (True) or rejected (False)
        """
        kb = self.load()
        
        if pattern_id not in kb['issue_patterns']:
            return
        
        for fix in kb['issue_patterns'][pattern_id]['historical_fixes']:
            if fix['fix_id'] == fix_id:
                if approved:
                    fix['approval_count'] += 1
                else:
                    fix['rejection_count'] += 1
                
                # Recalculate success rate
                total = fix['approval_count'] + fix['rejection_count']
                fix['success_rate'] = fix['approval_count'] / total if total > 0 else 0.0
                
                # Update auto-approve eligibility
                auto_threshold = kb['metadata']['auto_approve_threshold']
                min_approvals = kb['metadata']['min_approval_count_for_auto']
                fix['auto_approve'] = (
                    fix['success_rate'] >= auto_threshold and 
                    fix['approval_count'] >= min_approvals
                )
                
                fix['last_used'] = datetime.now().strftime("%Y-%m-%d")
                break
        
        self._kb_data = kb
        self.save()
    
    def get_all_patterns(self) -> Dict:
        """Get all issue patterns and their fixes."""
        kb = self.load()
        return kb['issue_patterns']
    
    def get_auto_approve_eligible_fixes(self) -> List[Dict]:
        """Get all fixes that are eligible for auto-approval."""
        kb = self.load()
        auto_fixes = []
        
        for pattern_id, pattern_data in kb['issue_patterns'].items():
            for fix in pattern_data['historical_fixes']:
                if fix.get('auto_approve', False):
                    auto_fixes.append({
                        'pattern_id': pattern_id,
                        'pattern_description': pattern_data['description'],
                        **fix
                    })
        
        return auto_fixes


# Global singleton instance
_kb_manager = None

def get_kb_manager() -> KnowledgeBankManager:
    """Get or create Knowledge Bank Manager singleton."""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBankManager()
    return _kb_manager
