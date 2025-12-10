import json
import os
from datetime import datetime
from typing import Dict, List, Optional

JIRA_TICKETS_FILE = os.path.join(os.path.dirname(__file__), "jira_tickets.json")


def load_tickets() -> Dict:
    """Load JIRA tickets from JSON file."""
    if not os.path.exists(JIRA_TICKETS_FILE):
        return {"tickets": [], "metadata": {"last_ticket_id": 0, "created_at": datetime.now().isoformat()}}
    
    with open(JIRA_TICKETS_FILE, "r") as f:
        return json.load(f)


def save_tickets(data: Dict) -> None:
    """Save JIRA tickets to JSON file."""
    with open(JIRA_TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_ticket(
    summary: str,
    description: str,
    priority: str = "Medium",
    affected_rows: int = 0,
    fix_sql: Optional[str] = None,
    assignee: str = "DQ-Team"
) -> Dict:
    """Create a new JIRA ticket."""
    data = load_tickets()
    
    # Generate ticket ID
    ticket_num = data["metadata"]["last_ticket_id"] + 1
    ticket_id = f"DQ-{ticket_num:04d}"
    
    ticket = {
        "ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "priority": priority,
        "affected_rows": affected_rows,
        "status": "OPEN",
        "created_at": datetime.now().isoformat(),
        "assignee": assignee,
        "labels": ["data-quality", "auto-generated", "bancs"],
        "comments": [],
        "attachment": {
            "name": "fix_sql.sql",
            "content": fix_sql
        } if fix_sql else None
    }
    
    # Add to tickets
    data["tickets"].append(ticket)
    data["metadata"]["last_ticket_id"] = ticket_num
    
    save_tickets(data)
    
    return ticket


def get_ticket(ticket_id: str) -> Optional[Dict]:
    """Get a specific ticket by ID."""
    data = load_tickets()
    for ticket in data["tickets"]:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    return None


def list_tickets(status: Optional[str] = None) -> List[Dict]:
    """List all tickets, optionally filtered by status."""
    data = load_tickets()
    tickets = data["tickets"]
    
    if status:
        tickets = [t for t in tickets if t["status"] == status]
    
    return tickets


def update_ticket_status(ticket_id: str, new_status: str) -> bool:
    """Update ticket status."""
    data = load_tickets()
    
    for ticket in data["tickets"]:
        if ticket["ticket_id"] == ticket_id:
            ticket["status"] = new_status
            ticket["updated_at"] = datetime.now().isoformat()
            save_tickets(data)
            return True
    
    return False


def add_comment(ticket_id: str, comment: str, author: str = "System") -> bool:
    """Add a comment to a ticket."""
    data = load_tickets()
    
    for ticket in data["tickets"]:
        if ticket["ticket_id"] == ticket_id:
            if "comments" not in ticket:
                ticket["comments"] = []
            
            ticket["comments"].append({
                "author": author,
                "text": comment,
                "created_at": datetime.now().isoformat()
            })
            
            save_tickets(data)
            return True
    
    return False
