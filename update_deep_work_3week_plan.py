#!/usr/bin/env python3

import datetime
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# -----------------------------------------------------
# 1) DEFINE THE 3-WEEK (15 BUSINESS DAYS) PLAN DETAILS
# -----------------------------------------------------
# We'll store each day (1..15) in a list of dicts.
# Each dict has 'block1_desc' and 'block2_desc'.
# The script will schedule them on consecutive weekdays,
# starting from "tomorrow" (skipping Sat/Sun).

PLAN = [
    {
        "day_label": "Day 1",
        "block1_desc": (
            "Kickoff & Architecture Overview\n\n"
            "• Review PlantUML diagram and confirm scope for each layer.\n"
            "• Identify any pre-existing resources (Kubernetes, logging stack, etc.).\n"
            "• Finalize chosen technologies (Docker/K8s, ELK, RabbitMQ/Kafka, etc.).\n"
            "• Set Up Core Repos & Basic Project Structure:\n"
            "  - Create repos/folders for each layer.\n"
            "  - Initialize Git & minimal CI.\n"
            "Deliverables:\n"
            "• Finalized architecture outline.\n"
            "• Git repo(s) with basic folder structures."
        ),
        "block2_desc": (
            "Container Orchestration (Kubernetes) Setup\n\n"
            "• Spin up a K8s cluster (Minikube, cloud, or on-prem).\n"
            "• Create minimal Helm charts/manifests as placeholders.\n"
            "• Basic IAM & Security Config:\n"
            "  - Decide on authN/Z (RBAC, Identity Provider, token-based, etc.).\n"
            "  - Plan secret management for credentials.\n"
            "Deliverables:\n"
            "• A functioning K8s environment with placeholder services.\n"
            "• Initial IAM plan (access rules, secret storage)."
        ),
    },
    {
        "day_label": "Day 2",
        "block1_desc": (
            "Logging & Monitoring (Observability) Setup\n\n"
            "• Deploy or configure chosen stack (ELK, EFK, or Grafana/Prometheus).\n"
            "• Verify logs from placeholder containers are collected.\n"
            "• Infrastructure Smoke Test:\n"
            "  - Run a 'Hello World' container to confirm logs & metrics.\n"
            "Deliverables:\n"
            "• Logging/monitoring capturing container logs/metrics.\n"
            "• A test service in the cluster for validation."
        ),
        "block2_desc": (
            "Global Context (Knowledge Graph) Prep\n\n"
            "• Stand up a lightweight Knowledge Graph DB (Neo4j or GraphDB).\n"
            "• Outline initial schema for domain entities.\n"
            "Data Storage / Data Lake Planning\n"
            "• Decide on raw data storage (S3, HDFS, local FS?).\n"
            "• Plan structured data storage (SQL or NoSQL).\n"
            "Deliverables:\n"
            "• Running Knowledge Graph instance (minimal).\n"
            "• Data Lake / Warehouse approach documented."
        ),
    },
    {
        "day_label": "Day 3",
        "block1_desc": (
            "Workflow Scheduling & Event Broker Setup\n\n"
            "• Pick a scheduling/orchestration tool (Airflow, Argo, etc.).\n"
            "• Spin up a Pub-Sub / Message Queue (RabbitMQ, Kafka, etc.).\n"
            "• Test a minimal 'hello workflow' (time/event-based trigger).\n"
            "Deliverables:\n"
            "• Basic scheduling system triggering tasks.\n"
            "• Working message bus with a test publisher/subscriber."
        ),
        "block2_desc": (
            "LLM Integration (Optional Stub)\n\n"
            "• Create a microservice or stub function for LLM calls (OpenAI API, local GPT container).\n"
            "• Ensure orchestration can invoke this service.\n"
            "Security & Access Controls\n"
            "• Set up basic API keys/JWT for bus & LLM.\n"
            "Deliverables:\n"
            "• LLM stub that handles simple text input/output.\n"
            "• Secure messaging channels with tokens or service accounts."
        ),
    },
    {
        "day_label": "Day 4",
        "block1_desc": (
            "Autonomous Workflow Agents – Basic Skeleton\n\n"
            "• Create code modules for:\n"
            "  - Task Automation (rule-based)\n"
            "  - Adaptive Learning (ML stubs)\n"
            "  - Specialized Agents\n"
            "• Decide how agents register with bus/orchestration.\n"
            "• Agent Collaboration Bus Integration:\n"
            "  - Agents subscribe to relevant queues/topics.\n"
            "  - Test message from orchestration to agent.\n"
            "Deliverables:\n"
            "• Basic code structure for Agents.\n"
            "• Agents able to receive & log test events."
        ),
        "block2_desc": (
            "Rule-Based Agent Implementation\n\n"
            "• Implement a simple rule engine (if–then) using JSON/YAML.\n"
            "• Parse triggers from the bus, execute a dummy action.\n"
            "Agent Logging & Observability\n"
            "• Ensure each agent logs inbound triggers & errors.\n"
            "• Logs visible in ELK/Grafana.\n"
            "Deliverables:\n"
            "• A functioning rule-based agent.\n"
            "• Observable logs in monitoring stack."
        ),
    },
    {
        "day_label": "Day 5",
        "block1_desc": (
            "Adaptive Learning Agent Stub\n\n"
            "• Set up a minimal ML-based agent (scikit-learn, TF, or placeholder) to classify or set priority.\n"
            "• Data Flow to ML Model:\n"
            "  - Confirm events can reach the ML agent.\n"
            "  - ML outputs a recommendation.\n"
            "Deliverables:\n"
            "• Basic ML-based agent.\n"
            "• End-to-end path for event → ML model → recommendation."
        ),
        "block2_desc": (
            "Presentation/UI Layer – Initial Setup\n\n"
            "• Stand up a minimal UI (React/Angular/Vue or simple web dashboard).\n"
            "• Display agent outputs/logs.\n"
            "Integration with Orchestration\n"
            "• Let users trigger/schedule workflows from the UI.\n"
            "• Show relevant knowledge graph snippets.\n"
            "Deliverables:\n"
            "• Basic UI or dashboard showing agent events.\n"
            "• API endpoints to orchestrate workflows from front-end."
        ),
    },
    {
        "day_label": "Day 6",
        "block1_desc": (
            "Refine Global Context (Knowledge Graph)\n\n"
            "• Insert actual domain data.\n"
            "• Provide an interface for agents to query/update the graph.\n"
            "Workflows with Knowledge Graph\n"
            "• Enhance scheduling logic to include knowledge-graph context.\n"
            "Deliverables:\n"
            "• Populated knowledge graph with domain data.\n"
            "• Orchestration that passes context to agents."
        ),
        "block2_desc": (
            "Specialized Agents\n\n"
            "• Implement at least one domain-specific agent (e.g., Document Processing, Compliance Checker).\n"
            "• Demonstrate scenario where specialized agent consults rule-based or ML-based agent.\n"
            "Deliverables:\n"
            "• Specialized agent performing real domain tasks.\n"
            "• Inter-agent communication example."
        ),
    },
    {
        "day_label": "Day 7",
        "block1_desc": (
            "Data & Analytics Layer – Real-Time Streams\n\n"
            "• If not done, stand up Kafka or another real-time broker.\n"
            "• Ingest mock source data (sensor, transaction logs, etc.).\n"
            "• Agent Integration:\n"
            "  - Subscribe agent to real-time topic.\n"
            "Deliverables:\n"
            "• Functioning real-time data pipeline.\n"
            "• Agent reacting to live or simulated streaming events."
        ),
        "block2_desc": (
            "Data Lake / Warehouse Integration\n\n"
            "• Hook up pipeline so processed data lands in S3, HDFS, or Snowflake/BigQuery.\n"
            "• ML Model Storage & Lifecycle:\n"
            "  - Decide on model versioning (local folder, MLflow, S3, etc.).\n"
            "Deliverables:\n"
            "• Data ingestion path from streams to persistent storage.\n"
            "• Basic approach for updating/replacing ML models."
        ),
    },
    {
        "day_label": "Day 8",
        "block1_desc": (
            "UI Enhancements & Reporting\n\n"
            "• Add pages/dashboards showing workflow statuses, agent decisions.\n"
            "• Include simple charts if feasible.\n"
            "Role-Based Access / Permissions in UI\n"
            "• Integrate with IAM to restrict views/actions.\n"
            "Deliverables:\n"
            "• More informative UI with real-time agent activity.\n"
            "• Security/permissions in front-end."
        ),
        "block2_desc": (
            "Feedback Loop & Continuous Learning\n\n"
            "• Let users override or rate agent decisions in the UI.\n"
            "• Persist feedback in DB or knowledge graph.\n"
            "Adaptive Learning Updates\n"
            "• ML agent incorporates user feedback.\n"
            "• Rule-based agent stores exceptions.\n"
            "Deliverables:\n"
            "• Feedback mechanism in UI.\n"
            "• Basic adaptive improvement path for agents."
        ),
    },
    {
        "day_label": "Day 9",
        "block1_desc": (
            "Advanced Logging & Monitoring\n\n"
            "• Build detailed dashboards in Kibana/Grafana (agent throughput, error rates).\n"
            "• Set up alerts for high error rates or job failures.\n"
            "Disaster Recovery & Scaling\n"
            "• Outline how to scale containers (K8s autoscaling).\n"
            "• Simple backup/snapshot strategy for DB.\n"
            "Deliverables:\n"
            "• Monitoring dashboards with relevant metrics.\n"
            "• Scaling/DR plan for data & knowledge graph."
        ),
        "block2_desc": (
            "Integration & Stress Testing\n\n"
            "• Generate test workloads to check concurrency.\n"
            "• Identify bottlenecks (MQ capacity, ML CPU usage, etc.).\n"
            "Performance Tuning\n"
            "• Tweak config (Kafka partitions, K8s resources) to handle more throughput.\n"
            "Deliverables:\n"
            "• Performance report on system capacity.\n"
            "• Optimized configs for at least one bottleneck."
        ),
    },
    {
        "day_label": "Day 10",
        "block1_desc": (
            "Compliance & Security Review\n\n"
            "• Check domain-specific regs (GDPR, HIPAA, etc.).\n"
            "• Ensure data encryption in transit/at rest.\n"
            "• Verify logs do not expose sensitive info.\n"
            "Finalize Agent Collaboration Patterns\n"
            "• Document standard agent-to-agent request flows.\n"
            "Deliverables:\n"
            "• A compliance checklist or security posture summary.\n"
            "• Formalized agent collaboration patterns."
        ),
        "block2_desc": (
            "Thorough End-to-End Testing\n\n"
            "• Test a multi-step workflow using real-time streams, knowledge graph, ML agent, feedback loop.\n"
            "• Confirm logs/metrics/UI all update correctly.\n"
            "Bug Triage & Fixes\n"
            "• Resolve high/medium-severity bugs.\n"
            "Deliverables:\n"
            "• Successful end-to-end test covering all layers.\n"
            "• Clean codebase with critical bugs fixed."
        ),
    },
    {
        "day_label": "Day 11",
        "block1_desc": (
            "Documentation Deep Dive\n\n"
            "• Refine developer docs (how to add new agents, define new workflows).\n"
            "• Document infrastructure steps (K8s deployment, network topology).\n"
            "User-Facing Docs/Tutorials\n"
            "• Create FAQ/how-to guide for UI usage.\n"
            "• Possibly record short videos.\n"
            "Deliverables:\n"
            "• Detailed developer-oriented docs.\n"
            "• User guides or tutorials for non-technical stakeholders."
        ),
        "block2_desc": (
            "UI/UX Improvements\n\n"
            "• Polish front-end for clarity and visual appeal.\n"
            "• Possibly add advanced features (filtering tasks, searching logs, toggling agent behaviors).\n"
            "Optional Portal Features\n"
            "• Real-time dashboards, graph visualization of knowledge graph, etc.\n"
            "Deliverables:\n"
            "• A more polished UI with better user experience.\n"
            "• Potential advanced portal features (if time)."
        ),
    },
    {
        "day_label": "Day 12",
        "block1_desc": (
            "LLM Integration Refinement\n\n"
            "• Add more advanced prompt management or chain-of-thought logic.\n"
            "• Incorporate user feedback to improve text responses.\n"
            "Agent Collaboration Scenarios\n"
            "• Build scenario templates (e.g., 'New Customer Onboarding') spanning multiple agents.\n"
            "Deliverables:\n"
            "• More robust LLM integration.\n"
            "• Scenario templates for multi-agent collaboration."
        ),
        "block2_desc": (
            "Advanced ML/AI Model Management\n\n"
            "• Implement/Refine model registry (MLflow, SageMaker, etc.).\n"
            "• Show how to swap/update ML model in production.\n"
            "Validation of ML Outcomes\n"
            "• Track accuracy, precision/recall, etc.\n"
            "Deliverables:\n"
            "• A model registry or pipeline for updating ML agent.\n"
            "• Basic ML performance tracking."
        ),
    },
    {
        "day_label": "Day 13",
        "block1_desc": (
            "Scalability & Load Testing\n\n"
            "• Expand load tests for multiple concurrent workflows.\n"
            "• Evaluate horizontal autoscaling for busiest components.\n"
            "Resilience Testing\n"
            "• Simulate partial failures (offline knowledge graph, dropped messages).\n"
            "Deliverables:\n"
            "• Scalability report with recommended resource settings.\n"
            "• Documented resilience test outcomes."
        ),
        "block2_desc": (
            "Edge-Case Handling & Advanced Error Recovery\n\n"
            "• Improve error-handling in agents (retries, fallback, manual intervention).\n"
            "• Update orchestration to handle timeouts or crashes gracefully.\n"
            "Collaboration Protocol Refinement\n"
            "• Add versioning/message schema definitions to let agents evolve independently.\n"
            "Deliverables:\n"
            "• Agents with robust error recovery.\n"
            "• Documented versioning/messaging protocol."
        ),
    },
    {
        "day_label": "Day 14",
        "block1_desc": (
            "Compliance & Audit Logging\n\n"
            "• Ensure all critical decisions (esp. ML-based) are auditable (model version, data used).\n"
            "• Enhance logs for traceability.\n"
            "Final Security Pass\n"
            "• Confirm SSL/TLS for bus, LLM calls, data lake writes.\n"
            "• Update container images for patches.\n"
            "Deliverables:\n"
            "• Audit-ready log structure.\n"
            "• Security review ensuring minimal vulnerabilities."
        ),
        "block2_desc": (
            "Documentation & Training Updates\n\n"
            "• Merge new features, security steps, best practices into docs.\n"
            "• Possibly set up a training or certification framework (internal or external).\n"
            "Deliverables:\n"
            "• Comprehensive docs reflecting final architecture.\n"
            "• Training/certification outline (if relevant)."
        ),
    },
    {
        "day_label": "Day 15",
        "block1_desc": (
            "Final End-to-End Demo\n\n"
            "• Show entire system: UI → bus → agents → data & ML → feedback loop.\n"
            "• Show logs, metrics, real-time updates.\n"
            "Collect Stakeholder Feedback\n"
            "• Gather final input or must-fix items.\n"
            "Deliverables:\n"
            "• A recorded or live final demo.\n"
            "• A list of final feedback or next-phase enhancements."
        ),
        "block2_desc": (
            "MVP Sign-Off & Roadmap\n\n"
            "• Compile 'post-project' or 'next steps' doc (known limitations, future expansions).\n"
            "• Plan for 24/7 support, advanced SLAs, or commercialization if relevant.\n"
            "Wrap-Up & Handover\n"
            "• Ensure code, docs, creds in a secure repo.\n"
            "• Close out tasks or schedule them for next iteration.\n"
            "Deliverables:\n"
            "• MVP sign-off with readiness statement.\n"
            "• Future roadmap for further development/scaling."
        ),
    },
]


