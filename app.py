import streamlit as st
from google import genai
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="TripCraft AI",
    page_icon="\u2708",
    layout="wide"
)

# ---------------- API SETUP ----------------
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.warning("Running in demo mode (no API key found)")

client = genai.Client(api_key=API_KEY) if API_KEY else None

# ---------------- HELPERS ----------------
def generate_plan(prompt):
    # demo mode fallback
    if client is None:
        return """Day 1:
- Morning: Eiffel Tower - iconic landmark visit
- Afternoon: Louvre Museum - explore art collections
- Evening: Seine River Cruise - relaxing boat ride

Day 2:
- Morning: Montmartre - artistic streets walk
- Afternoon: Champs-Élysées - shopping and cafes
- Evening: Arc de Triomphe - sunset view
"""

    resp = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )
    return resp.text


def parse_days(text):
    days = []
    current = None

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("Day"):
            if current:
                days.append(current)
            current = {"title": line, "items": []}
        elif current:
            current["items"].append(line)

    if current:
        days.append(current)

    return days


def create_pdf(text):
    file_path = "itinerary.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    story = []

    for line in text.split("\n"):
        if line.strip() == "":
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    return file_path


def build_prompt(city, days, budget, interests, user_input):
    return f"""
You are an AI travel planner.

User request: {days} day trip to {city}, budget {budget}, interests: {', '.join(interests)}. {user_input}

Rules:
- Exactly {days} days
- Include mix of food, sightseeing, and experiences
- Avoid repetition
- Each item max 10–12 words

Format:

Day 1:
- Morning: <place> - <short description>
- Afternoon: <place> - <short description>
- Evening: <place> - <short description>

No extra explanation.
"""


# ---------------- HEADER ----------------
st.title("\U0001F30D TripCraft AI")
st.markdown("Plan trips fast without wasting hours \U0001F604")
st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.header("\u2699 Trip Settings")

city = st.sidebar.text_input("City", "Paris")
days = st.sidebar.slider("Number of Days", 1, 10, 3)
budget = st.sidebar.selectbox("Budget", ["Low", "Medium", "High"])
interests = st.sidebar.multiselect(
    "Interests",
    ["Food", "Sightseeing", "Shopping", "Museums", "Nightlife"],
    default=["Sightseeing", "Food"]
)

# ---------------- INPUT ----------------
st.subheader("\U0001F9F3 Describe your trip")

user_input = st.text_area(
    "Additional preferences (optional)",
    placeholder="e.g. I want a relaxing trip with cafes and less walking..."
)

# ---------------- SESSION STATE ----------------
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "last_output" not in st.session_state:
    st.session_state.last_output = None

# ---------------- GENERATE ----------------
if st.button("\U0001F680 Generate Plan"):
    prompt = build_prompt(city, days, budget, interests, user_input)
    st.session_state.last_prompt = prompt

    with st.spinner("\u2728 Creating your travel plan..."):
        try:
            output = generate_plan(prompt)
            st.session_state.last_output = output
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- REGENERATE ----------------
if st.session_state.last_prompt:
    if st.button("\U0001F504 Regenerate Plan"):
        with st.spinner("\U0001F501 Regenerating..."):
            try:
                output = generate_plan(st.session_state.last_prompt)
                st.session_state.last_output = output
            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- OUTPUT ----------------
if st.session_state.last_output:
    st.success("\u2705 Your plan is ready!")
    st.markdown("## \u2728 Your Personalized Itinerary")

    parsed = parse_days(st.session_state.last_output)

    for day in parsed:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e1e1e, #2c2c2c);
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 25px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            border: 1px solid #333;
        ">
            <h2 style="
                color:#00FFD1;
                margin-bottom:15px;
                font-size:24px;
            ">
                \U0001F4C5 {day['title']}
            </h2>
        """, unsafe_allow_html=True)

        for item in day["items"]:
            item = item.lstrip("- ").strip()

            item = item.replace("Morning:", "<b style='color:#FFD700;'>Morning:</b>")
            item = item.replace("Afternoon:", "<b style='color:#87CEFA;'>Afternoon:</b>")
            item = item.replace("Evening:", "<b style='color:#FF7F50;'>Evening:</b>")

            st.markdown(f"""
            <div style="
                background-color:#262626;
                padding:12px 15px;
                border-radius:12px;
                margin-bottom:10px;
                font-size:16px;
                color:#f5f5f5;
                line-height:1.6;
            ">
                {item}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- PDF ----------------
    pdf_file = create_pdf(st.session_state.last_output)

    with open(pdf_file, "rb") as f:
        st.download_button(
            label="\U0001F4C4 Download as PDF",
            data=f,
            file_name="travel_plan.pdf",
            mime="application/pdf"
        )