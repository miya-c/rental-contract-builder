from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    is_active = db.Column(db.Boolean(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contracts = relationship("Contract", back_populates="created_by")
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class RealEstateAgent(db.Model):
    """Real estate agent model (宅建士)"""
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    registration_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contracts = relationship("Contract", back_populates="agent")
    
    def __repr__(self):
        return f'<RealEstateAgent {self.name} ({self.license_number})>'

class Owner(db.Model):
    """Property owner model"""
    __tablename__ = 'owners'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buildings = relationship("Building", back_populates="owner")
    
    def __repr__(self):
        return f'<Owner {self.name}>'

class Building(db.Model):
    """Building information model"""
    __tablename__ = 'buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    
    # Structure information
    structure = db.Column(db.String(50), nullable=False)  # 木造, 鉄筋コンクリート造, etc.
    roof_structure = db.Column(db.String(50), nullable=True)  # 陸屋根, 瓦葺き, etc.
    floors = db.Column(db.Integer, nullable=False)  # Total number of floors
    total_units = db.Column(db.Integer, nullable=False)  # Total number of units
    building_type = db.Column(db.String(50), nullable=False)  # アパート, マンション, etc.
    construction_date = db.Column(db.Date, nullable=True)  # New construction date
    
    # Foreign key
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'), nullable=False)
    
    # Other fields
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("Owner", back_populates="buildings")
    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Building {self.name} ({self.address})>'

class Room(db.Model):
    """Room information model"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False)
    layout = db.Column(db.String(20), nullable=False)  # 1LDK, 2DK, etc.
    floor_area = db.Column(db.Float, nullable=False)  # In square meters
    floor = db.Column(db.Integer, nullable=False)  # Which floor the room is on
    
    # Amenities (Boolean flags)
    has_kitchen = db.Column(db.Boolean, default=False)
    has_toilet = db.Column(db.Boolean, default=False)
    has_bath = db.Column(db.Boolean, default=False)
    has_shower = db.Column(db.Boolean, default=False)
    has_washroom = db.Column(db.Boolean, default=False)
    has_hot_water = db.Column(db.Boolean, default=False)
    has_stove = db.Column(db.Boolean, default=False)
    has_air_conditioner = db.Column(db.Boolean, default=False)
    has_lighting = db.Column(db.Boolean, default=False)
    has_telephone = db.Column(db.Boolean, default=False)
    has_internet = db.Column(db.Boolean, default=False)
    has_fire_alarm = db.Column(db.Boolean, default=False)
    has_tv_connection = db.Column(db.Boolean, default=False)
    has_elevator_access = db.Column(db.Boolean, default=False)
    has_parking = db.Column(db.Boolean, default=False)
    has_bicycle_parking = db.Column(db.Boolean, default=False)
    has_private_garden = db.Column(db.Boolean, default=False)
    
    # Custom amenities (as JSON string)
    custom_amenities = db.Column(db.Text, nullable=True)  # Stored as JSON
    
    # Foreign key
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    
    # Other fields
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    building = relationship("Building", back_populates="rooms")
    contracts = relationship("Contract", back_populates="room")
    
    def __repr__(self):
        return f'<Room {self.room_number} in Building {self.building_id}>'

class ContractTemplate(db.Model):
    """Contract template model"""
    __tablename__ = 'contract_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_content = db.Column(db.Text, nullable=False)  # HTML/Template content
    file_type = db.Column(db.String(20), nullable=False, default='html')  # html, excel, word, pdf
    file_binary = db.Column(db.LargeBinary, nullable=True)  # For storing binary content
    file_name = db.Column(db.String(255), nullable=True)  # Original filename
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contracts = relationship("Contract", back_populates="template")
    
    def __repr__(self):
        return f'<ContractTemplate {self.name}>'

class SpecialTerm(db.Model):
    """Special terms that can be added to contracts"""
    __tablename__ = 'special_terms'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_common = db.Column(db.Boolean, default=False)  # If commonly used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SpecialTerm {self.title}>'

# Association table for Contract and SpecialTerm many-to-many relationship
contract_special_terms = db.Table(
    'contract_special_terms',
    db.Column('contract_id', db.Integer, db.ForeignKey('contracts.id'), primary_key=True),
    db.Column('special_term_id', db.Integer, db.ForeignKey('special_terms.id'), primary_key=True)
)

class Contract(db.Model):
    """Lease contract model"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    tenant_name = db.Column(db.String(100), nullable=False)
    tenant_address = db.Column(db.String(255), nullable=False)
    tenant_phone = db.Column(db.String(20), nullable=True)
    tenant_email = db.Column(db.String(120), nullable=True)
    
    # Contract details
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Null for indefinite term
    rent_amount = db.Column(db.Integer, nullable=False)  # Monthly rent in yen
    security_deposit = db.Column(db.Integer, nullable=True)
    key_money = db.Column(db.Integer, nullable=True)
    management_fee = db.Column(db.Integer, nullable=True)
    
    # Additional terms
    custom_special_terms = db.Column(db.Text, nullable=True)  # For free-form special terms
    
    # PDF file storage path (or content for PDFs generated on-the-fly)
    pdf_path = db.Column(db.String(255), nullable=True)
    
    # Foreign keys
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('contract_templates.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="contracts")
    agent = relationship("RealEstateAgent", back_populates="contracts")
    created_by = relationship("User", back_populates="contracts")
    template = relationship("ContractTemplate", back_populates="contracts")
    special_terms = db.relationship('SpecialTerm', secondary=contract_special_terms,
                                    lazy='subquery', backref=db.backref('contracts', lazy=True))
    
    def __repr__(self):
        return f'<Contract {self.contract_number} for {self.tenant_name}>'
