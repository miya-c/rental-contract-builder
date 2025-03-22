from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms import TextAreaField, DateField, FloatField, IntegerField, HiddenField, FileField
from wtforms import SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from models import User, RealEstateAgent, Owner, Room, Building

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持')
    submit = SubmitField('ログイン')

class UserForm(FlaskForm):
    """User creation and editing form"""
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('パスワード', validators=[
        Optional(),
        Length(min=6, message='パスワードは6文字以上である必要があります。')
    ])
    confirm_password = PasswordField('パスワード（確認）', validators=[
        Optional(),
        EqualTo('password', message='パスワードが一致しません。')
    ])
    role = SelectField('ユーザー権限', choices=[
        ('user', '一般ユーザー'),
        ('admin', '管理者')
    ], validators=[DataRequired()])
    is_active = BooleanField('アクティブ', default=True)
    submit = SubmitField('保存')

class RealEstateAgentForm(FlaskForm):
    """Real estate agent form"""
    name = StringField('宅建士名', validators=[DataRequired(), Length(max=100)])
    license_number = StringField('免許番号', validators=[DataRequired(), Length(max=50)])
    registration_date = DateField('登録日', validators=[Optional()], format='%Y-%m-%d')
    notes = TextAreaField('備考', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('保存')

    def validate_license_number(self, field):
        """Validate license number uniqueness"""
        agent = RealEstateAgent.query.filter_by(license_number=field.data).first()
        if agent and (not self.id.data or int(self.id.data) != agent.id):
            raise ValidationError('この免許番号は既に登録されています。')

    # Hidden field for edit mode
    id = HiddenField('ID')

class OwnerForm(FlaskForm):
    """Property owner form"""
    name = StringField('オーナー名', validators=[DataRequired(), Length(max=100)])
    address = StringField('住所', validators=[DataRequired(), Length(max=255)])
    phone = StringField('電話番号', validators=[Optional(), Length(max=20)])
    email = StringField('メールアドレス', validators=[Optional(), Email(), Length(max=120)])
    notes = TextAreaField('備考', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('保存')

    # Hidden field for edit mode
    id = HiddenField('ID')

class BuildingForm(FlaskForm):
    """Building information form"""
    name = StringField('建物名', validators=[DataRequired(), Length(max=100)])
    address = StringField('住所', validators=[DataRequired(), Length(max=255)])
    
    structure_choices = [
        ('木造', '木造'),
        ('コンクリートブロック造', 'コンクリートブロック造'),
        ('鉄骨造', '鉄骨造'),
        ('鉄筋コンクリート造', '鉄筋コンクリート造'),
        ('木骨石造', '木骨石造'),
        ('軽量鉄骨造', '軽量鉄骨造'),
        ('その他', 'その他（自由入力）')
    ]
    structure = SelectField('構造', choices=structure_choices, validators=[DataRequired()])
    custom_structure = StringField('その他の構造', validators=[Optional(), Length(max=50)])
    
    roof_structure_choices = [
        ('陸屋根', '陸屋根'),
        ('瓦葺き', '瓦葺き'),
        ('スレート葺き', 'スレート葺き'),
        ('亜鉛メッキ合板葺き', '亜鉛メッキ合板葺き'),
        ('草葺き', '草葺き'),
        ('セメント瓦葺き', 'セメント瓦葺き'),
        ('アルミニューム葺き', 'アルミニューム葺き'),
        ('板葺き', '板葺き'),
        ('杉皮葺き', '杉皮葺き'),
        ('ビニール板葺き', 'ビニール板葺き'),
        ('その他', 'その他（自由入力）')
    ]
    roof_structure = SelectField('屋根構造', choices=roof_structure_choices, validators=[Optional()])
    custom_roof_structure = StringField('その他の屋根構造', validators=[Optional(), Length(max=50)])
    
    floors = IntegerField('階数', validators=[DataRequired()])
    total_units = IntegerField('総戸数', validators=[DataRequired()])
    
    building_type_choices = [
        ('アパート', 'アパート'),
        ('マンション', 'マンション'),
        ('戸建て', '戸建て'),
        ('貸間', '貸間'),
        ('その他', 'その他（自由入力）')
    ]
    building_type = SelectField('建物の種類', choices=building_type_choices, validators=[DataRequired()])
    custom_building_type = StringField('その他の建物種類', validators=[Optional(), Length(max=50)])
    
    construction_date = DateField('新築年月', validators=[Optional()], format='%Y-%m-%d')
    notes = TextAreaField('備考', validators=[Optional(), Length(max=1000)])
    
    owner_id = SelectField('オーナー', coerce=int, validators=[DataRequired()])
    submit = SubmitField('保存')

    # Hidden field for edit mode
    id = HiddenField('ID')
    
    def __init__(self, *args, **kwargs):
        super(BuildingForm, self).__init__(*args, **kwargs)
        # Populate the owner dropdown
        self.owner_id.choices = [(owner.id, owner.name) for owner in Owner.query.all()]

class RoomForm(FlaskForm):
    """Room information form"""
    room_number = StringField('部屋番号', validators=[DataRequired(), Length(max=20)])
    layout = StringField('間取り', validators=[DataRequired(), Length(max=20)])
    floor_area = FloatField('床面積（m²）', validators=[DataRequired()])
    floor = IntegerField('階数', validators=[DataRequired()])
    
    # Amenities checkboxes
    has_kitchen = BooleanField('台所')
    has_toilet = BooleanField('トイレ')
    has_bath = BooleanField('浴室')
    has_shower = BooleanField('シャワー')
    has_washroom = BooleanField('洗面所')
    has_hot_water = BooleanField('給湯')
    has_stove = BooleanField('コンロ')
    has_air_conditioner = BooleanField('エアコン')
    has_lighting = BooleanField('照明器具')
    has_telephone = BooleanField('電話設置')
    has_internet = BooleanField('インターネット回線')
    has_fire_alarm = BooleanField('火災警報器')
    has_tv_connection = BooleanField('共聴設備')
    has_elevator_access = BooleanField('エレベーター')
    has_parking = BooleanField('駐車場')
    has_bicycle_parking = BooleanField('駐輪場')
    has_private_garden = BooleanField('専用庭')
    
    # Custom amenities
    custom_amenities = TextAreaField('追加設備（カンマ区切りで入力）', validators=[Optional()])
    
    notes = TextAreaField('備考', validators=[Optional(), Length(max=1000)])
    building_id = SelectField('建物', coerce=int, validators=[DataRequired()])
    submit = SubmitField('保存')

    # Hidden field for edit mode
    id = HiddenField('ID')
    
    def __init__(self, *args, **kwargs):
        super(RoomForm, self).__init__(*args, **kwargs)
        # Populate the building dropdown
        self.building_id.choices = [(building.id, building.name) for building in Building.query.all()]

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkbox selection"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ContractForm(FlaskForm):
    """Lease contract form"""
    contract_number = StringField('契約番号', validators=[DataRequired(), Length(max=50)])
    tenant_name = StringField('借主名', validators=[DataRequired(), Length(max=100)])
    tenant_address = StringField('借主住所', validators=[DataRequired(), Length(max=255)])
    tenant_phone = StringField('借主電話番号', validators=[Optional(), Length(max=20)])
    tenant_email = StringField('借主メールアドレス', validators=[Optional(), Email(), Length(max=120)])
    
    start_date = DateField('契約開始日', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('契約終了日', validators=[Optional()], format='%Y-%m-%d')
    rent_amount = IntegerField('月額賃料（円）', validators=[DataRequired()])
    security_deposit = IntegerField('敷金（円）', validators=[Optional()])
    key_money = IntegerField('礼金（円）', validators=[Optional()])
    management_fee = IntegerField('管理費（円）', validators=[Optional()])
    
    room_id = SelectField('部屋', coerce=int, validators=[DataRequired()])
    agent_id = SelectField('宅建士', coerce=int, validators=[DataRequired()])
    template_id = SelectField('契約書テンプレート', coerce=int, validators=[DataRequired()])
    
    special_terms = MultiCheckboxField('特約条項', coerce=int)
    custom_special_terms = TextAreaField('追加特約条項', validators=[Optional()])
    
    submit = SubmitField('契約書作成')

    # Hidden field for edit mode
    id = HiddenField('ID')
    
    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        from models import Room, RealEstateAgent, ContractTemplate, SpecialTerm
        
        # Populate the room dropdown
        rooms = Room.query.join(Building).all()
        self.room_id.choices = [(room.id, f"{room.building.name} {room.room_number}") for room in rooms]
        
        # Populate the agent dropdown
        self.agent_id.choices = [(agent.id, f"{agent.name} ({agent.license_number})") 
                                for agent in RealEstateAgent.query.all()]
        
        # Populate the template dropdown
        self.template_id.choices = [(template.id, template.name) 
                                   for template in ContractTemplate.query.all()]
        
        # Populate the special terms checkboxes
        self.special_terms.choices = [(term.id, term.title) 
                                     for term in SpecialTerm.query.all()]

class SpecialTermForm(FlaskForm):
    """Special term form"""
    title = StringField('タイトル', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    is_common = BooleanField('よく使う特約', default=False)
    submit = SubmitField('保存')

    # Hidden field for edit mode
    id = HiddenField('ID')

class ContractTemplateForm(FlaskForm):
    """Contract template form"""
    name = StringField('テンプレート名', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('説明', validators=[Optional()])
    file_content = TextAreaField('テンプレート内容（HTMLのみ）', validators=[Optional()])
    is_default = BooleanField('デフォルトテンプレート', default=False)
    
    file_type = SelectField('ファイル形式', choices=[
        ('html', 'HTML'),
        ('excel', 'Excel'),
        ('word', 'Word'),
        ('pdf', 'PDF')
    ], validators=[DataRequired()])
    
    template_file = FileField('テンプレートファイルをアップロード', 
                             validators=[Optional()])
    
    submit = SubmitField('保存')

    # Hidden field for edit mode
    id = HiddenField('ID')
    
    def validate_file_content(self, field):
        # HTMLの場合はテンプレート内容が必要
        if self.file_type.data == 'html' and not field.data:
            raise ValidationError('HTML形式の場合はテンプレート内容を入力してください。')
    
    def validate_template_file(self, field):
        # HTML以外の場合はファイルのアップロードが必要
        if self.file_type.data != 'html' and not field.data:
            raise ValidationError('ファイルをアップロードしてください。')
        
        # ファイル拡張子の確認
        if field.data:
            filename = field.data.filename
            if self.file_type.data == 'excel' and not (filename.endswith('.xlsx') or filename.endswith('.xls')):
                raise ValidationError('Excel形式のファイル(.xlsx, .xls)をアップロードしてください。')
            elif self.file_type.data == 'word' and not (filename.endswith('.docx') or filename.endswith('.doc')):
                raise ValidationError('Word形式のファイル(.docx, .doc)をアップロードしてください。')
            elif self.file_type.data == 'pdf' and not filename.endswith('.pdf'):
                raise ValidationError('PDF形式のファイル(.pdf)をアップロードしてください。')
