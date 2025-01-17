#!/usr/bin/env python3
"""
Updates (or creates if missing) 'Deep Work Block 1' and 'Deep Work Block 2' events
on Google Calendar for Jan 6–17, 2025 (Mon–Fri).
Each day has two 2-hour blocks (8-10am & 10:30am-12:30pm) with the schedule below.
"""

import datetime
import os
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# ------------------------------------------------
# 1) DATA: TWO-WEEK PLAN (JAN 6–17, 2025, MON–FRI)
# ------------------------------------------------
# We'll store each day's content for Block 1 and Block 2.
# Day 1 = Mon, Jan 6,  Day 2 = Tue, Jan 7, ... Day 5 = Fri, Jan 10
# Day 6 = Mon, Jan 13, Day 7 = Tue, Jan 14, ... Day 10 = Fri, Jan 17
#
# Times (local):
#   Block 1: 08:00–10:00
#   Block 2: 10:30–12:30

SCHEDULE = [
    # Week 1
    {
        "date": datetime.date(2025, 1, 6),   # Day 1 (Mon)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Detailed Use Case Identification\n\n"
            "• Brainstorm 3–5 workflows to automate; pick 1–2 for MVP.\n"
            "• Write user stories/acceptance criteria.\n"
            "• Define success metrics (reduce manual effort, ensure error-free triggers).\n"
            "• Deliverable: short doc with workflow triggers, conditions, actions."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "System Architecture Design\n\n"
            "• Sketch system structure (rule engine, data flow, multi-channel integration).\n"
            "• Decide on tech stack (Python, Node, etc.) & logging/error strategy.\n"
            "• Deliverable: concise architecture diagram & approach to logging."
        ),
    },
    {
        "date": datetime.date(2025, 1, 7),   # Day 2 (Tue)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Development Environment Setup\n\n"
            "• Create Git repo, branches, basic CI/CD.\n"
            "• Install/configure base libraries (requests, Slack SDK, etc.).\n"
            "• Set up database (SQLite or similar) if needed.\n"
            "• Deliverable: project skeleton & working dev environment."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Implement Basic Rule Engine\n\n"
            "• Write a simple class/function to parse triggers & conditions.\n"
            "• Hardcode or load rules from JSON/YAML.\n"
            "• Unit tests to confirm rule engine logic.\n"
            "• Deliverable: minimal rule engine + test outputs."
        ),
    },
    {
        "date": datetime.date(2025, 1, 8),   # Day 3 (Wed)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Workflow Integration\n\n"
            "• Implement input side (e.g., connect to CRM or mock data).\n"
            "• Ensure rule engine can receive 'trigger' data.\n"
            "• Deliverable: functioning pipeline for one real/mocked workflow."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Refine Logging & Error Handling\n\n"
            "• Log every trigger/event with timestamp.\n"
            "• Catch/report errors (error log or Slack alert).\n"
            "• Manual end-to-end testing to ensure correct action.\n"
            "• Deliverable: stable pipeline w/ robust logging."
        ),
    },
    {
        "date": datetime.date(2025, 1, 9),   # Day 4 (Thu)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Introduce a Second Channel\n\n"
            "• Integrate a different service (Slack if you did email first, etc.).\n"
            "• Expand rule engine to handle multiple actions per trigger.\n"
            "• Deliverable: multi-channel support with two distinct integrations."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Adaptive Learning Planning\n\n"
            "• Decide how feedback is collected (UI, endpoint, etc.).\n"
            "• Data model for feedback (store user override, success/fail, etc.).\n"
            "• Deliverable: plan & data schema for adaptive learning."
        ),
    },
    {
        "date": datetime.date(2025, 1, 10),  # Day 5 (Fri)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Implement Feedback Capture\n\n"
            "• Add code to log user feedback (REST endpoint or small UI).\n"
            "• If time, add simple auto-disable for consistently rejected rules.\n"
            "• Deliverable: functioning feedback collection, placeholder adaptive logic."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Extended Testing & Validation\n\n"
            "• Test with varied triggers to ensure correct actions/logging.\n"
            "• Fix top-priority bugs, clean up code.\n"
            "• Deliverable: more robust MVP w/ multiple triggers/channels + feedback."
        ),
    },
    # Week 2
    {
        "date": datetime.date(2025, 1, 13),  # Day 6 (Mon)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Improve Rule Engine Flexibility\n\n"
            "• Let rules be defined/updated without full redeploy (external config).\n"
            "• Possibly add priority/weighting to rules.\n"
            "• Deliverable: dynamic rule configuration."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Documentation & Onboarding Materials\n\n"
            "• Write a User Guide (how to add/edit rules, how feedback is used).\n"
            "• Demo prep (script or slides) for showing end-to-end functionality.\n"
            "• Deliverable: draft docs + demo plan."
        ),
    },
    {
        "date": datetime.date(2025, 1, 14),  # Day 7 (Tue)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Add Another Workflow (Optional)\n\n"
            "• If time, define a second workflow with different triggers/actions.\n"
            "• Check moderate load performance (10 triggers at once?).\n"
            "• Deliverable: additional workflow integrated, performance notes."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Monitoring & Basic 24/7 Considerations\n\n"
            "• Set up alerts if system goes down or triggers fail often.\n"
            "• Outline support channels (Slack, email) & escalation path.\n"
            "• Deliverable: minimal monitoring approach + support plan."
        ),
    },
    {
        "date": datetime.date(2025, 1, 15),  # Day 8 (Wed)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Comprehensive QA & Regression Testing\n\n"
            "• Run through all workflows, channels, logs, feedback loops.\n"
            "• Document edge cases or issues.\n"
            "• Deliverable: formal QA/test report, improved UX/logging."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Security & Permissions Review\n\n"
            "• Check auth/authorization, secure credential storage.\n"
            "• Final bug fix sprint from QA.\n"
            "• Deliverable: documented security checklist + stable build."
        ),
    },
    {
        "date": datetime.date(2025, 1, 16),  # Day 9 (Thu)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Community/Training Materials\n\n"
            "• Build a Knowledge Base or wiki pages.\n"
            "• Outline short tutorials (docs or videos).\n"
            "• Deliverable: knowledge base articles, draft training materials."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Final Integration Tests\n\n"
            "• Confirm end-to-end flow: rule engine, multi-channel actions, feedback, etc.\n"
            "• Prepare final review for stakeholders.\n"
            "• Deliverable: comprehensive test coverage + final review materials."
        ),
    },
    {
        "date": datetime.date(2025, 1, 17),  # Day 10 (Fri)
        "block1_title": "Deep Work Block 1",
        "block1_desc": (
            "Roadmap for Future Enhancements\n\n"
            "• Brainstorm next-level features (advanced ML, scaling solutions).\n"
            "• Polish any loose ends (code cleanup, small UI tweaks).\n"
            "• Deliverable: future roadmap doc + refined MVP."
        ),
        "block2_title": "Deep Work Block 2",
        "block2_desc": (
            "Formal Demo or Presentation\n\n"
            "• Walk through trigger → rule engine → action → feedback.\n"
            "• Highlight logs, monitoring, support channels.\n"
            "• Deliverable: final demo + stakeholder sign-off or next steps."
        ),
    },
]


