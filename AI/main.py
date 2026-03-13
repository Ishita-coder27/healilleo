import os
from pathlib import Path

import gradio as gr

from engine import chat_with_ai, get_recommendations
from pdf_processing.vitals_extractor import VitalsExtractor


ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_REPORTS_DIR = ROOT_DIR / "sample_reports"
EXTRACTOR = VitalsExtractor()


def get_sample_report_choices():
    reports = {}
    if SAMPLE_REPORTS_DIR.exists():
        for pdf_path in sorted(SAMPLE_REPORTS_DIR.glob("*.pdf")):
            reports[pdf_path.name] = str(pdf_path)
    return reports


SAMPLE_REPORTS = get_sample_report_choices()


def resolve_report_path(pdf_file, sample_report_name):
    if pdf_file is not None:
        return pdf_file.name, os.path.basename(pdf_file.name)

    if sample_report_name and sample_report_name in SAMPLE_REPORTS:
        sample_path = SAMPLE_REPORTS[sample_report_name]
        return sample_path, sample_report_name

    raise gr.Error("Choose a sample report or upload a PDF before analyzing.")


def normalize_extracted_data(result, report_name):
    vitals = []
    vitals_for_prompt = {}

    for vital in result.get("vitals", []):
        vital_row = {
            "name": vital.name,
            "value": vital.value,
            "unit": vital.unit,
            "status": vital.status,
            "category": vital.category,
            "reference_range": vital.reference_range,
            "confidence": round(vital.confidence, 3),
            "method": vital.method,
        }
        vitals.append(vital_row)

        display_value = vital.value
        if vital.unit:
            display_value = f"{display_value} {vital.unit}"
        if vital.status and vital.status != "Unknown":
            display_value = f"{display_value} [{vital.status}]"
        vitals_for_prompt[vital.name] = display_value

    return {
        "report_name": report_name,
        "patient_info": result.get("patient_info", {}),
        "vitals": vitals_for_prompt,
        "vitals_detailed": vitals,
        "stats": result.get("stats", {}),
        "pdf_method": result.get("pdf_method", "unknown"),
    }


def build_report_summary(report_data):
    patient_info = report_data.get("patient_info", {})
    stats = report_data.get("stats", {})

    patient_name = patient_info.get("Patient Name") or "Unknown"
    age = patient_info.get("Age") or "Unknown"
    gender = patient_info.get("Gender") or "Unknown"
    report_date = patient_info.get("Report Date") or "Unknown"

    top_vitals = report_data.get("vitals_detailed", [])[:8]
    vital_lines = []
    for vital in top_vitals:
        line = f"- {vital['name']}: {vital['value']}"
        if vital["unit"]:
            line += f" {vital['unit']}"
        if vital["status"] and vital["status"] != "Unknown":
            line += f" ({vital['status']})"
        vital_lines.append(line)

    if not vital_lines:
        vital_lines.append("- No vitals were extracted from this report.")

    return "\n".join(
        [
            f"## Report Overview",
            f"**Source Report:** {report_data['report_name']}",
            "",
            f"**Patient:** {patient_name}",
            f"**Age:** {age}",
            f"**Gender:** {gender}",
            f"**Report Date:** {report_date}",
            f"**Extraction Method:** {report_data.get('pdf_method', 'unknown')}",
            "",
            "### Extraction Stats",
            f"- Total vitals found: {stats.get('total', 0)}",
            f"- Normal values: {stats.get('normal', 0)}",
            f"- Abnormal values: {stats.get('abnormal', 0)}",
            "",
            "### Sample of Extracted Vitals",
            *vital_lines,
        ]
    )


def analyze_report(pdf_file, sample_report_name):
    report_path, report_name = resolve_report_path(pdf_file, sample_report_name)
    raw_result = EXTRACTOR.extract(report_path)
    report_data = normalize_extracted_data(raw_result, report_name)
    recommendations = get_recommendations(report_data)
    summary = build_report_summary(report_data)
    status = f"Analyzed `{report_name}`. Ask follow-up questions in the report-aware AI chat."

    return report_data, summary, recommendations, report_data, [], status


