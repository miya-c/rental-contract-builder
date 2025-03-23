import os
import json
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app import app, db
from models import User, RealEstateAgent, Owner, Building, Room, Contract
from models import ContractTemplate, SpecialTerm, contract_special_terms
from forms import LoginForm, UserForm, RealEstateAgentForm, OwnerForm, BuildingForm
from forms import RoomForm, ContractForm, SpecialTermForm, ContractTemplateForm
from utils import generate_pdf, require_admin


# Route for the home page
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash,
                                        form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('ユーザー名またはパスワードが正しくありません。', 'danger')

    return render_template('login.html', form=form)


# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))


# Route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Get counts for dashboard statistics
    contracts_count = Contract.query.count()
    buildings_count = Building.query.count()
    rooms_count = Room.query.count()
    owners_count = Owner.query.count()

    # Get recent contracts
    recent_contracts = Contract.query.order_by(
        Contract.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           contracts_count=contracts_count,
                           buildings_count=buildings_count,
                           rooms_count=rooms_count,
                           owners_count=owners_count,
                           recent_contracts=recent_contracts)


# ========== User Management Routes ==========


@app.route('/admin/users')
@login_required
@require_admin
def user_management():
    users = User.query.all()
    return render_template('admin/user_management.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@require_admin
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('そのユーザー名は既に使用されています。', 'danger')
            return render_template('admin/add_user.html', form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash('そのメールアドレスは既に使用されています。', 'danger')
            return render_template('admin/add_user.html', form=form)

        # Create new user
        user = User(username=form.username.data,
                    email=form.email.data,
                    password_hash=generate_password_hash(form.password.data),
                    role=form.role.data,
                    is_active=form.is_active.data)
        db.session.add(user)
        db.session.commit()

        flash('ユーザーが追加されました。', 'success')
        return redirect(url_for('user_management'))

    return render_template('admin/add_user.html', form=form)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_admin
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)

    # Remove password validation for edit form
    form.password.validators = []
    form.confirm_password.validators = []

    if form.validate_on_submit():
        # Check if username is changed and already exists
        if form.username.data != user.username and User.query.filter_by(
                username=form.username.data).first():
            flash('そのユーザー名は既に使用されています。', 'danger')
            return render_template('admin/edit_user.html',
                                   form=form,
                                   user=user)

        # Check if email is changed and already exists
        if form.email.data != user.email and User.query.filter_by(
                email=form.email.data).first():
            flash('そのメールアドレスは既に使用されています。', 'danger')
            return render_template('admin/edit_user.html',
                                   form=form,
                                   user=user)

        # Update user details
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data

        # Update password if provided
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()
        flash('ユーザー情報が更新されました。', 'success')
        return redirect(url_for('user_management'))

    return render_template('admin/edit_user.html', form=form, user=user)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@require_admin
def delete_user(user_id):
    if current_user.id == user_id:
        flash('自分自身を削除することはできません。', 'danger')
        return redirect(url_for('user_management'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('ユーザーが削除されました。', 'success')
    return redirect(url_for('user_management'))


# ========== Real Estate Agent Routes ==========


@app.route('/agents')
@login_required
def agent_list():
    agents = RealEstateAgent.query.all()
    return render_template('agents/list.html', agents=agents)


@app.route('/agents/add', methods=['GET', 'POST'])
@login_required
def add_agent():
    form = RealEstateAgentForm()
    if form.validate_on_submit():
        agent = RealEstateAgent(name=form.name.data,
                                license_number=form.license_number.data,
                                registration_date=form.registration_date.data,
                                notes=form.notes.data)
        db.session.add(agent)
        db.session.commit()

        flash('宅建士が追加されました。', 'success')
        return redirect(url_for('agent_list'))

    return render_template('agents/add.html', form=form)


@app.route('/agents/edit/<int:agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
    agent = RealEstateAgent.query.get_or_404(agent_id)
    form = RealEstateAgentForm(obj=agent)
    form.id.data = agent.id

    if form.validate_on_submit():
        agent.name = form.name.data
        agent.license_number = form.license_number.data
        agent.registration_date = form.registration_date.data
        agent.notes = form.notes.data

        db.session.commit()
        flash('宅建士情報が更新されました。', 'success')
        return redirect(url_for('agent_list'))

    return render_template('agents/edit.html', form=form, agent=agent)


@app.route('/agents/delete/<int:agent_id>', methods=['POST'])
@login_required
def delete_agent(agent_id):
    agent = RealEstateAgent.query.get_or_404(agent_id)

    # Check if agent is used in any contracts
    if agent.contracts:
        flash('契約で使用されている宅建士は削除できません。', 'danger')
        return redirect(url_for('agent_list'))

    db.session.delete(agent)
    db.session.commit()

    flash('宅建士が削除されました。', 'success')
    return redirect(url_for('agent_list'))


# ========== Owner Routes ==========


@app.route('/owners')
@login_required
def owner_list():
    owners = Owner.query.all()
    return render_template('owners/list.html', owners=owners)


@app.route('/owners/add', methods=['GET', 'POST'])
@login_required
def add_owner():
    form = OwnerForm()
    if form.validate_on_submit():
        owner = Owner(name=form.name.data,
                      address=form.address.data,
                      phone=form.phone.data,
                      email=form.email.data,
                      notes=form.notes.data)
        db.session.add(owner)
        db.session.commit()

        flash('オーナーが追加されました。', 'success')
        return redirect(url_for('owner_list'))

    return render_template('owners/add.html', form=form)


@app.route('/owners/edit/<int:owner_id>', methods=['GET', 'POST'])
@login_required
def edit_owner(owner_id):
    owner = Owner.query.get_or_404(owner_id)
    form = OwnerForm(obj=owner)
    form.id.data = owner.id

    if form.validate_on_submit():
        owner.name = form.name.data
        owner.address = form.address.data
        owner.phone = form.phone.data
        owner.email = form.email.data
        owner.notes = form.notes.data

        db.session.commit()
        flash('オーナー情報が更新されました。', 'success')
        return redirect(url_for('owner_list'))

    return render_template('owners/edit.html', form=form, owner=owner)


@app.route('/owners/delete/<int:owner_id>', methods=['POST'])
@login_required
def delete_owner(owner_id):
    owner = Owner.query.get_or_404(owner_id)

    # Check if owner has buildings
    if owner.buildings:
        flash('建物が登録されているオーナーは削除できません。', 'danger')
        return redirect(url_for('owner_list'))

    db.session.delete(owner)
    db.session.commit()

    flash('オーナーが削除されました。', 'success')
    return redirect(url_for('owner_list'))


# ========== Building Routes ==========


@app.route('/buildings')
@login_required
def building_list():
    buildings = Building.query.all()
    return render_template('buildings/list.html', buildings=buildings)


@app.route('/buildings/add', methods=['GET', 'POST'])
@login_required
def add_building():
    form = BuildingForm()
    if form.validate_on_submit():
        # Handle custom structure if 'other' is selected
        structure = form.structure.data
        if structure == 'その他' and form.custom_structure.data:
            structure = form.custom_structure.data

        # Handle custom roof structure if 'other' is selected
        roof_structure = form.roof_structure.data
        if roof_structure == 'その他' and form.custom_roof_structure.data:
            roof_structure = form.custom_roof_structure.data

        # Handle custom building type if 'other' is selected
        building_type = form.building_type.data
        if building_type == 'その他' and form.custom_building_type.data:
            building_type = form.custom_building_type.data

        building = Building(name=form.name.data,
                            address=form.address.data,
                            structure=structure,
                            roof_structure=roof_structure,
                            floors=form.floors.data,
                            total_units=form.total_units.data,
                            building_type=building_type,
                            construction_date=form.construction_date.data,
                            notes=form.notes.data,
                            owner_id=form.owner_id.data)
        db.session.add(building)
        db.session.commit()

        flash('建物が追加されました。', 'success')
        return redirect(url_for('building_list'))

    return render_template('buildings/add.html', form=form)


@app.route('/buildings/edit/<int:building_id>', methods=['GET', 'POST'])
@login_required
def edit_building(building_id):
    building = Building.query.get_or_404(building_id)
    form = BuildingForm(obj=building)
    form.id.data = building.id

    # Set custom fields if the value is not in predefined choices
    structure_values = [choice[0] for choice in form.structure.choices]
    if building.structure not in structure_values:
        form.structure.data = 'その他'
        form.custom_structure.data = building.structure

    roof_structure_values = [
        choice[0] for choice in form.roof_structure.choices
    ]
    if building.roof_structure and building.roof_structure not in roof_structure_values:
        form.roof_structure.data = 'その他'
        form.custom_roof_structure.data = building.roof_structure

    building_type_values = [choice[0] for choice in form.building_type.choices]
    if building.building_type not in building_type_values:
        form.building_type.data = 'その他'
        form.custom_building_type.data = building.building_type

    if form.validate_on_submit():
        # Handle custom structure if 'other' is selected
        structure = form.structure.data
        if structure == 'その他' and form.custom_structure.data:
            structure = form.custom_structure.data

        # Handle custom roof structure if 'other' is selected
        roof_structure = form.roof_structure.data
        if roof_structure == 'その他' and form.custom_roof_structure.data:
            roof_structure = form.custom_roof_structure.data

        # Handle custom building type if 'other' is selected
        building_type = form.building_type.data
        if building_type == 'その他' and form.custom_building_type.data:
            building_type = form.custom_building_type.data

        building.name = form.name.data
        building.address = form.address.data
        building.structure = structure
        building.roof_structure = roof_structure
        building.floors = form.floors.data
        building.total_units = form.total_units.data
        building.building_type = building_type
        building.construction_date = form.construction_date.data
        building.notes = form.notes.data
        building.owner_id = form.owner_id.data

        db.session.commit()
        flash('建物情報が更新されました。', 'success')
        return redirect(url_for('building_list'))

    return render_template('buildings/edit.html', form=form, building=building)


@app.route('/buildings/view/<int:building_id>')
@login_required
def view_building(building_id):
    building = Building.query.get_or_404(building_id)
    rooms = Room.query.filter_by(building_id=building_id).all()
    return render_template('buildings/view.html',
                           building=building,
                           rooms=rooms)


@app.route('/buildings/delete/<int:building_id>', methods=['POST'])
@login_required
def delete_building(building_id):
    building = Building.query.get_or_404(building_id)

    # Check if building has rooms
    if building.rooms:
        flash('部屋が登録されている建物は削除できません。', 'danger')
        return redirect(url_for('building_list'))

    db.session.delete(building)
    db.session.commit()

    flash('建物が削除されました。', 'success')
    return redirect(url_for('building_list'))


# ========== Room Routes ==========


@app.route('/rooms/add/<int:building_id>', methods=['GET', 'POST'])
@login_required
def add_room(building_id):
    building = Building.query.get_or_404(building_id)
    form = RoomForm()
    form.building_id.data = building_id

    if form.validate_on_submit():
        # Convert custom amenities to JSON
        custom_amenities = []
        if form.custom_amenities.data:
            custom_amenities = [
                item.strip() for item in form.custom_amenities.data.split(',')
                if item.strip()
            ]

        room = Room(room_number=form.room_number.data,
                    layout=form.layout.data,
                    floor_area=form.floor_area.data,
                    floor=form.floor.data,
                    has_kitchen=form.has_kitchen.data,
                    has_toilet=form.has_toilet.data,
                    has_bath=form.has_bath.data,
                    has_shower=form.has_shower.data,
                    has_washroom=form.has_washroom.data,
                    has_hot_water=form.has_hot_water.data,
                    has_stove=form.has_stove.data,
                    has_air_conditioner=form.has_air_conditioner.data,
                    has_lighting=form.has_lighting.data,
                    has_telephone=form.has_telephone.data,
                    has_internet=form.has_internet.data,
                    has_fire_alarm=form.has_fire_alarm.data,
                    has_tv_connection=form.has_tv_connection.data,
                    has_elevator_access=form.has_elevator_access.data,
                    has_parking=form.has_parking.data,
                    has_bicycle_parking=form.has_bicycle_parking.data,
                    has_private_garden=form.has_private_garden.data,
                    custom_amenities=json.dumps(custom_amenities)
                    if custom_amenities else None,
                    notes=form.notes.data,
                    building_id=building_id)
        db.session.add(room)
        db.session.commit()

        flash('部屋情報が追加されました。', 'success')
        return redirect(url_for('view_building', building_id=building_id))

    return render_template('rooms/add.html', form=form, building=building)


@app.route('/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    form.id.data = room.id

    # Set custom amenities as comma-separated list
    if room.custom_amenities:
        try:
            custom_amenities_list = json.loads(room.custom_amenities)
            form.custom_amenities.data = ', '.join(custom_amenities_list)
        except json.JSONDecodeError:
            form.custom_amenities.data = room.custom_amenities

    if form.validate_on_submit():
        # Convert custom amenities to JSON
        custom_amenities = []
        if form.custom_amenities.data:
            custom_amenities = [
                item.strip() for item in form.custom_amenities.data.split(',')
                if item.strip()
            ]

        room.room_number = form.room_number.data
        room.layout = form.layout.data
        room.floor_area = form.floor_area.data
        room.floor = form.floor.data
        room.has_kitchen = form.has_kitchen.data
        room.has_toilet = form.has_toilet.data
        room.has_bath = form.has_bath.data
        room.has_shower = form.has_shower.data
        room.has_washroom = form.has_washroom.data
        room.has_hot_water = form.has_hot_water.data
        room.has_stove = form.has_stove.data
        room.has_air_conditioner = form.has_air_conditioner.data
        room.has_lighting = form.has_lighting.data
        room.has_telephone = form.has_telephone.data
        room.has_internet = form.has_internet.data
        room.has_fire_alarm = form.has_fire_alarm.data
        room.has_tv_connection = form.has_tv_connection.data
        room.has_elevator_access = form.has_elevator_access.data
        room.has_parking = form.has_parking.data
        room.has_bicycle_parking = form.has_bicycle_parking.data
        room.has_private_garden = form.has_private_garden.data
        room.custom_amenities = json.dumps(
            custom_amenities) if custom_amenities else None
        room.notes = form.notes.data
        room.building_id = form.building_id.data

        db.session.commit()
        flash('部屋情報が更新されました。', 'success')
        return redirect(url_for('view_building', building_id=room.building_id))

    return render_template('rooms/edit.html', form=form, room=room)


@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    building_id = room.building_id

    # Check if room is used in any contracts
    if room.contracts:
        flash('契約で使用されている部屋は削除できません。', 'danger')
        return redirect(url_for('view_building', building_id=building_id))

    db.session.delete(room)
    db.session.commit()

    flash('部屋情報が削除されました。', 'success')
    return redirect(url_for('view_building', building_id=building_id))


# ========== Special Terms Routes ==========


@app.route('/special-terms')
@login_required
def special_term_list():
    terms = SpecialTerm.query.all()
    return render_template('special_terms/list.html', terms=terms)


@app.route('/special-terms/add', methods=['GET', 'POST'])
@login_required
def add_special_term():
    form = SpecialTermForm()
    if form.validate_on_submit():
        term = SpecialTerm(title=form.title.data,
                           content=form.content.data,
                           is_common=form.is_common.data)
        db.session.add(term)
        db.session.commit()

        flash('特約条項が追加されました。', 'success')
        return redirect(url_for('special_term_list'))

    return render_template('special_terms/add.html', form=form)


@app.route('/special-terms/edit/<int:term_id>', methods=['GET', 'POST'])
@login_required
def edit_special_term(term_id):
    term = SpecialTerm.query.get_or_404(term_id)
    form = SpecialTermForm(obj=term)
    form.id.data = term.id

    if form.validate_on_submit():
        term.title = form.title.data
        term.content = form.content.data
        term.is_common = form.is_common.data

        db.session.commit()
        flash('特約条項が更新されました。', 'success')
        return redirect(url_for('special_term_list'))

    return render_template('special_terms/edit.html', form=form, term=term)


@app.route('/special-terms/delete/<int:term_id>', methods=['POST'])
@login_required
def delete_special_term(term_id):
    term = SpecialTerm.query.get_or_404(term_id)

    # Remove term from all contracts
    stmt = contract_special_terms.delete().where(
        contract_special_terms.c.special_term_id == term_id)
    db.session.execute(stmt)

    db.session.delete(term)
    db.session.commit()

    flash('特約条項が削除されました。', 'success')
    return redirect(url_for('special_term_list'))


# ========== Contract Template Routes ==========


@app.route('/templates')
@login_required
def template_list():
    templates = ContractTemplate.query.all()
    return render_template('templates/list.html', templates=templates)


@app.route('/templates/add', methods=['GET', 'POST'])
@login_required
def add_template():
    form = ContractTemplateForm()
    if form.validate_on_submit():
        file_content = ''
        file_binary = None
        file_name = None

        # Handle different file types
        if form.file_type.data == 'html':
            # For HTML templates, use the text content provided
            file_content = form.file_content.data

            # If a template file is uploaded, read its contents
            if form.template_file.data:
                try:
                    file_content = form.template_file.data.read().decode(
                        'utf-8')
                    file_name = secure_filename(
                        form.template_file.data.filename)
                except UnicodeDecodeError:
                    flash('HTMLファイルはUTF-8でエンコードされている必要があります。', 'danger')
                    return render_template('templates/add.html', form=form)
        else:
            # For non-HTML templates (Excel, Word, PDF), store the binary content
            if form.template_file.data:
                file_binary = form.template_file.data.read()
                file_name = secure_filename(form.template_file.data.filename)

                # Set a placeholder for the file_content field
                if form.file_type.data == 'excel':
                    file_content = 'Excel Template'
                elif form.file_type.data == 'word':
                    file_content = 'Word Template'
                elif form.file_type.data == 'pdf':
                    file_content = 'PDF Template'

        # If this is set as default, unset other default templates
        if form.is_default.data:
            default_templates = ContractTemplate.query.filter_by(
                is_default=True).all()
            for template in default_templates:
                template.is_default = False

        template = ContractTemplate(name=form.name.data,
                                    description=form.description.data,
                                    file_content=file_content,
                                    file_type=form.file_type.data,
                                    file_binary=file_binary,
                                    file_name=file_name,
                                    is_default=form.is_default.data)
        db.session.add(template)
        db.session.commit()

        flash('契約書テンプレートが追加されました。', 'success')
        return redirect(url_for('template_list'))

    return render_template('templates/add.html', form=form)


# @app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
# @login_required
# def edit_template(template_id):
#     template = ContractTemplate.query.get_or_404(template_id)
#     form = ContractTemplateForm(obj=template)
#     form.id.data = template.id

#     if form.validate_on_submit():
#         file_content = form.file_content.data
#         file_binary = None
#         file_name = None

#         # Handle different file types
#         if form.file_type.data == 'html':
#             # For HTML templates, use the text content provided
#             if form.template_file.data:
#                 try:
#                     file_content = form.template_file.data.read().decode('utf-8')
#                     file_name = secure_filename(form.template_file.data.filename)
#                     file_binary = None  # Clear binary data when switching to HTML
#                 except UnicodeDecodeError:
#                     flash('HTMLファイルはUTF-8でエンコードされている必要があります。', 'danger')
#                     return render_template('templates/edit.html', form=form, template=template)
#         else:
#             # For non-HTML templates (Excel, Word, PDF), store the binary content
#             if form.template_file.data:
#                 file_binary = form.template_file.data.read()
#                 file_name = secure_filename(form.template_file.data.filename)

#                 # Set a placeholder for the file_content field
#                 if form.file_type.data == 'excel':
#                     file_content = 'Excel Template'
#                 elif form.file_type.data == 'word':
#                     file_content = 'Word Template'
#                 elif form.file_type.data == 'pdf':
#                     file_content = 'PDF Template'

#         # If this is set as default, unset other default templates
#         if form.is_default.data and not template.is_default:
#             default_templates = ContractTemplate.query.filter_by(is_default=True).all()
#             for t in default_templates:
#                 t.is_default = False

#         template.name = form.name.data
#         template.description = form.description.data
#         template.file_content = file_content
#         template.file_type = form.file_type.data
#         template.file_binary = file_binary
#         template.file_name = file_name
#         template.is_default = form.is_default.data

#         db.session.commit()
#         flash('契約書テンプレートが更新されました。', 'success')
#         return redirect(url_for('template_list'))
#     # building オブジェクトを取得する
#     building = None
#     if hasattr(template, 'building'):  # buildingを取得
#         building = template.building
#     # owner を取得するためのロジックを追加します。
#     owner = None
#     if hasattr(building, 'owner'):
#         owner = building.owner
#     # テンプレートをレンダリングする際に 'contract', 'building', 'owner' を追加する
#     return render_template('templates/edit.html', form=form, template=template, contract=template, building=building, owner=owner)


@app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    template = ContractTemplate.query.get_or_404(template_id)
    form = ContractTemplateForm(obj=template)
    form.id.data = template.id

    if form.validate_on_submit():
        file_content = form.file_content.data
        file_binary = None
        file_name = None

        db.session.commit()
        flash('契約書テンプレートが更新されました。', 'success')
        return redirect(url_for('template_list'))

    # building オブジェクトを取得する
    building = None
    if hasattr(template, 'building'):
        building = template.building

    # room を取得するためのロジックを追加
    room = None
    if hasattr(template, 'room'):
        room = template.room

    # owner を取得するためのロジックを追加
    owner = None
    if hasattr(building, 'owner'):
        owner = building.owner

    # agent を取得するためのロジックを追加
    agent = None
    if hasattr(template, 'agent'):
        agent = template.agent

    # テンプレートをレンダリングする際に 'contract', 'building', 'owner', 'room', 'agent' を追加する
    return render_template('templates/edit.html',
                           form=form,
                           template=template,
                           contract=template,
                           building=building,
                           owner=owner,
                           room=room,
                           agent=agent)


@app.route('/templates/download/<int:template_id>')
@login_required
def download_template(template_id):
    template = ContractTemplate.query.get_or_404(template_id)

    # Check if template is binary type
    if template.file_type == 'html':
        flash('HTMLテンプレートはダウンロードできません。', 'warning')
        return redirect(url_for('template_list'))

    if not template.file_binary or not template.file_name:
        flash('テンプレートファイルが見つかりませんでした。', 'danger')
        return redirect(url_for('template_list'))

    # Create temporary file and save binary content
    from io import BytesIO
    file_data = BytesIO(template.file_binary)

    # Determine MIME type
    mimetype = None
    if template.file_type == 'excel':
        if template.file_name.endswith('.xlsx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'application/vnd.ms-excel'
    elif template.file_type == 'word':
        if template.file_name.endswith('.docx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            mimetype = 'application/msword'
    elif template.file_type == 'pdf':
        mimetype = 'application/pdf'

    return send_file(file_data,
                     mimetype=mimetype,
                     as_attachment=True,
                     download_name=template.file_name)


@app.route('/templates/delete/<int:template_id>', methods=['POST'])
@login_required
def delete_template(template_id):
    template = ContractTemplate.query.get_or_404(template_id)

    # Check if template is used in any contracts
    if template.contracts:
        flash('契約で使用されているテンプレートは削除できません。', 'danger')
        return redirect(url_for('template_list'))

    db.session.delete(template)
    db.session.commit()

    flash('契約書テンプレートが削除されました。', 'success')
    return redirect(url_for('template_list'))


# ========== Contract Routes ==========


@app.route('/contracts')
@login_required
def contract_list():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return render_template('contracts/list.html', contracts=contracts)


@app.route('/contracts/create', methods=['GET', 'POST'])
@login_required
def create_contract():
    form = ContractForm()

    # If no templates exist, redirect to create one
    if not form.template_id.choices:
        flash('契約書を作成するにはテンプレートが必要です。新しいテンプレートを作成してください。', 'warning')
        return redirect(url_for('add_template'))

    if form.validate_on_submit():
        # Generate a unique contract number
        current_date = datetime.now().strftime('%Y%m%d')
        count = Contract.query.filter(
            Contract.contract_number.like(f"{current_date}%")).count() + 1
        contract_number = f"{current_date}-{count:04d}"

        # Create the contract
        contract = Contract(
            contract_number=contract_number,
            tenant_name=form.tenant_name.data,
            tenant_address=form.tenant_address.data,
            tenant_phone=form.tenant_phone.data,
            tenant_email=form.tenant_email.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            rent_amount=form.rent_amount.data,
            security_deposit=form.security_deposit.data,
            key_money=form.key_money.data,
            management_fee=form.management_fee.data,
            custom_special_terms=form.custom_special_terms.data,
            room_id=form.room_id.data,
            agent_id=form.agent_id.data,
            created_by_id=current_user.id,
            template_id=form.template_id.data)
        db.session.add(contract)

        # Add selected special terms
        if form.special_terms.data:
            for term_id in form.special_terms.data:
                term = SpecialTerm.query.get(term_id)
                if term:
                    contract.special_terms.append(term)

        db.session.commit()

        # Generate PDF and store its path
        pdf_path = generate_pdf(contract.id)
        if pdf_path:
            contract.pdf_path = pdf_path
            db.session.commit()
            flash('契約書が作成されました。', 'success')
            return redirect(url_for('view_contract', contract_id=contract.id))
        else:
            flash('PDFの生成中にエラーが発生しました。契約は保存されましたが、PDFを再生成してください。', 'warning')
            return redirect(url_for('view_contract', contract_id=contract.id))

    return render_template('contracts/create.html', form=form)


@app.route('/contracts/view/<int:contract_id>')
@login_required
def view_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contracts/view.html', contract=contract)


@app.route('/contracts/pdf/<int:contract_id>')
@login_required
def download_contract_pdf(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if not contract.pdf_path or not os.path.exists(contract.pdf_path):
        # Generate or regenerate PDF
        pdf_path = generate_pdf(contract_id)
        if not pdf_path:
            flash('PDFの生成中にエラーが発生しました。', 'danger')
            return redirect(url_for('view_contract', contract_id=contract_id))

        contract.pdf_path = pdf_path
        db.session.commit()

    # Set a filename for the download
    filename = f"lease_contract_{contract.contract_number}.pdf"
    return send_file(contract.pdf_path,
                     as_attachment=True,
                     download_name=filename)


@app.route('/contracts/original/<int:contract_id>')
@login_required
def download_contract_original(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if not contract.original_file_path or not os.path.exists(contract.original_file_path):
        flash('元のファイルが見つかりませんでした。', 'danger')
        return redirect(url_for('view_contract', contract_id=contract_id))

    # Get the file extension and determine the correct MIME type
    file_ext = os.path.splitext(contract.original_file_path)[1].lower()
    
    # Set mime type based on file extension
    mimetype = None
    if file_ext in ['.xlsx', '.xls']:
        if file_ext == '.xlsx':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'application/vnd.ms-excel'
        filename = f"lease_contract_{contract.contract_number}{file_ext}"
    elif file_ext in ['.docx', '.doc']:
        if file_ext == '.docx':
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            mimetype = 'application/msword'
        filename = f"lease_contract_{contract.contract_number}{file_ext}"
    elif file_ext == '.pdf':
        mimetype = 'application/pdf'
        filename = f"lease_contract_{contract.contract_number}.pdf"
    else:
        mimetype = 'application/octet-stream'
        filename = f"lease_contract_{contract.contract_number}{file_ext}"

    return send_file(contract.original_file_path,
                     mimetype=mimetype,
                     as_attachment=True,
                     download_name=filename)


@app.route('/contracts/regenerate-pdf/<int:contract_id>', methods=['POST'])
@login_required
def regenerate_contract_pdf(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    # Delete the old PDF file if it exists
    if contract.pdf_path and os.path.exists(contract.pdf_path):
        try:
            os.remove(contract.pdf_path)
        except OSError as e:
            logging.error(f"Error deleting PDF file: {e}")

    # Generate new PDF
    pdf_path = generate_pdf(contract_id)
    if pdf_path:
        contract.pdf_path = pdf_path
        db.session.commit()
        flash('PDFが再生成されました。', 'success')
    else:
        flash('PDFの生成中にエラーが発生しました。', 'danger')

    return redirect(url_for('view_contract', contract_id=contract_id))


@app.route('/contracts/delete/<int:contract_id>', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    # Delete PDF file if it exists
    if contract.pdf_path and os.path.exists(contract.pdf_path):
        try:
            os.remove(contract.pdf_path)
        except OSError as e:
            logging.error(f"Error deleting PDF file: {e}")
    
    # Delete original file if it exists
    if contract.original_file_path and os.path.exists(contract.original_file_path):
        try:
            os.remove(contract.original_file_path)
        except OSError as e:
            logging.error(f"Error deleting original file: {e}")

    # Delete the contract
    db.session.delete(contract)
    db.session.commit()

    flash('契約書が削除されました。', 'success')
    return redirect(url_for('contract_list'))


# ========== API Routes ==========


@app.route('/api/room-details/<int:room_id>')
@login_required
def api_room_details(room_id):
    room = Room.query.get_or_404(room_id)
    building = room.building
    owner = building.owner

    # Get amenities as a list
    custom_amenities = []
    if room.custom_amenities:
        try:
            custom_amenities = json.loads(room.custom_amenities)
        except json.JSONDecodeError:
            pass

    room_data = {
        'id': room.id,
        'room_number': room.room_number,
        'layout': room.layout,
        'floor_area': room.floor_area,
        'floor': room.floor,
        'building': {
            'id':
            building.id,
            'name':
            building.name,
            'address':
            building.address,
            'structure':
            building.structure,
            'roof_structure':
            building.roof_structure,
            'floors':
            building.floors,
            'building_type':
            building.building_type,
            'construction_date':
            building.construction_date.strftime('%Y-%m-%d')
            if building.construction_date else None
        },
        'owner': {
            'id': owner.id,
            'name': owner.name,
            'address': owner.address
        },
        'amenities': {
            'has_kitchen': room.has_kitchen,
            'has_toilet': room.has_toilet,
            'has_bath': room.has_bath,
            'has_shower': room.has_shower,
            'has_washroom': room.has_washroom,
            'has_hot_water': room.has_hot_water,
            'has_stove': room.has_stove,
            'has_air_conditioner': room.has_air_conditioner,
            'has_lighting': room.has_lighting,
            'has_telephone': room.has_telephone,
            'has_internet': room.has_internet,
            'has_fire_alarm': room.has_fire_alarm,
            'has_tv_connection': room.has_tv_connection,
            'has_elevator_access': room.has_elevator_access,
            'has_parking': room.has_parking,
            'has_bicycle_parking': room.has_bicycle_parking,
            'has_private_garden': room.has_private_garden,
            'custom': custom_amenities
        }
    }

    return jsonify(room_data)


@app.route('/api/agent-details/<int:agent_id>')
@login_required
def api_agent_details(agent_id):
    agent = RealEstateAgent.query.get_or_404(agent_id)

    agent_data = {
        'id':
        agent.id,
        'name':
        agent.name,
        'license_number':
        agent.license_number,
        'registration_date':
        agent.registration_date.strftime('%Y-%m-%d')
        if agent.registration_date else None
    }

    return jsonify(agent_data)


@app.route('/api/special-term-details/<int:term_id>')
@login_required
def api_special_term_details(term_id):
    term = SpecialTerm.query.get_or_404(term_id)

    term_data = {'id': term.id, 'title': term.title, 'content': term.content}

    return jsonify(term_data)


# ========== Error Handlers ==========


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           error_code=404,
                           error_message="ページが見つかりませんでした。"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                           error_code=500,
                           error_message="サーバーエラーが発生しました。"), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html',
                           error_code=403,
                           error_message="このページにアクセスする権限がありません。"), 403