# -----------------------------------------
# 2) GOOGLE CALENDAR AUTH & EVENT UPDATING
# -----------------------------------------

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_service():
    """Authenticate to Google Calendar API and return a service object."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def find_event_by_summary_in_range(service, summary, start_dt, end_dt):
    """
    Search for an event with the given 'summary' between start_dt and end_dt.
    Return the first matching event dict or None if not found.
    For the query, we must provide valid RFC3339 strings with 'Z' or an offset.
    """
    time_min_str = start_dt.isoformat() + 'Z'
    time_max_str = end_dt.isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min_str,
        timeMax=time_max_str,
        q=summary,           # search by summary
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    for evt in events:
        if evt.get('summary', '').lower() == summary.lower():
            return evt
    return None


def update_event_description(service, event_data, new_description):
    """
    Update the 'description' field of an existing event (event_data),
    then call the API to persist changes.
    """
    event_data['description'] = new_description
    updated_event = service.events().update(
        calendarId='primary',
        eventId=event_data['id'],
        body=event_data
    ).execute()
    print(f"UPDATED event: {updated_event.get('htmlLink')}")


def create_event(service, summary, start_dt, end_dt, description):
    """
    Create a new event if none is found.
    Times are specified as naive datetimes here, but the 'timeZone'
    in the event body clarifies actual zone used on the calendar.
    """
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Europe/London'  # or your preferred zone
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Europe/London'
        },
    }
    created = service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"CREATED event -> {created.get('htmlLink')}")


# -------------------------
# 3) MAIN WORKFLOW (UPDATE)
# -------------------------

def main():
    service = get_google_service()

    # For each day in SCHEDULE, we have block1 and block2
    for day_info in SCHEDULE:
        date_ = day_info["date"]

        # Times for block 1: 08:00–10:00
        block1_start = datetime.datetime(date_.year, date_.month, date_.day, 8, 0)
        block1_end   = datetime.datetime(date_.year, date_.month, date_.day, 10, 0)

        # Times for block 2: 10:30–12:30
        block2_start = datetime.datetime(date_.year, date_.month, date_.day, 10, 30)
        block2_end   = datetime.datetime(date_.year, date_.month, date_.day, 12, 30)

        # Summaries & descriptions
        b1_summary = day_info["block1_title"]
        b1_desc    = day_info["block1_desc"]
        b2_summary = day_info["block2_title"]
        b2_desc    = day_info["block2_desc"]

        # 1) Handle Deep Work Block 1
        existing_b1 = find_event_by_summary_in_range(service, b1_summary, block1_start, block1_end)
        if existing_b1:
            # Update it
            update_event_description(service, existing_b1, b1_desc)
        else:
            # Create new
            create_event(service, b1_summary, block1_start, block1_end, b1_desc)

        # 2) Handle Deep Work Block 2
        existing_b2 = find_event_by_summary_in_range(service, b2_summary, block2_start, block2_end)
        if existing_b2:
            # Update it
            update_event_description(service, existing_b2, b2_desc)
        else:
            # Create new
            create_event(service, b2_summary, block2_start, block2_end, b2_desc)

    print("\nAll Deep Work blocks (Jan 6–17, 2025) have been updated or created!")


if __name__ == "__main__":
    main()
