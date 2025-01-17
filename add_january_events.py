#!/usr/bin/env python3
"""
Adds the entire January 2005 schedule for Elench AI Automation
to both Google Calendar and Apple Calendar on macOS.
"""

import datetime
import os
import os.path
import pickle
import subprocess

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ------------------------------------------------------
# 1) Define the Repetitive Structure (Hourly, Daily, etc.)
# ------------------------------------------------------

# We’ll model a typical Monday–Friday schedule:
#  06:00–07:00  Morning Routine
#  07:00–08:00  Planning & Admin
#  08:00–10:00  Deep Work Block 1
#  10:00–10:30  Break
#  10:30–12:30  Deep Work Block 2
#  12:30–13:30  Lunch Break
#  13:30–15:30  Operational Work
#  15:30–16:00  Break
#  16:00–18:00  Marketing & Outreach
#  18:00–19:00  Wrap-Up & Personal Time
#  19:00–20:00  Family/Personal
#  20:00–21:00  Optional Work/Study
#  21:00–22:00  Wind Down

# Saturdays (big-picture thinking) and Sundays (rest) will have lighter events.

# Daily Themes (for descriptions):
#   Monday:    Week Agenda & Planning
#   Tuesday:   Product/Service Dev
#   Wednesday: Networking & Outreach
#   Thursday:  Admin & Finances
#   Friday:    Weekly Review & Wrap-Up
#   Saturday:  Big-Picture Thinking
#   Sunday:    Rest & Reflection

WEEKDAY_FOCUS = {
    0: "Focus: Week Agenda & Planning (Monday)",
    1: "Focus: Product/Service Development (Tuesday)",
    2: "Focus: Networking & Marketing (Wednesday)",
    3: "Focus: Admin & Finances (Thursday)",
    4: "Focus: Weekly Review & Wrap-Up (Friday)",
    5: "Focus: Big-Picture Thinking (Saturday)",
    6: "Focus: Rest & Reflection (Sunday)"
}

# Helper function to easily create a start/end time on a specific date.
def dt(year, month, day, hour, minute=0):
    return datetime.datetime(year, month, day, hour, minute)

def weekday_schedule(year, month, day, weekday):
    """
    Returns a list of event dicts for a single day (Mon-Fri).
    weekday: Monday=0 ... Sunday=6
    """
    # Monday–Friday
    if 0 <= weekday <= 4:
        return [
            {
                'summary': 'Morning Routine',
                'start': dt(year, month, day, 6, 0),
                'end':   dt(year, month, day, 7, 0),
                'description': 'Wake up, light exercise, shower, breakfast.'
            },
            {
                'summary': 'Planning & Admin',
                'start': dt(year, month, day, 7, 0),
                'end':   dt(year, month, day, 8, 0),
                'description': 'Check emails, review calendar, daily priorities.'
            },
            {
                'summary': 'Deep Work Block 1',
                'start': dt(year, month, day, 8, 0),
                'end':   dt(year, month, day, 10, 0),
                'description': 'High-focus tasks (strategy, development).'
            },
            {
                'summary': 'Break',
                'start': dt(year, month, day, 10, 0),
                'end':   dt(year, month, day, 10, 30),
                'description': 'Hydration, quick walk, snack.'
            },
            {
                'summary': 'Deep Work Block 2',
                'start': dt(year, month, day, 10, 30),
                'end':   dt(year, month, day, 12, 30),
                'description': 'Follow-ups, calls, business strategy.'
            },
            {
                'summary': 'Lunch Break',
                'start': dt(year, month, day, 12, 30),
                'end':   dt(year, month, day, 13, 30),
                'description': 'Lunch and short rest.'
            },
            {
                'summary': 'Operational Work',
                'start': dt(year, month, day, 13, 30),
                'end':   dt(year, month, day, 15, 30),
                'description': 'Admin tasks, scheduling, finances.'
            },
            {
                'summary': 'Break',
                'start': dt(year, month, day, 15, 30),
                'end':   dt(year, month, day, 16, 0),
                'description': 'Hydration, check messages.'
            },
            {
                'summary': 'Marketing & Outreach',
                'start': dt(year, month, day, 16, 0),
                'end':   dt(year, month, day, 18, 0),
                'description': 'Networking, contacting leads/partners, social media.'
            },
            {
                'summary': 'Wrap-Up & Personal Time',
                'start': dt(year, month, day, 18, 0),
                'end':   dt(year, month, day, 19, 0),
                'description': 'Review day, finalize tasks, short break.'
            },
            {
                'summary': 'Family/Personal',
                'start': dt(year, month, day, 19, 0),
                'end':   dt(year, month, day, 20, 0),
                'description': 'Dinner, relax, personal hobbies.'
            },
            {
                'summary': 'Optional Work/Study',
                'start': dt(year, month, day, 20, 0),
                'end':   dt(year, month, day, 21, 0),
                'description': 'Light tasks, reading, or wind down.'
            },
            {
                'summary': 'Wind Down',
                'start': dt(year, month, day, 21, 0),
                'end':   dt(year, month, day, 22, 0),
                'description': 'Relaxation, reflection, prep for sleep.'
            }
        ]

    # Saturday
    elif weekday == 5:
        return [
            {
                'summary': 'Late Morning Start',
                'start': dt(year, month, day, 8, 0),
                'end':   dt(year, month, day, 9, 0),
                'description': 'Slightly slower morning routine on Saturday.'
            },
            {
                'summary': 'Big-Picture Planning',
                'start': dt(year, month, day, 9, 0),
                'end':   dt(year, month, day, 11, 0),
                'description': 'Industry reading, brainstorming, strategy.'
            },
            {
                'summary': 'Family/Personal Time',
                'start': dt(year, month, day, 11, 0),
                'end':   dt(year, month, day, 14, 0),
                'description': 'Lunch, hobbies, relaxation.'
            },
            {
                'summary': 'Creative Brainstorm Session',
                'start': dt(year, month, day, 14, 0),
                'end':   dt(year, month, day, 16, 0),
                'description': 'Think about new product ideas or improvement.'
            },
            {
                'summary': 'Short Work Session (Optional)',
                'start': dt(year, month, day, 16, 0),
                'end':   dt(year, month, day, 18, 0),
                'description': 'Tie up loose ends if needed.'
            },
            {
                'summary': 'Evening Relaxation',
                'start': dt(year, month, day, 18, 0),
                'end':   dt(year, month, day, 20, 0),
                'description': 'Dinner, time with family/friends.'
            },
            {
                'summary': 'Light Review',
                'start': dt(year, month, day, 20, 0),
                'end':   dt(year, month, day, 21, 0),
                'description': 'Optional reflection on the week.'
            }
        ]

    # Sunday
    else:  # weekday == 6
        return [
            {
                'summary': 'Rest & Leisure',
                'start': dt(year, month, day, 9, 0),
                'end':   dt(year, month, day, 12, 0),
                'description': 'Sleep in, family time, minimal to-do.'
            },
            {
                'summary': 'Personal / Family Time',
                'start': dt(year, month, day, 12, 0),
                'end':   dt(year, month, day, 18, 0),
                'description': 'Relax, hobbies, no major work.'
            },
            {
                'summary': 'Light Weekly Planning',
                'start': dt(year, month, day, 18, 0),
                'end':   dt(year, month, day, 19, 0),
                'description': 'Short session to prep for Monday.'
            }
        ]


