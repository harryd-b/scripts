#!/usr/bin/env python3
"""
Updates Google Calendar for the year 2025 with 4pm-6pm "Marketing & Outreach"
events (Mon–Fri). If events already exist in that slot, we delete them first
and then create new ones with the fresh descriptions from the week-by-week plan.
"""

import datetime
import os
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ------------------------------------
# 1) DEFINE THE WEEK-BY-WEEK SCHEDULE
# ------------------------------------
# Below is the same marketing plan from the prompt, adjusted for 2025.
# For simplicity, each "week" is anchored to a Monday date. The user-specified
# tasks are Monday–Friday. Adjust the start_date if you need to exactly match
# partial weeks (e.g., Jan 2–Jan 5).

def dt(year, month, day, hour=0, minute=0):
    """Helper to create datetime objects easily."""
    return datetime.datetime(year, month, day, hour, minute)

WEEKS = [
    # Week 1: Monday, Jan 6, 2025
    {
        "start_date": datetime.date(2025, 1, 6),
        "focus": "Defining Brand Identity and Messaging",
        "days": {
            "Mon": (
                "1. Brainstorm: What does Elench stand for? (mission, vision, core values)\n"
                "2. Draft your brand story."
            ),
            "Tue": (
                "1. Outline key audience segments (enterprise vs. SMB, technical vs. non-technical)\n"
                "2. Identify unique differentiators."
            ),
            "Wed": (
                "1. Develop brand messaging pillars (3–5 points)\n"
                "2. Map how these pillars solve specific client needs."
            ),
            "Thu": (
                "1. Draft brand tone and style guidelines (formal, friendly, tech-savvy)\n"
                "2. Begin assembling a simple ‘Brand Guidelines’ doc."
            ),
            "Fri": (
                "1. Finalize brand identity draft (refine story, pillars, tone)\n"
                "2. Plan next week’s website update approach."
            )
        }
    },
    # Week 2: Monday, Jan 13, 2025
    {
        "start_date": datetime.date(2025, 1, 13),
        "focus": "Website Updates & Brand Guidelines",
        "days": {
            "Mon": (
                "1. Audit current website (content, design, UX)\n"
                "2. Note required updates to align with new brand identity."
            ),
            "Tue": (
                "1. Prioritize website changes\n"
                "2. Create a simple action plan."
            ),
            "Wed": (
                "1. Start updating website copy (homepage, ‘About,’ etc.)\n"
                "2. Ensure messaging aligns with brand pillars."
            ),
            "Thu": (
                "1. Tidy up website visuals (colors, fonts, imagery)\n"
                "2. Ask a colleague or friend for feedback."
            ),
            "Fri": (
                "1. Compile a short ‘Brand Guidelines’ PDF (logo usage, tone, color scheme)\n"
                "2. Final check & refine website updates."
            )
        }
    },
    # Week 3: Monday, Jan 20, 2025
    {
        "start_date": datetime.date(2025, 1, 20),
        "focus": "Content Strategy & Initial Blog Post",
        "days": {
            "Mon": (
                "1. Develop a quick editorial calendar (next 2–3 months)\n"
                "2. Brainstorm 3–5 key blog post ideas."
            ),
            "Tue": (
                "1. Select your first blog post topic\n"
                "2. Outline the main points (headline, subheadings, key takeaways)."
            ),
            "Wed": (
                "1. Draft the blog post (~600–800 words)\n"
                "2. Incorporate SEO-friendly keywords."
            ),
            "Thu": (
                "1. Edit and proofread your blog post\n"
                "2. Gather or create any supporting images/diagrams."
            ),
            "Fri": (
                "1. Publish the blog post on your website\n"
                "2. Share on LinkedIn or any relevant channel."
            )
        }
    },
    # Week 4: Monday, Jan 27, 2025
    {
        "start_date": datetime.date(2025, 1, 27),
        "focus": "White Paper Planning & Early Drafting",
        "days": {
            "Mon": (
                "1. Identify a high-value white paper topic\n"
                "2. Gather key data, research, existing internal knowledge."
            ),
            "Tue": (
                "1. Create a detailed outline (sections, subtopics, data points)\n"
                "2. Decide on approximate length (5–10 pages?)."
            ),
            "Wed": (
                "1. Draft the introduction and problem statement\n"
                "2. Compile references/statistics to include."
            ),
            "Thu": (
                "1. Draft additional sections (methodology, case examples)\n"
                "2. Keep track of sources and citations."
            ),
            "Fri": (
                "1. Quick review of progress\n"
                "2. Plan next steps for finalizing or refining the white paper."
            )
        }
    },
    # Week 5: Monday, Feb 3, 2025
    {
        "start_date": datetime.date(2025, 2, 3),
        "focus": "Social Media & High-Level SEO Planning",
        "days": {
            "Mon": (
                "1. Define social media goals (brand awareness, lead generation)\n"
                "2. Identify key channels (LinkedIn, Twitter, Medium)."
            ),
            "Tue": (
                "1. Research SEO basics (top keywords, competitor strategies)\n"
                "2. List 10–15 keywords relevant to Elench."
            ),
            "Wed": (
                "1. Draft a social media content calendar (1–2 posts/week)\n"
                "2. Brainstorm post ideas (tips, insights, behind-the-scenes)."
            ),
            "Thu": (
                "1. Outline on-page SEO improvements (meta tags, headings)\n"
                "2. Start implementing small SEO tweaks."
            ),
            "Fri": (
                "1. Gather or create 1–2 social media graphics\n"
                "2. Finalize the social media + SEO plan for the next few weeks."
            )
        }
    },
    # Week 6: Monday, Feb 10, 2025
    {
        "start_date": datetime.date(2025, 2, 10),
        "focus": "Website Optimization & White Paper Completion",
        "days": {
            "Mon": (
                "1. Implement more website SEO updates (site structure, internal linking)\n"
                "2. Perform a speed check (e.g., Google PageSpeed)."
            ),
            "Tue": (
                "1. Continue writing/refining final sections of the white paper\n"
                "2. Check citations and references."
            ),
            "Wed": (
                "1. Edit and proofread the entire white paper draft\n"
                "2. Gather design ideas or templates for final layout."
            ),
            "Thu": (
                "1. Design basic layout (cover page, formatting)\n"
                "2. Insert any charts, visuals, or infographics."
            ),
            "Fri": (
                "1. Final read-through\n"
                "2. Plan the official white paper release date and promotional steps."
            )
        }
    },
    # Week 7: Monday, Feb 17, 2025
    {
        "start_date": datetime.date(2025, 2, 17),
        "focus": "Launching/Publishing White Paper & Ongoing Content",
        "days": {
            "Mon": (
                "1. Publish white paper (PDF on website or gated landing page)\n"
                "2. Create a 'White Paper' web landing page with an email form."
            ),
            "Tue": (
                "1. Draft an email or LinkedIn post announcing the white paper\n"
                "2. Invite contacts to download or share."
            ),
            "Wed": (
                "1. Monitor downloads and gather feedback\n"
                "2. Plan next blog post topic based on white paper insights."
            ),
            "Thu": (
                "1. Draft second blog post summarizing key insights\n"
                "2. Include a CTA to read the full paper."
            ),
            "Fri": (
                "1. Edit and publish the second blog post\n"
                "2. Share on social channels."
            )
        }
    },
    # Week 8: Monday, Feb 24, 2025
    {
        "start_date": datetime.date(2025, 2, 24),
        "focus": "Deepening Social Media Efforts & Brand Awareness",
        "days": {
            "Mon": (
                "1. Evaluate what’s working on social (engagement, clicks)\n"
                "2. Tweak posting schedule based on data."
            ),
            "Tue": (
                "1. Brainstorm 2–3 new content ideas (infographics, short videos, polls)\n"
                "2. Draft initial outlines or scripts."
            ),
            "Wed": (
                "1. Create or source visuals/graphics for social posts\n"
                "2. Schedule next week’s social posts."
            ),
            "Thu": (
                "1. Review brand messaging consistency across channels\n"
                "2. Make any copy/design adjustments."
            ),
            "Fri": (
                "1. Engage with your community: reply to comments, join discussions\n"
                "2. Explore relevant LinkedIn groups or Twitter threads."
            )
        }
    },
    # Week 9: Monday, Mar 3, 2025
    {
        "start_date": datetime.date(2025, 3, 3),
        "focus": "Continuing SEO, Building More Content",
        "days": {
            "Mon": (
                "1. Revisit SEO keywords—check new trends or competitor changes\n"
                "2. Identify 2+ long-tail keywords for an upcoming blog."
            ),
            "Tue": (
                "1. Draft third blog post focusing on one new keyword\n"
                "2. Include internal links to your white paper or prior posts."
            ),
            "Wed": (
                "1. Edit and finalize the third blog post\n"
                "2. Publish it and optimize metadata."
            ),
            "Thu": (
                "1. Review Google Analytics for content performance\n"
                "2. Check page views, time on page, bounce rate."
            ),
            "Fri": (
                "1. Assess top-performing content so far\n"
                "2. Plan improvements for the next content cycle."
            )
        }
    },
    # Week 10: Monday, Mar 10, 2025
    {
        "start_date": datetime.date(2025, 3, 10),
        "focus": "Outreach & Partnerships",
        "days": {
            "Mon": (
                "1. Make a list of potential partners or industry sites for guest posting\n"
                "2. Draft outreach emails/messages."
            ),
            "Tue": (
                "1. Send 2–3 outreach messages\n"
                "2. Follow up on any connections made at events or LinkedIn groups."
            ),
            "Wed": (
                "1. Create a short pitch for a guest blog post or webinar\n"
                "2. Brainstorm topic ideas that benefit both parties."
            ),
            "Thu": (
                "1. Review your website for a 'Partners' or 'Resources' page\n"
                "2. Begin drafting content for that page."
            ),
            "Fri": (
                "1. Measure any responses to outreach\n"
                "2. Adjust your approach for next week."
            )
        }
    },
    # Week 11: Monday, Mar 17, 2025
    {
        "start_date": datetime.date(2025, 3, 17),
        "focus": "Refining Collateral & Simple Case Study",
        "days": {
            "Mon": (
                "1. Review all brand collateral (Guidelines, website, white paper)\n"
                "2. Note any needed updates for consistency."
            ),
            "Tue": (
                "1. Identify a successful project or pilot for a mini case study\n"
                "2. Gather data or quotes to support it."
            ),
            "Wed": (
                "1. Draft the short case study (problem, solution, outcome)\n"
                "2. Proofread and format for website or PDF."
            ),
            "Thu": (
                "1. Finalize the case study and publish on website or LinkedIn\n"
                "2. Create a quick social post linking to it."
            ),
            "Fri": (
                "1. Recap your marketing metrics (downloads, blog views, social engagement)\n"
                "2. Note improvements for the final weeks."
            )
        }
    },
    # Week 12: Monday, Mar 24, 2025
    {
        "start_date": datetime.date(2025, 3, 24),
        "focus": "Wrap-Up & Next Quarter Planning",
        "days": {
            "Mon": (
                "1. Compile a final performance report (analytics, leads, social interactions)\n"
                "2. Compare results to your original goals."
            ),
            "Tue": (
                "1. Identify top 3 successes\n"
                "2. Identify top 3 areas needing improvement."
            ),
            "Wed": (
                "1. Draft a Q2 marketing roadmap (new content ideas, partnerships, events)\n"
                "2. Confirm which tasks can roll over."
            ),
            "Thu": (
                "1. Fine-tune brand guidelines based on new insights\n"
                "2. Archive or restructure any outdated or underperforming content."
            ),
            "Fri": (
                "1. Write a quick internal “Lessons Learned” doc\n"
                "2. Celebrate the progress made—prepare for Q2 initiatives!"
            )
        }
    },
]

