import streamlit as st
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import os
import json
import re

from openai import OpenAI

# -----------------------------
# OPENAI SETUP (HARD CODED REPLACED - SAFE)
# -----------------------------

import streamlit as st
from openai import OpenAI

api_key = st.text_input("Enter OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None

# -----------------------------
# STREAMLIT
# -----------------------------
st.set_page_config(page_title="Intelligence Briefing System", layout="wide")
st.title("Intelligence Briefing System")

input_text = st.text_area("Source Material", height=250)
STRICT_MODE = st.toggle("Strict Intelligence Mode", value=True)

# -----------------------------
# SCENARIO NAME
# -----------------------------
def generate_scenario_name(text):
    keywords = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
    return f"OPERATION {keywords[0].upper()}" if keywords else "OPERATION SENTINEL"

# -----------------------------
# GUARANTEED STRUCTURE
# -----------------------------
REQUIRED_STRUCTURE = {
    "EXECUTIVE SUMMARY": 3,
    "KEY INTELLIGENCE": 5,
    "ASSESSMENT": 8,
    "IMPLICATIONS": 5,
    "RISKS": 5,
    "CONFIDENCE ASSESSMENT": 7,
    "RECOMMENDED ACTIONS": 5
}

# -----------------------------
# NORMALISE OUTPUT (IMPORTANT FIX)
# -----------------------------
def normalise_report(report: dict):
    fixed = {}

    for section, required_len in REQUIRED_STRUCTURE.items():
        items = report.get(section, [])

        # ensure list exists
        if not isinstance(items, list):
            items = []

        # pad missing items
        while len(items) < required_len:
            items.append("Insufficient intelligence available to expand this point further.")

        # trim excess
        items = items[:required_len]

        fixed[section] = items

    return fixed

# -----------------------------
# LOCAL FALLBACK
# -----------------------------
def local_analysis(text):
    return normalise_report({
        "EXECUTIVE SUMMARY": [
            "Developing situation under observation.",
            "Information remains fragmented.",
            "No confirmed escalation indicators."
        ],
        "KEY INTELLIGENCE": [
            "Activity patterns observed.",
            "Multiple sources reporting movement.",
            "Infrastructure disruption noted.",
            "Social media reporting inconsistent.",
            "No official confirmation available."
        ],
        "ASSESSMENT": [
            "Situation remains ambiguous.",
            "Indicators suggest possible routine activity.",
            "No hostile intent confirmed."
        ],
        "IMPLICATIONS": [
            "Public uncertainty may increase.",
            "Operational disruption possible.",
            "Escalation remains limited.",
            "Further data may change assessment.",
            "Monitoring required."
        ],
        "RISKS": [
            "Misinterpretation risk present.",
            "Misinformation propagation likely.",
            "Misclassification of activity possible.",
            "Source reliability variable.",
            "Narrative escalation possible."
        ],
        "CONFIDENCE ASSESSMENT": [
            "Confidence is low.",
            "Evidence base is limited.",
            "Verification not yet possible."
        ],
        "RECOMMENDED ACTIONS": [
            "Continue monitoring sources.",
            "Seek corroborating intelligence.",
            "Track escalation indicators.",
            "Validate reporting consistency.",
            "Update assessment as needed."
        ]
    })

# -----------------------------
# PROMPT
# -----------------------------
def build_prompt(text, strict_mode):
    return f"""
You are a professional intelligence analyst.

Return ONLY valid JSON.

You MUST return ALL sections:

EXECUTIVE SUMMARY: 3 items
KEY INTELLIGENCE: 5 items
ASSESSMENT: 8 items
IMPLICATIONS: 5 items
RISKS: 5 items
CONFIDENCE ASSESSMENT: 7 items
RECOMMENDED ACTIONS: 5 items

Each item must be a 3–5 sentence analytical paragraph.

INPUT:
{text}
"""

# -----------------------------
# PDF GENERATION
# -----------------------------
def add_page_decorations(canvas_obj, doc):
    width, height = A4

    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawCentredString(width / 2, height - 20, "SECRET")
    canvas_obj.drawCentredString(width / 2, 20, "SECRET")
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(width - 40, 20, f"Page {doc.page}")
    canvas_obj.restoreState()

# -----------------------------
# PDF BUILDER
# -----------------------------
def generate_mod_pdf(report_dict, scenario_name):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=60,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=1,
        spaceAfter=30
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=18,
        leading=22,
        spaceBefore=12,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=18,
        spaceAfter=8
    )

    bullet_indent = ParagraphStyle(
        "BulletIndent",
        parent=body_style,
        leftIndent=18
    )

    elements = []

    # COVER
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph(f"INTELLIGENCE BRIEFING - {scenario_name}", title_style))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Automated Intelligence Assessment System", body_style))
    elements.append(PageBreak())

    # SECTIONS
    first = True

    for section_num, (section, content_list) in enumerate(report_dict.items(), 1):
        if not first:
            elements.append(PageBreak())
        first = False

        elements.append(Paragraph(f"{section_num}. {section}", section_style))

        if section == "RECOMMENDED ACTIONS":
            for item in content_list:
                elements.append(Paragraph(f"• {item}", bullet_indent))
        else:
            for i, point in enumerate(content_list, 1):
                elements.append(Paragraph(f"{section_num}.{i} {point}", body_style))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 12))

    doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    buffer.seek(0)
    return buffer

# -----------------------------
# MAIN APP
# -----------------------------
if st.button("Generate Intelligence Briefing"):
    if not input_text.strip():
        st.warning("Enter source material")
        st.stop()

    scenario_name = generate_scenario_name(input_text)
    report = None

    # -----------------------------
    # OPENAI ATTEMPT
    # -----------------------------
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional intelligence analyst. Output ONLY valid JSON. No markdown, no commentary."
                    },
                    {
                        "role": "user",
                        "content": build_prompt(input_text, STRICT_MODE)
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content

            if not raw:
                st.error("OPENAI ERROR: Empty response returned")
                st.stop()

            report = json.loads(raw)

        except Exception as e:
            st.error(f"OPENAI ERROR: {e}")
            report = local_analysis(input_text)

    else:
        st.info("No API key detected — running offline mode")
        report = local_analysis(input_text)

    # -----------------------------
    # ENSURE STRUCTURE IS ALWAYS VALID
    # -----------------------------
    report = normalise_report(report)

    # -----------------------------
    # PDF DOWNLOAD
    # -----------------------------
    pdf_file = generate_mod_pdf(report, scenario_name)

    st.download_button(
        "Download SECRET Briefing PDF",
        data=pdf_file,
        file_name=f"{scenario_name.lower().replace(' ', '_')}_briefing.pdf",
        mime="application/pdf"
    )

    # -----------------------------
    # DISPLAY REPORT
    # -----------------------------
    st.subheader(f"INTELLIGENCE BRIEFING - {scenario_name}")

    for section_num, (section, content_list) in enumerate(report.items(), 1):
        st.markdown(f"## {section_num}. {section}")

        for i, point in enumerate(content_list, 1):
            st.markdown(f"**{section_num}.{i}** {point}")