# ----------------------------------------
# 2) GOOGLE CALENDAR OAUTH AND HELPERS
# ----------------------------------------

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_service():
    """
    Authenticate to the Google Calendar API, returning a service object.
    We'll store credentials in token.pickle after the first run.
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

    return build('calendar', 'v3', credentials=creds)


def find_event_by_summary_in_range(service, summary, start_dt, end_dt):
    """
    Look for an event with the given summary between start_dt and end_dt.
    Return the first matching event dict or None if not found.
    (We append 'Z' to indicate UTC time for timeMin/timeMax.)
    """
    time_min_str = start_dt.isoformat() + 'Z'
    time_max_str = end_dt.isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min_str,
        timeMax=time_max_str,
        q=summary,
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
    Update the 'description' of an existing event.
    """
    event_data['description'] = new_description
    updated_event = service.events().update(
        calendarId='primary',
        eventId=event_data['id'],
        body=event_data
    ).execute()
    print(f"[UPDATED] {updated_event.get('htmlLink')}")


def create_event(service, summary, start_dt, end_dt, description):
    """
    Create a new event with the specified summary, times, and description.
    We'll set the timeZone to 'Europe/London'.
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
    print(f"[CREATED] {created.get('htmlLink')}")


# ----------------------------------------
# 3) MAIN LOGIC - SCHEDULING 15 WORKDAYS
# ----------------------------------------

def main():
    service = get_google_service()

    # Determine the first day (tomorrow):
    # We'll skip weekends, scheduling only Mon-Fri for 15 days.
    # Start from tomorrow, increment until we've placed all 15 plan items.
    days_needed = len(PLAN)
    day_count = 0
    current_date = datetime.date.today() + datetime.timedelta(days=1)

    while day_count < days_needed:
        # Skip Saturday (5) & Sunday (6)
        if current_date.weekday() < 5:  # 0=Mon, 4=Fri
            # We have a new business day
            plan_item = PLAN[day_count]

            # Build times for each block
            # Block 1: 08:00-10:00
            block1_start = datetime.datetime(
                current_date.year, current_date.month, current_date.day, 8, 0
            )
            block1_end = datetime.datetime(
                current_date.year, current_date.month, current_date.day, 10, 0
            )

            # Block 2: 10:30-12:30
            block2_start = datetime.datetime(
                current_date.year, current_date.month, current_date.day, 10, 30
            )
            block2_end = datetime.datetime(
                current_date.year, current_date.month, current_date.day, 12, 30
            )

            # Summaries
            b1_summary = "Deep Work Block 1"
            b2_summary = "Deep Work Block 2"

            # Descriptions from plan
            b1_desc = f"{plan_item['day_label']} - {b1_summary}\n\n{plan_item['block1_desc']}"
            b2_desc = f"{plan_item['day_label']} - {b2_summary}\n\n{plan_item['block2_desc']}"

            # 1) Block 1: Update or create
            existing_b1 = find_event_by_summary_in_range(service, b1_summary, block1_start, block1_end)
            if existing_b1:
                update_event_description(service, existing_b1, b1_desc)
            else:
                create_event(service, b1_summary, block1_start, block1_end, b1_desc)

            # 2) Block 2: Update or create
            existing_b2 = find_event_by_summary_in_range(service, b2_summary, block2_start, block2_end)
            if existing_b2:
                update_event_description(service, existing_b2, b2_desc)
            else:
                create_event(service, b2_summary, block2_start, block2_end, b2_desc)

            day_count += 1

        # Move to the next calendar day
        current_date += datetime.timedelta(days=1)

    print(f"\nAll {days_needed} business days (2 blocks each) have been updated/created in 'Europe/London' time zone!")


if __name__ == "__main__":
    main()
