import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from crypto_engine.peks import get_public_key_fingerprint

def generate_credential_pdf(auditor, private_key=None, temporary_password=None, username=None):
    """
    Generates a secure credential PDF for the auditor.
    Returns bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name="DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_LEFT,
        spaceAfter=20
    )
    
    section_heading = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        name="BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    
    bold_body_style = ParagraphStyle(
        name="BoldBodyTextCustom",
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    
    mono_style = ParagraphStyle(
        name="MonospaceKey",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1e293b")
    )
    
    alert_style = ParagraphStyle(
        name="AlertText",
        parent=body_style,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#991b1b")
    )
    
    story = []
    
    # 1. Header with Logo & Meta
    header_data = [
        [
            Paragraph("<b>SECUREMATCH</b>", ParagraphStyle(
                name="LogoStyle",
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#1e3a8a")
            )),
            Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}<br/>Confidential", ParagraphStyle(
                name="HeaderDate",
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#64748b"),
                alignment=TA_CENTER
            ))
        ]
    ]
    header_table = Table(header_data, colWidths=[350, 150])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    
    # Divider line
    divider = Table([[""]], colWidths=[500], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))
    
    # 2. Document Title
    story.append(Paragraph("Cryptographic Identity & Credentials", title_style))
    story.append(Paragraph(
        "This document contains secure configuration and identity credentials for accessing the SecureMatch "
        "search portal. The public-private key pair generated below enables search signature validation.",
        subtitle_style
    ))
    
    # 3. Auditor & Credentials Table
    story.append(Paragraph("Identity Details", section_heading))
    
    # Determine values
    org = auditor.designation or "External Authority"
    auditor_name = auditor.name
    username_val = username or getattr(auditor, "username", None) or f"auditor_{auditor.id}"
    temp_pass_val = temporary_password or "******** [REDACTED]"
    portal_url = "http://localhost:5173/portal"
    creation_date = auditor.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(auditor, "created_at", None) else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    public_key_fp = get_public_key_fingerprint(auditor.public_key)
    
    details_data = [
        [Paragraph("<b>Auditor Name</b>", body_style), Paragraph(auditor_name, body_style)],
        [Paragraph("<b>Organization</b>", body_style), Paragraph(org, body_style)],
        [Paragraph("<b>Username</b>", bold_body_style), Paragraph(username_val, bold_body_style)],
        [Paragraph("<b>Temporary Password</b>", bold_body_style), Paragraph(temp_pass_val, ParagraphStyle(
            name="TempPass",
            parent=bold_body_style,
            textColor=colors.HexColor("#059669")
        ))],
        [Paragraph("<b>Portal URL</b>", body_style), Paragraph(portal_url, body_style)],
        [Paragraph("<b>Key Version</b>", body_style), Paragraph(str(auditor.key_version), body_style)],
        [Paragraph("<b>Key Fingerprint</b>", body_style), Paragraph(public_key_fp, mono_style)],
        [Paragraph("<b>Creation Date</b>", body_style), Paragraph(creation_date, body_style)],
    ]
    
    details_table = Table(details_data, colWidths=[150, 350])
    details_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))
    
    # 4. Public Key / Private Key Section
    story.append(Paragraph("Cryptographic Material", section_heading))
    
    keys_intro = (
        "Below is your registered Public Key. If a Private Key was generated in this transaction, "
        "it is shown in the portal one-time and must be stored in a secure location (e.g. key vault)."
    )
    story.append(Paragraph(keys_intro, body_style))
    story.append(Spacer(1, 5))
    
    # Public Key Display
    pub_key_para = Paragraph(auditor.public_key.replace("\n", "<br/>"), mono_style)
    pub_table = Table([[pub_key_para]], colWidths=[500])
    pub_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(pub_table)
    
    # Private Key Display (if provided)
    if private_key:
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Generated Private Key (KEEP SECURE - SHOWING ONCE)</b>", bold_body_style))
        story.append(Spacer(1, 5))
        priv_key_para = Paragraph(private_key.replace("\n", "<br/>"), mono_style)
        priv_table = Table([[priv_key_para]], colWidths=[500])
        priv_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fff1f2")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#fecdd3")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(priv_table)
        
    story.append(Spacer(1, 15))
    
    # 5. Security Instructions
    story.append(Paragraph("Critical Security Instructions", section_heading))
    instructions = (
        "1. <b>Private Key Confidentiality:</b> Never share your private key. SecureMatch administrators will never ask for it.<br/>"
        "2. <b>Signature Required:</b> To execute search queries, your local agent must sign the query using your private key.<br/>"
        "3. <b>Key Rotation:</b> If you suspect your key has been compromised, perform key rotation immediately via the portal.<br/>"
        "4. <b>Access Revocation:</b> Multiple signature failures or mismatching key versions will trigger automated account suspension."
    )
    
    instructions_table = Table([[Paragraph(instructions, alert_style)]], colWidths=[500])
    instructions_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#ef4444")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(instructions_table)
    
    # Build Document
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
