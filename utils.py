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
        # Prepare HTML content from template
        template_content = data['template'].file_content
        
        # Use Jinja2 to render the template with contract data
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
        
        return pdf_path
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return None
