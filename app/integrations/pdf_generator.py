import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from app.schemas.research_report_schema import ResearchReport


def generate_pdf_report(report: ResearchReport):

    ticker = report.ticker

    directory = f"reports/{ticker}"
    os.makedirs(directory, exist_ok=True)

    file_path = f"{directory}/latest_report.pdf"

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"{ticker} Research Report", styles['Title']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(report.summary, styles['BodyText']))
    elements.append(Spacer(1, 20))

    fundamentals_data = [
        ["Current Price", report.fundamentals.current_price],
        ["Change %", report.fundamentals.change_percent],
    ]

    elements.append(Paragraph("Fundamentals", styles['Heading2']))
    elements.append(Table(fundamentals_data))
    elements.append(Spacer(1, 20))

    sentiment_data = [
        ["Label", report.sentiment.label],
        ["Score", report.sentiment.score],
        ["Articles", report.sentiment.article_count],
    ]

    elements.append(Paragraph("Sentiment", styles['Heading2']))
    elements.append(Table(sentiment_data))
    elements.append(Spacer(1, 20))

    prediction_data = [
        ["Forecast Day 1", report.prediction.forecast_5d[0]],
        ["Forecast Day 2", report.prediction.forecast_5d[1]],
        ["Forecast Day 3", report.prediction.forecast_5d[2]],
        ["Forecast Day 4", report.prediction.forecast_5d[3]],
        ["Forecast Day 5", report.prediction.forecast_5d[4]],
        ["Trend", report.prediction.trend],
        ["Confidence", report.prediction.confidence],
    ]

    elements.append(Paragraph("Price Prediction", styles['Heading2']))
    elements.append(Table(prediction_data))
    elements.append(Spacer(1, 20))

    technical_data = [
        ["RSI", report.technical.rsi],
        ["MACD Signal", report.technical.macd_signal],
        ["BB Position", report.technical.bb_position],
        ["Signal", report.technical.overall_signal],
    ]

    elements.append(Paragraph("Technical Indicators", styles['Heading2']))
    elements.append(Table(technical_data))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("News Highlights", styles['Heading2']))

    for headline in report.news_highlights:
        elements.append(Paragraph(f"- {headline}", styles['BodyText']))

    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Risk Factors", styles['Heading2']))

    for risk in report.risk_factors:
        elements.append(Paragraph(f"- {risk}", styles['BodyText']))

    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Recommendation", styles['Heading2']))
    elements.append(Paragraph(report.recommendation, styles['BodyText']))

    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Analyst Note", styles['Heading2']))
    elements.append(Paragraph(report.analyst_note, styles['BodyText']))

    pdf = SimpleDocTemplate(file_path, pagesize=letter)

    pdf.build(elements)

    return file_path