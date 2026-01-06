import os
import re 

from datetime import date
from typing import Any, Dict, List, Tuple


from jira_botter import servicedesk 






# =========================
# Konfiguration
# =========================

# Jira
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = "project = SWELIB"
JIRA_FIELDS = [
    "summary",
    "description",
    "comment",
    "updated",
]
SUPPORT_ACCOUNT_IDS = set([
    "5e5e24b1459a810c9af29a67",
])
SUPPORT_EMAIL_DOMAINS = set([
    # "company.com",
])

SUPPORT_DISPLAYNAME_KEYWORDS = [
    # "Support",
    # "Service Desk",
]
#text
MAX_CHARS_PER_FIELD = 3000






def is_support_author(author: Dict[str, Any]) -> bool:
    if not author:
        return False
    account_id = author.get("accountId") or ""
    email = author.get("emailAddress") or ""  # kann in Cloud fehlen
    display = author.get("displayName") or ""

    if account_id and account_id in SUPPORT_ACCOUNT_IDS:
        return True

    if email and "@" in email:
        domain = email.split("@", 1)[1].lower()
        if domain in SUPPORT_EMAIL_DOMAINS:
            return True

    if display:
        dlow = display.lower()
        for kw in SUPPORT_DISPLAYNAME_KEYWORDS:
            if kw.lower() in dlow:
                return True

    return False

def truncate(text: Any, max_chars: int = MAX_CHARS_PER_FIELD) -> str:
    if not isinstance(text, str):
        return ""
    t = text.strip()
    return t[:max_chars] if len(t) > max_chars else t

def strip_signatures_and_links(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.split(r"(\n--\s*\n|\nMit freundlichen Grüßen|\nBest regards)", text, maxsplit=1)[0]
    return text.strip()

def adf_to_text(node: Any) -> str:
    # Atlassian Document Format -> Text extrahieren
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        parts = []
        if "text" in node and isinstance(node["text"], str):
            parts.append(node["text"])
        for v in node.values():
            if isinstance(v, (dict, list)):
                parts.append(adf_to_text(v))
        return " ".join([p for p in parts if p]).strip()
    if isinstance(node, list):
        return " ".join([adf_to_text(x) for x in node]).strip()
    return ""

def normalize_richtext(field: Any) -> str:
    if field is None:
        return ""
    if isinstance(field, str):
        return field.strip()
    if isinstance(field, (dict, list)):
        return adf_to_text(field).strip()
    return str(field).strip()






def build_problem_solution_raw(issue: Dict[str, Any]) -> Tuple[str, str]:
    fields = issue.get("fields", {}) or {}

    summary = fields.get("summary") or ""
    description = normalize_richtext(fields.get("description"))
    description = strip_signatures_and_links(description)

    comment_obj = fields.get("comment") or {}
    comments = comment_obj.get("comments") or []

    customer_texts: List[str] = []
    support_texts: List[str] = []

    for c in comments:
        body = normalize_richtext(c.get("body"))
        body = strip_signatures_and_links(body)
        if not body:
            continue

        author = c.get("author") or {}
        if is_support_author(author):
            support_texts.append(body)
        else:
            customer_texts.append(body)

    parts_problem = []
    if summary:
        parts_problem.append(str(summary))
    if description:
        parts_problem.append(str(description))
    parts_problem.extend(customer_texts)

    problem_raw = truncate("\n\n".join([p for p in parts_problem if p]).strip())
    solution_raw = truncate("\n\n".join([p for p in support_texts if p]).strip()) if support_texts else ""

    return problem_raw, solution_raw


def process_ticket(issue):
    problem_raw, solution_raw = build_problem_solution_raw(issue)

    return {
        "issue_key": issue.get("key"),
        "problem_raw": problem_raw,
        "solution_raw": solution_raw,
    }















#TODO: could reduce details here already
def fetch_details(ticket_ids: list[str], jira_baseurl: str, jira_auth_email: str, jira_auth_token: str, jira_project: str):
    if not all([jira_baseurl, jira_auth_email, jira_auth_token, jira_project]):
        raise Exception
    
    if not ticket_ids:
        return []

    jira = servicedesk.Jira(jira_baseurl, {"email": jira_auth_email, "api_token": jira_auth_token})
    query = {
        "issueIdsOrKeys": ticket_ids,
        "fields": JIRA_FIELDS,
    }

    response = jira.call(
        f"/rest/api/3/issue/bulkfetch",
        type="POST",
        payload=query
    )

    return [ {"id" : x.get("id"), "key": x.get("key"), "fields": x.get("fields")} for x in response.get("issues", []) or [] ]



def fetch_tickets(jira_baseurl: str, jira_auth_email: str, jira_auth_token: str, jira_project: str, date: date=None, limit=100):
    if not all([jira_baseurl, jira_auth_email, jira_auth_token, jira_project]):
        raise Exception
    

    jira = servicedesk.Jira(jira_baseurl, {"email": jira_auth_email, "api_token": jira_auth_token})
    query = {
        "jql": f'project="{jira_project}" {"" if not date else f'AND updated >= "{date.strftime("%Y-%m-%d %H:%M")}"'} ORDER BY updated ASC', 
    } | ({"maxResults": limit} if limit else {})
    

    while True:
        response = jira.call(
            "/rest/api/3/search/jql",
            params=query
        )
        
                
        yield [ x.get("id") for x in response.get("issues", []) or [] ]

        if limit == None:
            break

        if not limit or not "nextPageToken" in response:
            break

        else:
            query["nextPageToken"] = response["nextPageToken"]









#TODO
if __name__ == "__main__":
    pass
    