def ensure_report_context(pdf_file, sample_report_name, report_data):
    if report_data:
        return report_data

    report_path, report_name = resolve_report_path(pdf_file, sample_report_name)
    raw_result = EXTRACTOR.extract(report_path)
    return normalize_extracted_data(raw_result, report_name)


def ask_report_question(question, pdf_file, sample_report_name, report_data, chat_history):
    if not question or not question.strip():
        raise gr.Error("Enter a question for the report-aware AI assistant.")

    report_context = ensure_report_context(pdf_file, sample_report_name, report_data)
    answer = chat_with_ai(report_context, question.strip())
    updated_history = (chat_history or []) + [[question.strip(), answer]]
    return updated_history, "", report_context


def clear_chat():
    return [], ""


CSS = """
.app-shell {
    max-width: 1200px;
    margin: 0 auto;
}
.hero {
    background: linear-gradient(135deg, #0f2744 0%, #1d4b73 55%, #7bb8d9 100%);
    border-radius: 18px;
    padding: 28px;
    color: #f4fbff;
    margin-bottom: 18px;
}
.hero h1 {
    margin: 0 0 8px;
    font-size: 2.1rem;
}
.hero p {
    margin: 0;
    color: #d5ebf7;
}
"""


with gr.Blocks() as demo:
    report_state = gr.State({})

    with gr.Column(elem_classes=["app-shell"]):
        gr.HTML(
            """
            <div class="hero">
                <h1>AI Health Report Assistant</h1>
                <p>Select a sample report or upload your own PDF, extract the report data,
                then ask questions with that exact report kept in context.</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                sample_report = gr.Dropdown(
                    label="Choose a Sample Report",
                    choices=list(SAMPLE_REPORTS.keys()),
                    value=next(iter(SAMPLE_REPORTS), None),
                    info="Use one of the PDFs from the sample_reports folder.",
                )
                pdf_input = gr.File(
                    label="Or Upload a Medical Report",
                    file_types=[".pdf"],
                )
                analyze_btn = gr.Button("Analyze Report", variant="primary")
                status_output = gr.Markdown()

                gr.Markdown(
                    """
                    **Suggested Ask AI prompts**

                    - What are the abnormal values in this report?
                    - Summarize this report in simple language.
                    - What diet changes should this patient focus on?
                    - Which vitals should be monitored again soon?
                    """
                )

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("Report Summary"):
                        summary_output = gr.Markdown(
                            "Analyze a sample report or upload a PDF to see the report summary."
                        )

                    with gr.Tab("Extracted Data"):
                        extracted_output = gr.JSON(
                            label="Structured report data"
                        )

                    with gr.Tab("Recommendations"):
                        recommendation_output = gr.Textbox(
                            label="Health Recommendations",
                            lines=18,
                        )

        gr.Markdown("## Ask AI About This Report")
        chatbot = gr.Chatbot(
            label="Report-aware AI chat",
            height=420,
        )

        with gr.Row():
            question_input = gr.Textbox(
                label="Ask a question about the analyzed report",
                placeholder="Example: explain the high values in simple words",
                scale=5,
            )
            ask_btn = gr.Button("Ask AI", variant="primary", scale=1)
            clear_btn = gr.Button("Clear Chat", scale=1)

        analyze_btn.click(
            fn=analyze_report,
            inputs=[pdf_input, sample_report],
            outputs=[
                extracted_output,
                summary_output,
                recommendation_output,
                report_state,
                chatbot,
                status_output,
            ],
        )

        ask_btn.click(
            fn=ask_report_question,
            inputs=[question_input, pdf_input, sample_report, report_state, chatbot],
            outputs=[chatbot, question_input, report_state],
        )

        question_input.submit(
            fn=ask_report_question,
            inputs=[question_input, pdf_input, sample_report, report_state, chatbot],
            outputs=[chatbot, question_input, report_state],
        )

        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot, question_input],
        )

demo.launch(
    theme=gr.themes.Soft(),
    css=CSS,
)
