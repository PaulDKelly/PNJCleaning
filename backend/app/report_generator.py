from fpdf import FPDF
from datetime import datetime
import os

class PNJReport(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pnj_blue = (2, 132, 199)
        self.dark_blue = (15, 23, 42)
        self.logo_path = r"E:\Code\Projects\PNJCleaning\backend\app\static\images\image_1.png"
        self.fsb_logo = r"E:\Code\Projects\PNJCleaning\backend\app\static\images\image_2.png"
        self.bics_logo = r"E:\Code\Projects\PNJCleaning\backend\app\static\images\image_23.png"

    def header(self):
        if self.page_no() == 1:
            if os.path.exists(self.logo_path):
                self.image(self.logo_path, 10, 10, 60)
            self.set_y(15)
            self.set_font('helvetica', 'B', 28)
            self.set_text_color(2, 132, 199)
            self.cell(0, 15, 'CERTIFICATE', ln=True, align='R')
            self.ln(25)
        else:
            self.set_fill_color(15, 23, 42)
            self.rect(0, 0, 210, 25, 'F')
            if os.path.exists(self.logo_path):
                self.image(self.logo_path, 10, 5, 25)
            self.set_y(5)
            self.set_text_color(255, 255, 255)
            self.set_font('helvetica', 'B', 14)
            self.cell(0, 10, 'KITCHEN EXTRACT SYSTEM AUDIT', ln=True, align='R')
            self.ln(15)

    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(100, 116, 139)
        if os.path.exists(self.fsb_logo):
            self.image(self.fsb_logo, 10, self.get_y(), 15)
        if os.path.exists(self.bics_logo):
            self.image(self.bics_logo, 30, self.get_y(), 15)
            
        self.set_x(0)
        self.cell(0, 10, f'Page {self.page_no()} | CONFIDENTIAL | PNJ Cleaners Limited', align='C')
        self.set_y(-15)
        self.cell(0, 10, 'Email: gary@pnjcleaning.co.uk | Office: +44 1283 791 953 | Mob: +44 758 512 7242', align='C')

def generate_client_pdf(report, micron_readings, inspection_items, filter_items, photos, output_path):
    pdf = PNJReport()
    pdf.set_auto_page_break(auto=True, margin=30)
    
    # --- PAGE 1: CERTIFICATE ---
    pdf.add_page()
    pdf.set_text_color(15, 23, 42)
    pdf.set_font('helvetica', '', 14)
    pdf.cell(0, 10, 'This is to certify that', ln=True)
    pdf.ln(2)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 15, f" {report.company}", ln=True, fill=True)
    pdf.set_font('helvetica', '', 11)
    pdf.cell(0, 8, f" {report.address}", ln=True, fill=True)
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 12)
    pdf.multi_cell(0, 7, "The areas listed below were cleaned and/or inspected by PNJ Cleaners Limited in accordance with BESA TR19 standards.")
    pdf.ln(5)

    # Certification Summary
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    cert_items = [
        ("Cooker canopies and Grease traps", "Compliant"),
        ("Extraction Ducting (accessible hatches)", "Compliant"),
        ("Extraction fan and housing", "Compliant"),
        ("Duct run / Riser", "Compliant")
    ]
    for el, stat in cert_items:
        pdf.cell(145, 10, f" {el}", border=1)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(45, 10, f" {stat}", border=1, ln=True, align='C')
        pdf.set_text_color(15, 23, 42)
    
    pdf.ln(10)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(20, 184, 166)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, f" NEXT CLEAN SCHEDULED: {report.risk_improvements or 'April 2026'}", ln=True, fill=True)
    pdf.set_text_color(15, 23, 42)
    
    pdf.ln(15)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(95, 8, 'Authorized Representative:', border='T')
    pdf.cell(95, 8, 'Date of Certification:', border='T', align='R', ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(95, 5, "Gary Kelly (Director)", ln=False)
    pdf.cell(95, 5, report.date.strftime('%d %B %Y'), align='R', ln=True)

    # --- PAGE 2: INTRODUCTION & AUDIT STANDARDS ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'Post Clean Inspection Report', ln=True)
    pdf.set_font('helvetica', 'I', 12)
    pdf.cell(0, 8, 'Kitchen Extract System Audit', ln=True)
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, 'Introduction', ln=True)
    pdf.set_font('helvetica', '', 9)
    intro_txt = (
        f"This report follows an inspection and system clean carried out by PNJ Cleaners Limited on behalf of {report.company}. "
        "The survey was conducted in accordance with recommendations set out in the following documents:\n\n"
        "- BS EN 15780:2011 Ventilation for Buildings - Ductwork - Cleanliness of Ventilation Systems\n"
        "- BESA TR19 Grease Guide to Good Practice Internal Cleanliness of Ventilation Systems\n"
        "- RC44 Recommendations for fire risk assessment of catering extract ventilation\n"
        "- HVCA DW/172: Specification for Kitchen Ventilation Systems (2005)\n"
        "- Health & Safety Act at Work 1974\n"
        "- The Regulatory Reform (Fire) Safety Order 2005\n\n"
        "The intention is to provide complete management and traceability of the Kitchen Extract Systems. "
        "Observations supported by photographs and Wet Film Thickness Test (WFTT) measurements taken provide an objective account of the "
        "condition of each extract installation."
    )
    pdf.multi_cell(0, 5, intro_txt)
    
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, 'Purpose & Fire Hazard', ln=True)
    pdf.set_font('helvetica', '', 9)
    purpose_txt = (
        "Kitchen extract systems present particular hazards. As well as removing odours and steam, the extract system "
        "removes greasy vapours which are an ignition source. Accumulated grease forms a hidden combustion load. "
        "Spontaneous ignition occurs at 310-360 deg C. Grease extract ductwork cleansing therefore helps reduce the "
        "flammable materials that build up within the system."
    )
    pdf.multi_cell(0, 5, purpose_txt)

    # --- PAGE 3: GUIDE TO GOOD PRACTICE SUMMARY ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'Guide to Good Practice Summary', ln=True)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, '1) Recommended Frequency of Cleaning (BESA TR19)', ln=True)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(60, 8, ' Use Level', border=1, fill=True)
    pdf.cell(70, 8, ' Cooking Hours', border=1, fill=True)
    pdf.cell(60, 8, ' Frequency', border=1, fill=True, ln=True)
    
    pdf.set_font('helvetica', '', 9)
    freqs = [("Heavy Use", "12-16 hours per day", "3 Monthly"), ("Moderate Use", "6-12 hours per day", "6 Monthly"), ("Low Use", "2-6 hours per day", "12 Monthly")]
    for a, b, c in freqs:
        pdf.cell(60, 8, f" {a}", border=1)
        pdf.cell(70, 8, f" {b}", border=1)
        pdf.cell(60, 8, f" {c}", border=1, ln=True)
    
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, '2) Acceptable Grease Deposit Levels (um)', ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, "BESA TR19 defines the following benchmarks for defining cleanliness and fire safety thresholds:")
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(100, 8, ' Measurement Criterion', border=1, fill=True)
    pdf.cell(90, 8, ' Recommended Action', border=1, fill=True, ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(100, 8, ' Average of 200 um cross-system', border=1)
    pdf.cell(90, 8, ' Complete system cleaning required', border=1, ln=True)
    pdf.cell(100, 8, ' Any single measurement > 500 um', border=1)
    pdf.cell(90, 8, ' Urgent Local Clean required', border=1, ln=True)
    pdf.cell(100, 8, ' Post-clean verification > 50 um', border=1)
    pdf.cell(90, 8, ' System re-clean required', border=1, ln=True)
    
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, '3) Risk Assessment Matrix', ln=True)
    risks = [
        (1, "Below 200 um. No outstanding issues in extraction system."),
        (2, "Averages below 200 um. Spot levels of over 200 um detected."),
        (3, "System averages over 200 um OR sections over 500 um."),
        (4, "Averages over 200 um AND sections over 500 um. Maintenance concerns."),
        (5, "Well above 200 um. Fan/filters in high-risk condition. Inaccessible areas."),
        (6, "Well above 500 um. Heavy build up > 1mm. Serious fire safety hazards.")
    ]
    for r_val, r_desc in risks:
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(15, 7, f" {r_val}", border=1, align='C')
        pdf.set_font('helvetica', '', 8)
        w_avail = pdf.w - pdf.l_margin - pdf.r_margin - 15
        pdf.multi_cell(w_avail, 7, f" {r_desc}", border=1)

    # --- PAGE 4: SYSTEM INSPECTION GRID ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'Extract Systems Inspection and Clean Report', ln=True)
    pdf.ln(3)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(50, 8, ' Client / Site:', border=1, fill=True)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(140, 8, f" {report.company} ({report.brand or '-'})", border=1, ln=True)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(50, 8, ' Risk Class (Pre):', border=1, fill=True)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(45, 8, f" Level {report.risk_pre or '-'}", border=1)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(50, 8, ' Risk Class (Post):', border=1, fill=True)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(45, 8, f" Level {report.risk_post or '-'}", border=1, ln=True)
    
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 10, 'Technical Audit Observations', ln=True)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(60, 8, ' Element', border=1, fill=True)
    pdf.cell(25, 8, ' Status', border=1, fill=True, align='C')
    pdf.cell(105, 8, ' Observation / Technical Advice', border=1, fill=True, ln=True)
    
    pdf.set_font('helvetica', '', 9)
    for item in inspection_items:
        obs_txt = f" {item.advice or '-'}"
        obs_w = 105
        lines = pdf.multi_cell(obs_w, 7, obs_txt, split_only=True)
        item_lines = pdf.multi_cell(60, 7, f" {item.item_name}", split_only=True)
        h = max(len(lines), len(item_lines)) * 7
        h = max(h, 7)
        
        if pdf.get_y() + h > 260: pdf.add_page()
        
        curr_y = pdf.get_y()
        curr_x = pdf.get_x()
        
        pdf.multi_cell(60, 7, f" {item.item_name}", border=1)
        next_y = pdf.get_y()
        
        pdf.set_xy(curr_x + 60, curr_y)
        status = "Compliant" if item.pass_status else ("Issue" if item.fail_status else "N/A")
        pdf.set_text_color(22, 163, 74) if status == "Compliant" else (pdf.set_text_color(185, 28, 28) if status == "Issue" else pdf.set_text_color(100, 116, 139))
        pdf.cell(25, h, status, border=1, align='C')
        pdf.set_text_color(15, 23, 42)
        
        pdf.set_xy(curr_x + 85, curr_y)
        pdf.multi_cell(obs_w, 7, obs_txt, border=1)
        obs_next_y = pdf.get_y()
        
        pdf.set_y(max(next_y, obs_next_y, curr_y + h))

    # --- PAGE 5: WFTT AUDIT DATA & RECOMMENDATIONS ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'WFTT Deposit Thickness Audit (um)', ln=True)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(20, 10, ' Point', border=1, fill=True, align='C')
    pdf.cell(100, 10, ' Location Description', border=1, fill=True)
    pdf.cell(35, 10, ' Pre-Clean', border=1, fill=True, align='C')
    pdf.cell(35, 10, ' Post-Clean', border=1, fill=True, align='C', ln=True)
    
    pdf.set_font('helvetica', '', 10)
    for m in micron_readings:
        pdf.cell(20, 8, f" {m.location}", border=1, align='C')
        pdf.cell(100, 8, f" {m.description}", border=1)
        pdf.cell(35, 8, f" {m.pre_clean or '-'}", border=1, align='C')
        pdf.set_text_color(22, 163, 74) if (m.post_clean or 0) <= 50 else pdf.set_text_color(185, 28, 28)
        pdf.cell(35, 8, f" {m.post_clean or '0'}", border=1, align='C', ln=True)
        pdf.set_text_color(15, 23, 42)
        
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, 'Summary of Remedial Requirements / Fire Risks:', ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.set_fill_color(255, 241, 242)
    pdf.multi_cell(0, 6, f"{report.remedial_requirements or 'No urgent remedial requirements identified.'}", border=1, fill=True)
    
    pdf.ln(3)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, 'Recommended Risk Improvements:', ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"{report.risk_improvements or 'Maintain regular cleaning schedule.'}", border=1)

    # --- PAGE 6: PHOTOGRAPHIC EVIDENCE ---
    if photos:
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, 'Photographic Evidence Archive', ln=True)
        pdf.ln(5)
        
        img_w = 85
        img_h = 55
        margin_x = 10
        margin_y = 15
        
        start_x = pdf.l_margin + 5
        start_y = pdf.get_y()
        
        for i, photo in enumerate(photos):
            page_idx = i % 4
            if i > 0 and page_idx == 0:
                pdf.add_page()
                start_y = 30
            
            col = page_idx % 2
            row = page_idx // 2
            
            x = start_x + (img_w + margin_x) * col
            y = start_y + (img_h + margin_y) * row
            
            if os.path.exists(photo.photo_path):
                pdf.image(photo.photo_path, x, y, img_w, img_h)
            else:
                pdf.rect(x, y, img_w, img_h)
                pdf.set_xy(x, y + img_h/2)
                pdf.cell(img_w, 10, '[Image Missing]', align='C')
            
            pdf.set_xy(x, y + img_h + 2)
            pdf.set_font('helvetica', 'B', 8)
            pdf.cell(img_w, 5, f"{photo.photo_type}: {photo.inspection_item or 'Observation Point'}", align='C')

    # --- PAGE 7: SYSTEM CLEAN SUMMARY & CHEMICALS ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'SYSTEM CLEANED SUMMARY', ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 10, ' Provide a brief description of the system cleaned:', border=1, fill=True, ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 8, f" {report.sketch_details or 'Main Extract System Clean'}", border=1)
    
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(140, 10, ' Has the entire system been cleaned? (TR19 Compliance)', border=1, fill=True)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(50, 10, ' YES' if report.status == "Approved" else ' Partial', border=1, ln=True, align='C')
    
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 10, ' If no, please record areas that do not comply and why:', border=1, fill=True, ln=True)
    pdf.set_font('helvetica', '', 10)
    non_compliance = "No. Attenuator not accessible." if "Attenuator" in (report.sketch_details or "") else "All areas accessible and cleaned."
    pdf.multi_cell(0, 8, f" {non_compliance}", border=1)
    
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 10, ' Chemicals used (attach DATA sheets):', border=1, fill=True, ln=True)
    pdf.set_font('helvetica', 'I', 10)
    pdf.cell(0, 10, ' Evans Lift A054 (MSDS attached)', border=1, ln=True)

    # --- PAGE 8: SCHEMATIC DRAWING REFERENCE ---
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'SCHEMATIC DRAWING REFERENCE', ln=True)
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(63, 10, ' 1. Testing Locations', border=1, fill=True, align='C')
    pdf.cell(63, 10, ' 2. Access Panels & Fans', border=1, fill=True, align='C')
    pdf.cell(64, 10, ' 3. Uncleaned Areas', border=1, fill=True, align='C', ln=True)
    
    pdf.rect(pdf.l_margin, pdf.get_y(), 190, 120)
    pdf.set_y(pdf.get_y() + 50)
    pdf.set_font('helvetica', 'I', 10)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, '[ Schematic Diagram Log Reference Only ]', align='C', ln=True)
    pdf.cell(0, 10, 'Drawing not to scale', align='C', ln=True)
    pdf.set_text_color(15, 23, 42)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path