# -------------------------------------------------
# 2) GOOGLE CALENDAR AUTH, DELETE, AND RE-CREATE
# -------------------------------------------------

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_service():
    """
    Authenticate to the Google Calendar API and return a service object.
    """
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

    service = build('calendar', 'v3', credentials=creds)
    return service

def delete_existing_marketing_events(service, day_start, day_end):
    """
    Find and delete any existing "Marketing & Outreach" events
    between day_start and day_end (inclusive).
    """
    events_result = service.events().list(
        calendarId='primary',
        timeMin=day_start.isoformat() + 'Z',
        timeMax=day_end.isoformat() + 'Z',
        q="Marketing & Outreach",  # search only for events with this summary in the title/desc
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    for event in events:
        summary = event.get('summary', '')
        # If we want to be extra sure we match EXACT summary, we can check:
        if summary.lower() == "marketing & outreach":
            event_id = event['id']
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            print(f"Deleted existing event: {summary} ({event_id})")

def create_event(service, summary, start_dt, end_dt, description):
    """
    Create a single event in Google Calendar, 4–6 PM "Marketing & Outreach."
    """
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Europe/London'
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Europe/London'
        },
    }
    created = service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"Created event -> {created.get('htmlLink')}")

def main():
    service = get_google_service()

    # For each 'week' in WEEKS, Monday to Friday
    for week_data in WEEKS:
        week_start = week_data["start_date"]
        focus = week_data["focus"]
        tasks_per_day = week_data["days"]  # dict: {"Mon": "...", "Tue": "...", ...}

        # Loop Mon-Fri
        for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
            current_date = week_start + datetime.timedelta(days=i)

            # Build the event description
            daily_tasks = tasks_per_day.get(day_name, "No tasks specified.")
            description = (
                f"**Focus**: {focus}\n\n"
                f"**{day_name} Tasks**:\n{daily_tasks}"
            )

            # Set event times: 4:00 PM to 6:00 PM
            start_dt = dt(current_date.year, current_date.month, current_date.day, 16, 0)
            end_dt   = dt(current_date.year, current_date.month, current_date.day, 18, 0)

            # 1) Delete any existing "Marketing & Outreach" events in this 4–6 PM window
            delete_existing_marketing_events(
                service=service,
                day_start=start_dt,
                day_end=end_dt
            )

            # 2) Create the new event
            create_event(
                service=service,
                summary="Marketing & Outreach",
                start_dt=start_dt,
                end_dt=end_dt,
                description=description
            )

    print("\nAll 'Marketing & Outreach' events have been replaced with updated descriptions for 2025!")

if __name__ == "__main__":
    from google.auth.transport.requests import Request  # needed for token refresh
    main()
