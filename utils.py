import os
import tempfile
import logging
from functools import wraps
from flask import render_template, flash, redirect, url_for
from flask_login import current_user
from jinja2 import Template
import weasyprint

from app import app, db
from models import Contract, Room, Building, Owner, RealEstateAgent, SpecialTerm, ContractTemplate

def require_admin(f):
    """Decorator to require admin role for a view"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('この操作を実行する権限がありません。', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_contract_data(contract_id):
    """Get all data needed for the contract PDF generation"""
    contract = Contract.query.get(contract_id)
    if not contract:
        logging.error(f"Contract with ID {contract_id} not found")
        return None
    
    room = Room.query.get(contract.room_id)
    if not room:
        logging.error(f"Room with ID {contract.room_id} not found")
        return None
    
    building = Building.query.get(room.building_id)
    if not building:
        logging.error(f"Building with ID {room.building_id} not found")
        return None
    
    owner = Owner.query.get(building.owner_id)
    if not owner:
        logging.error(f"Owner with ID {building.owner_id} not found")
        return None
    
    agent = RealEstateAgent.query.get(contract.agent_id)
    if not agent:
        logging.error(f"Agent with ID {contract.agent_id} not found")
        return None
    
    # Get all special terms for this contract
    special_terms = contract.special_terms
    
    # Parse custom amenities JSON
    custom_amenities = []
    if room.custom_amenities:
        try:
            import json
            custom_amenities = json.loads(room.custom_amenities)
        except json.JSONDecodeError:
            logging.error(f"Error parsing custom amenities JSON: {room.custom_amenities}")
    
    # Get the contract template
    template = ContractTemplate.query.get(contract.template_id)
    if not template:
        logging.error(f"Template with ID {contract.template_id} not found")
        return None
    
    return {
        'contract': contract,
        'room': room,
        'building': building,
        'owner': owner,
        'agent': agent,
        'special_terms': special_terms,
        'custom_amenities': custom_amenities,
        'template': template
    }

def generate_pdf(contract_id):
    """Generate a PDF for the contract and return the file path"""
    data = get_contract_data(contract_id)
    if not data:
        return None
    
    # Create a temporary directory for PDF generation
    pdf_dir = os.path.join(tempfile.gettempdir(), 'lease_contracts')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Create a filename for the PDF
    pdf_filename = f"contract_{data['contract'].contract_number}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    try:
        template = data['template']
        
        # Handle different template types
        if template.file_type == 'html':
            # HTML template - Use Jinja2 to render the HTML template
            template_content = template.file_content
            jinja_template = Template(template_content)
            html_content = jinja_template.render(
                contract=data['contract'],
                room=data['room'],
                building=data['building'],
                owner=data['owner'],
                agent=data['agent'],
                special_terms=data['special_terms'],
                custom_amenities=data['custom_amenities']
            )
            
            # Generate PDF with WeasyPrint
            weasyprint.HTML(string=html_content).write_pdf(pdf_path)
            
        elif template.file_type == 'excel':
            # Excel template
            from io import BytesIO
            import openpyxl
            
            # Load the Excel template
            if not template.file_binary:
                logging.error("Excel template has no binary data")
                return None
            
            workbook = openpyxl.load_workbook(BytesIO(template.file_binary))
            sheet = workbook.active
            
            # Fill in the Excel template with contract data
            # This is a basic implementation - customize as needed
            replace_dict = {
                '{{contract.contract_number}}': data['contract'].contract_number,
                '{{contract.tenant_name}}': data['contract'].tenant_name,
                '{{contract.tenant_address}}': data['contract'].tenant_address,
                '{{owner.name}}': data['owner'].name,
                '{{owner.address}}': data['owner'].address,
                '{{building.name}}': data['building'].name,
                '{{building.address}}': data['building'].address,
                '{{room.room_number}}': data['room'].room_number,
                '{{contract.rent_amount}}': str(data['contract'].rent_amount),
                '{{agent.name}}': data['agent'].name,
                '{{agent.license_number}}': data['agent'].license_number,
            }
            
            # Replace placeholders in all cells
            for row in sheet.rows:
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        for placeholder, value in replace_dict.items():
                            if placeholder in cell.value:
                                cell.value = cell.value.replace(placeholder, value)
            
            # Save to a temporary Excel file
            excel_path = os.path.join(pdf_dir, f"contract_{data['contract'].contract_number}.xlsx")
            workbook.save(excel_path)
            
            # Convert Excel to PDF (simplified - actual implementation would need external library)
            # For now, just copy the Excel file
            import shutil
            shutil.copy(excel_path, pdf_path)
            
        elif template.file_type == 'word':
            # Word template
            from io import BytesIO
            import docx
            from docx.shared import Pt
            
            # Load the Word template
            if not template.file_binary:
                logging.error("Word template has no binary data")
                return None
                
            doc = docx.Document(BytesIO(template.file_binary))
            
            # Fill in the Word template with contract data
            # This is a basic implementation - customize as needed
            replace_dict = {
                '{{contract.contract_number}}': data['contract'].contract_number,
                '{{contract.tenant_name}}': data['contract'].tenant_name,
                '{{contract.tenant_address}}': data['contract'].tenant_address,
                '{{owner.name}}': data['owner'].name,
                '{{owner.address}}': data['owner'].address,
                '{{building.name}}': data['building'].name,
                '{{building.address}}': data['building'].address,
                '{{room.room_number}}': data['room'].room_number,
                '{{contract.rent_amount}}': str(data['contract'].rent_amount),
                '{{agent.name}}': data['agent'].name,
                '{{agent.license_number}}': data['agent'].license_number,
            }
            
            # Replace placeholders in paragraphs
            for para in doc.paragraphs:
                for placeholder, value in replace_dict.items():
                    if placeholder in para.text:
                        para.text = para.text.replace(placeholder, value)
            
            # Replace placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            for placeholder, value in replace_dict.items():
                                if placeholder in para.text:
                                    para.text = para.text.replace(placeholder, value)
            
            # Save to a temporary Word file
            docx_path = os.path.join(pdf_dir, f"contract_{data['contract'].contract_number}.docx")
            doc.save(docx_path)
            
            # Convert Word to PDF (simplified - actual implementation would need external library)
            # For now, just copy the Word file
            import shutil
            shutil.copy(docx_path, pdf_path)
            
        elif template.file_type == 'pdf':
            # PDF template - use PyPDF2 to manipulate the PDF if needed
            # For now, just copy the PDF template
            from io import BytesIO
            import PyPDF2
            
            # Load the PDF template
            if not template.file_binary:
                logging.error("PDF template has no binary data")
                return None
                
            # For now, just save the PDF as is
            with open(pdf_path, 'wb') as f:
                f.write(template.file_binary)
                
        else:
            logging.error(f"Unsupported template type: {template.file_type}")
            return None
            
        return pdf_path
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return None