# -------------------------------------------------
# 2) Google Calendar Authentication & Setup Methods
# -------------------------------------------------

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_service():
    """
    Authenticate to Google Calendar API, returning a service object.
    Saves/loads user creds from 'token.pickle'.
    """
    creds = None
    # If token.pickle exists, load it
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid creds, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save creds for next time
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def add_event_to_google_calendar(service, event_data):
    """
    Inserts a single event into Google Calendar.
    event_data dict must have 'summary', 'start', 'end', 'description'.
    """
    def to_rfc3339(dt_obj):
        return dt_obj.isoformat()

    event_body = {
        'summary': event_data['summary'],
        'description': event_data.get('description', ''),
        'start': {
            'dateTime': to_rfc3339(event_data['start']),
            'timeZone': 'Europe/London',  # Adjust if needed
        },
        'end': {
            'dateTime': to_rfc3339(event_data['end']),
            'timeZone': 'Europe/London',  # Adjust if needed
        }
    }

    created_event = service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"--> [Google] Created event: {created_event.get('htmlLink')}")


# -------------------------------------
# 3) Apple Calendar Automation (macOS)
# -------------------------------------

def add_event_to_apple_calendar(event_data):
    """
    Uses AppleScript to add events to the default Calendar app on macOS.
    """
    start_str = event_data['start'].strftime('%m/%d/%Y %H:%M')
    end_str = event_data['end'].strftime('%m/%d/%Y %H:%M')
    title = event_data['summary'].replace('"', '\\"')
    notes = event_data.get('description', '').replace('"', '\\"')

    # You can choose a different calendar (e.g. "Work", "Home", etc.) by modifying "tell calendar..."
    script = f'''
    tell application "Calendar"
        activate
        tell calendar "Home"
            make new event with properties {{
                summary: "{title}",
                start date: date "{start_str}",
                end date: date "{end_str}",
                description: "{notes}"
            }}
        end tell
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        print(f"--> [Apple] Added event: {title} ({start_str} - {end_str})")
    except subprocess.CalledProcessError as e:
        print("Error adding event to Apple Calendar:", e)


# -------------------------
# 4) Generate & Insert Events
# -------------------------

def main():
    # Step A: Build a list of all events in January 2005
    all_events = []

    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 1, 31)
    delta = datetime.timedelta(days=1)

    while start_date <= end_date:
        daily_weekday = start_date.weekday()  # Monday=0, Sunday=6
        # Get base schedule for the day
        day_events = weekday_schedule(start_date.year, start_date.month, start_date.day, daily_weekday)

        # Add a top-level event for the daily focus/theme if you want it visible in the calendar:
        focus_event = {
            'summary': WEEKDAY_FOCUS[daily_weekday],
            'start': dt(start_date.year, start_date.month, start_date.day, 0, 0),
            'end':   dt(start_date.year, start_date.month, start_date.day, 0, 15),
            'description': f"Daily Theme: {WEEKDAY_FOCUS[daily_weekday]}"
        }
        # Insert the daily theme event at the front
        day_events.insert(0, focus_event)

        # Combine these day events with the master list
        all_events.extend(day_events)
        start_date += delta

    # Step B: Authenticate once for Google Calendar
    google_service = get_google_service()

    # Step C: Insert each event into both Google Calendar and Apple Calendar
    for event_data in all_events:
        # Google Calendar
        add_event_to_google_calendar(google_service, event_data)
        # Apple Calendar (only on macOS)
        # add_event_to_apple_calendar(event_data)

    print("\nAll January 2025 events have been added to Google and-or Apple Calendars!")

if __name__ == "__main__":
    main()
