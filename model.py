from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# جدول الأطباء
class DoctorRegister(db.Model):
    __tablename__ = 'doctor_register'

    doctor_id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Doctor {self.name}>"


# جدول الأمهات
class MotherRegister(db.Model):
    __tablename__ = 'mother_register'
    mother_id = db.Column(db.Integer, primary_key=True, unique=True)
    user_name = db.Column(db.String(100), unique=True, nullable=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=True)

    children = db.relationship('Child', backref='mother', lazy=True)

    def __repr__(self):
        return f"<Mother {self.user_name}>"


# جدول الأطفال
class Child(db.Model):
    __tablename__ = 'child'

    child_id = db.Column(db.Integer, primary_key=True, unique=True)
    mother_id = db.Column(db.Integer, db.ForeignKey('mother_register.mother_id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    BD = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # "male" or "female"
    level = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text, nullable=True)

    doctor_links = db.relationship('DoctorsChild', backref='child', lazy=True)
    activities = db.relationship('Activities', backref='child', lazy=True)
    medicines = db.relationship('Medicine', backref='child', lazy=True)


    def __repr__(self):
        return f"<Child {self.name}>"


# جدول الربط بين الطفل والطبيب (Many-to-Many)
class DoctorsChild(db.Model):
    __tablename__ = 'doctors_child'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_register.doctor_id'), nullable=False)

    doctor = db.relationship('DoctorRegister', backref='child_links', lazy=True)

    def __repr__(self):
        return f"<Link {self.child_id}-{self.doctor_id}>"


# جدول النشاطات
class Activities(db.Model):
    __tablename__ = 'activities'

    activity_id = db.Column(db.Integer, primary_key=True, unique=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    activity_name = db.Column(db.String(100), nullable=False)

    ratings = db.relationship('Rating', backref='activity', lazy=True)

    def __repr__(self):
        return f"<Activity {self.activity_name}>"


# جدول التقييمات
class Rating(db.Model):
    __tablename__ = 'rating'

    rating_id = db.Column(db.Integer, primary_key=True, unique=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Rating {self.rating}>"


# جدول الأدوية
class Medicine(db.Model):
    __tablename__ = 'medicine'

    medicine_id = db.Column(db.Integer, primary_key=True, unique=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_register.doctor_id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.Integer, nullable=False)
    time_per_day = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    finishdate = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Medicine {self.medicine_name}>"


# جدول التقارير



class DoctorReview(db.Model):
    __tablename__ = 'doctor_review'

    review_id = db.Column(db.Integer, primary_key=True, unique=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_register.doctor_id'), nullable=False)

    # 💡 تحديد الفترة الزمنية التي راجعها الطبيب (مهم جداً)
    # يمكن أن يكون التقرير عن أسبوع أو شهر
    review_start_date = db.Column(db.Date, nullable=False)
    review_end_date = db.Column(db.Date, nullable=False)

    # 💡 الملاحظات والتوجيهات النصية للطبيب
    doctor_notes = db.Column(db.Text, nullable=True)  # ملاحظة الطبيب حول الأداء العام (نص حر)
    new_focus_activity = db.Column(db.String(255), nullable=True)  # النشاط المقترح للتركيز عليه في الفترة القادمة

    # 💡 الإدخالات القابلة للقياس (لتوثيق قرار الطبيب)
    is_medication_adjusted = db.Column(db.Boolean, default=False)  # هل تم تعديل الدواء؟
    medication_details = db.Column(db.String(255), nullable=True)  # تفاصيل التعديل

    created_time = db.Column(db.DateTime, default=datetime.utcnow)  # وقت إنشاء هذه المراجعة

    def __repr__(self):
        return f"<Review {self.review_id} for Child {self.child_id}>"
class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedule'

    schedule_id = db.Column(db.Integer, primary_key=True, unique=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_register.doctor_id'), nullable=False)

    # اليوم من الأسبوع (مثلاً Monday, Tuesday...)
    day_of_week = db.Column(db.String(20), nullable=False)

    # وقت بداية الدوام ونهايته
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    doctor = db.relationship('DoctorRegister', backref='schedules', lazy=True)

    def __repr__(self):
        return f"<Schedule {self.day_of_week} - Dr.{self.doctor_id}>"
class DoctorAppointment(db.Model):
    __tablename__ = 'doctor_appointment'

    appointment_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_register.doctor_id'), nullable=False)

    day_of_week = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(10), nullable=True)             # مثل 15:30

    status = db.Column(db.String(20), default='available')

    doctor = db.relationship('DoctorRegister', backref='doctor_appointments', lazy=True)

    def __repr__(self):
        return f"<DoctorAppointment {self.day_of_week} {self.time} - Dr.{self.doctor_id}>"

class ChildAppointment(db.Model):
    __tablename__ = 'child_appointment'

    id = db.Column(db.Integer, primary_key=True, unique=True)

    appointment_id = db.Column(db.Integer, db.ForeignKey('doctor_appointment.appointment_id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.child_id'), nullable=False)
    mother_id = db.Column(db.Integer, db.ForeignKey('mother_register.mother_id'), nullable=True)

    # ملاحظات من الأم (مثلاً سبب الحجز)
    reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    child = db.relationship('Child', backref='child_appointments', lazy=True)
    mother = db.relationship('MotherRegister', backref='child_appointments', lazy=True)

    def __repr__(self):
        return f"<ChildAppointment Child:{self.child_id} -> Appt:{self.appointment_id}>"

