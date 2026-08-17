import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_calculator_pdf(amount, rate_annual, tenure):
    """
    Generates a secure in-memory PDF document for the EMI Amortization Schedule.
    Safe against zero-interest calculations.
    """
    if rate_annual == 0:
        emi = amount / tenure
        total_payment = amount
        total_interest = 0
        rate_monthly = 0
    else:
        rate_monthly = (rate_annual / 100) / 12
        power = (1 + rate_monthly) ** tenure
        emi = amount * rate_monthly * power / (power - 1)
        total_payment = emi * tenure
        total_interest = total_payment - amount

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#0056D2'),
        spaceAfter=15
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=8
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor('#00B894')
    )

    # Header Section
    story.append(Paragraph("LoanSphere Bank - EMI Amortization Schedule", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 10))

    # Summary Grid
    summary_data = [
        ["Loan Principal Amount:", f"INR {amount:,.2f}"],
        ["Annual Interest Rate:", f"{rate_annual:.2f}% p.a."],
        ["Loan Tenure:", f"{tenure} Months"],
        ["Monthly EMI Payment:", f"INR {emi:,.2f}"],
        ["Total Interest Payable:", f"INR {total_interest:,.2f}"],
        ["Total Amount Payable:", f"INR {total_payment:,.2f}"]
    ]

    t_summary = Table(summary_data, colWidths=[200, 300])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2D3748')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Amortization Schedule", header_style))

    # Schedule Table
    table_headers = ["Month", "EMI", "Principal Paid", "Interest Paid", "Balance Remaining"]
    schedule_data = [table_headers]

    remaining_balance = amount
    limit_tenure = min(tenure, 120)

    for m in range(1, tenure + 1):
        if rate_annual == 0:
            i_pay = 0
            p_pay = emi
        else:
            i_pay = remaining_balance * rate_monthly
            p_pay = emi - i_pay

        remaining_balance -= p_pay

        if m == tenure:
            p_pay += remaining_balance
            remaining_balance = 0

        if m <= limit_tenure:
            schedule_data.append([
                str(m),
                f"{emi:,.2f}",
                f"{p_pay:,.2f}",
                f"{i_pay:,.2f}",
                f"{max(0, remaining_balance):,.2f}"
            ])

    if tenure > 120:
        schedule_data.append(["...", "...", "...", "...", "..."])
        schedule_data.append([
            str(tenure),
            f"{emi:,.2f}",
            "Final Principal Paid",
            "Final Interest Paid",
            "0.00"
        ])

    t_schedule = Table(schedule_data, colWidths=[60, 110, 110, 110, 130])
    t_schedule.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0056D2')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_schedule)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(app):
    """
    Generates a secure in-memory PDF document for the loan application submission receipt.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0056D2'),
        spaceAfter=20
    )
    bold_style = ParagraphStyle(
        'ReceiptBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'ReceiptNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=6
    )

    story.append(Paragraph("LoanSphere Bank - Application Receipt", title_style))
    story.append(Paragraph(f"Application ID: {app.id}", bold_style))
    story.append(Paragraph(f"Date Submitted: {app.applied_at.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Paragraph(f"Application Status: {app.status}", bold_style))
    story.append(Spacer(1, 15))

    data = [
        ["Applicant Name", app.full_name],
        ["Email Address", app.email],
        ["Phone Number", app.phone],
        ["Loan Category", app.loan_type.name],
        ["Requested Loan Amount", f"INR {app.loan_amount:,.2f}"],
        ["Requested Tenure", f"{app.tenure_months} Months"],
        ["Occupation", app.occupation],
        ["Employer / Business Name", app.employer],
        ["Monthly Income", f"INR {app.monthly_income:,.2f}"],
        ["PAN Number", app.pan_number],
        ["Aadhar Number", app.aadhar_number]
    ]

    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))
    story.append(Paragraph("Thank you for choosing LoanSphere. We secure your dreams.", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
