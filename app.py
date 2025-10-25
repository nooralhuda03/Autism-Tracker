import io
from flask import (Flask, redirect, url_for, render_template
, request, session, flash,jsonify,send_file)
import base64
from datetime import datetime, date, timedelta
from flask_migrate import Migrate
from sqlalchemy import extract, func
from model import (db, DoctorRegister, MotherRegister, Child, Rating, Activities
, DoctorReview, Medicine, DoctorsChild, DoctorAppointment, DoctorSchedule, ChildAppointment)
import qrcode
from io import BytesIO

app = Flask(__name__)
migrate = Migrate(app, db)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autism_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def days_to_number(day_name):
    days_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }
    return days_map.get(day_name, 0)

@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        user_name = request.form['user_name']
        phone_number = request.form['phone_number']
        specialty = request.form['specialty']
        password = request.form['password']

        # إنشاء حساب الدكتور
        new_doctor = DoctorRegister(
            name=name,
            user_name=user_name,
            phone_number=phone_number,
            specialty=specialty,
            password=password
        )
        db.session.add(new_doctor)
        db.session.commit()

        # 🗓️ الأيام المحتملة
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        active_days = request.form.getlist("active_days")

        # 🔁 إضافة الجدول الأسبوعي والمواعيد الفارغة
        for day in days:
            if day in active_days:
                start_time = request.form.get(f"{day}_start")
                end_time = request.form.get(f"{day}_end")

                if start_time and end_time:
                    start_t = datetime.strptime(start_time, "%H:%M").time()
                    end_t = datetime.strptime(end_time, "%H:%M").time()

                    # حفظ الجدول الزمني
                    new_schedule = DoctorSchedule(
                        doctor_id=new_doctor.doctor_id,
                        day_of_week=day,
                        start_time=start_t,
                        end_time=end_t,
                        is_available=True
                    )
                    db.session.add(new_schedule)
                    db.session.commit()

                    # ⏱️ إنشاء المواعيد الزمنية المتاحة
                    slot_duration = timedelta(minutes=30)  # مثلًا كل موعد نصف ساعة
                    current_time = datetime.combine(datetime.today(), start_t)
                    end_datetime = datetime.combine(datetime.today(), end_t)

                    while current_time < end_datetime:
                        new_appointment = DoctorAppointment(
                            doctor_id=new_doctor.doctor_id,  # ✅ استخدمي الـ doctor_id من الكائن الجديد
                            day_of_week=day,  # ✅ اليوم الحالي من اللوب
                            time=current_time.strftime("%H:%M:%S"),
                            status='available'
                        )
                        db.session.add(new_appointment)
                        current_time += timedelta(minutes=30)

        db.session.commit()
        return redirect(url_for('doctor_login'))

    return render_template('doctor_rigester.html')


@app.route('/', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']

        doctor = DoctorRegister.query.filter_by(user_name=user_name, password=password).first()

        if doctor:
            session['doctor_id'] = doctor.doctor_id
            session['doctor_name'] = doctor.name
            session['specialty'] = doctor.specialty

            flash('Login successful', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('doctor_login.html')

@app.route('/add_child', methods=['GET'])
def add_child_page():
    return render_template('add_child.html')
@app.route('/add_child', methods=['GET', 'POST'])
def add_child():

    if request.method == 'POST':
        name = request.form['name']
        bd = request.form['bd']
        gender = request.form['gender']
        level = request.form['level']
        note = request.form.get('note', '')
        phone_number = request.form.get('mother_phone', '').strip()

        mother_obj = None

        # 🔹 إذا المستخدم أدخل رقم هاتف
        if phone_number:
            mother_obj = MotherRegister.query.filter_by(phone_number=phone_number).first()
            if not mother_obj:
                mother_obj = MotherRegister(
                    user_name=f"mother_{phone_number}",
                    phone_number=phone_number,
                    password="temp123"  # كلمة مرور مؤقتة
                )
                db.session.add(mother_obj)
                db.session.commit()

        # 🔹 إنشاء الطفل
        new_child = Child(
            mother=mother_obj,
            name=name,
            BD=datetime.strptime(bd, '%Y-%m-%d'),
            gender=gender,
            level=int(level),
            note=note
        )

        db.session.add(new_child)
        db.session.commit()
        doctor_id = session.get('doctor_id')
        if doctor_id:
            link = DoctorsChild(child_id=new_child.child_id, doctor_id=doctor_id)
            db.session.add(link)
            db.session.commit()
        else:
            flash("لم يتم العثور على جلسة الطبيب. يرجى تسجيل الدخول مرة أخرى.", "danger")

        # ✅ توليد رابط و QR بعد إضافة الطفل
        mother_login_url = f"http://{request.host.split(':')[0]}:5000/mother_login"
        qr_img = qrcode.make(mother_login_url)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_data = base64.b64encode(buffer.getvalue()).decode()

        # ✅ نرجع صفحة الـ QR كبوب-أب
        return render_template('qr_popup.html', qr_data=qr_data, child_name=name)

    # في حالة GET (فتح الصفحة العادية)
    return render_template('add_child.html')

@app.route('/manage_schedule', methods=['GET', 'POST'])
def manage_schedule():
    # التحقق من تسجيل دخول الدكتور
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        return redirect(url_for('doctor_login'))

    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        # نحول النصوص إلى وقت
        start_t = datetime.strptime(start_time, "%H:%M").time()
        end_t = datetime.strptime(end_time, "%H:%M").time()

        # 🔄 إذا كان موجود نفس اليوم مسبقاً نحدثه بدلاً من إضافة تكرار
        existing_schedule = DoctorSchedule.query.filter_by(doctor_id=doctor_id, day_of_week=day_of_week).first()
        if existing_schedule:
            existing_schedule.start_time = start_t
            existing_schedule.end_time = end_t
            existing_schedule.is_available = True
            db.session.commit()

            # نحذف المواعيد القديمة لهاليوم حتى نعيد إنشائها
            DoctorAppointment.query.filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.day_of_week == day_of_week,

            ).delete()
            db.session.commit()
        else:
            # نضيف الجدول لأول مرة
            new_schedule = DoctorSchedule(
                doctor_id=doctor_id,
                day_of_week=day_of_week,
                start_time=start_t,
                end_time=end_t,
                is_available=True
            )
            db.session.add(new_schedule)
            db.session.commit()

        # ⏱️ إنشاء المواعيد الجديدة لهاليوم
        slot_duration = timedelta(minutes=30)
        today = datetime.today()
        day_number = days_to_number(day_of_week)
        next_day = today + timedelta((day_number - today.weekday()) % 7)

        current_time = datetime.combine(next_day, start_t)
        end_datetime = datetime.combine(next_day, end_t)

        while current_time < end_datetime:
            new_appointment = DoctorAppointment(
                doctor_id=doctor_id,  # ✅ استخدمي الـ doctor_id من الكائن الجديد
                day_of_week=day_of_week,  # ✅ اليوم الحالي من اللوب
                time=current_time.strftime("%H:%M:%S"),
                status='available'
            )
            db.session.add(new_appointment)
            current_time += timedelta(minutes=30)

        db.session.commit()
        flash('تم تحديث جدول المواعيد بنجاح ✅', 'success')
        return redirect(url_for('manage_schedule'))

    # عرض الجداول الحالية
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id).all()
    return render_template('manage_schedule.html', schedules=schedules)

@app.route('/doctor_dashboard')
def doctor_dashboard():
    print("Session content:", dict(session))
    doctor_id = session.get('doctor_id')
    doctor = DoctorRegister.query.get(doctor_id)
    total_patients = Child.query.join(DoctorsChild).filter(DoctorsChild.doctor_id == doctor_id).count()

    # المرضى اللي عندهم موعد اليوم ولم يحضروا
    today_name = date.today().strftime('%A')

    # 2. جلب جميع الأطفال (أو الأطفال المرتبطين بالدكتور)
    children_query = (
        db.session.query(Child)
        .join(DoctorsChild, Child.child_id == DoctorsChild.child_id)
        .filter(DoctorsChild.doctor_id == doctor_id)
        .all()
    )
    children_data = []

    for child in children_query:
        status = 'N/A'
        has_appointment_today = False

        # 3. 🎯 البحث عن آخر موعد محجوز لهذا الطفل لليوم الحالي ولهذا الطبيب

        latest_appointment_record = (
            db.session.query(DoctorAppointment)
            .join(ChildAppointment, DoctorAppointment.appointment_id == ChildAppointment.appointment_id)
            .filter(
                ChildAppointment.child_id == child.child_id,
                DoctorAppointment.doctor_id == doctor_id,  # فلترة حسب الطبيب
                DoctorAppointment.day_of_week == today_name,  # 💡 الفلترة حسب اليوم
                DoctorAppointment.status.in_(['booked', 'completed'])  # الحالة يجب أن تكون محجوزة أو مكتملة
            )
            .order_by(ChildAppointment.created_at.desc())
            .first()
        )

        if latest_appointment_record:
            status = latest_appointment_record.status
            has_appointment_today = True

            # 4. إعداد البيانات لتمريرها إلى القالب
        child_with_status = {
            'child_id': child.child_id,
            'name': child.name,
            'BD': child.BD,
            'gender': child.gender,
            'level': child.level,
            'note': child.note,
            # 💡 البيانات التي يحتاجها القالب:
            'has_appointment_today': has_appointment_today,
            'appointment_status': status,
        }
        children_data.append(child_with_status)

    # 5. حساب الإحصائيات (بناءً على البيانات المفلترة لليوم)
    total_patients = len(children_data)
    waiting_patients = sum(1 for c in children_data if c['appointment_status'] == 'booked')
    seen_today = sum(1 for c in children_data if c['appointment_status'] == 'completed')

    return render_template(
        'doctor_dashboard.html',
        doctor_name=doctor.name,
        specialty=doctor.specialty,
        children=children_data,
        total_patients=total_patients,
        waiting_patients=waiting_patients,
        seen_today=seen_today,
    )

@app.route('/doctor/child_details/<int:child_id>', methods=['GET', 'POST'])
def doctor_child_details(child_id):

    # 1. التحقق من جلسة الطبيب
    if 'doctor_name' not in session:
        flash("الرجاء تسجيل الدخول كطبيب.", "danger")
        return redirect(url_for('doctor_login'))

    # 2. جلب الطفل (باستخدام db.session.get() الحديثة)
    child = db.session.get(Child, child_id)
    if not child:
        flash("Patient not found.", "danger")
        return redirect(url_for('doctor_dashboard'))

    medicines = Medicine.query.filter_by(child_id=child_id).order_by(Medicine.start_date.desc()).all()

    doctor_reviews = DoctorReview.query.filter_by(child_id=child_id).order_by(DoctorReview.created_time.desc()).all()

    if request.method == 'POST':
        new_note = request.form.get('doctor_note')

        if new_note:
            child.note = new_note
            db.session.commit()
            flash("ملاحظة الطبيب حُفظت بنجاح. ✅", "success")
        else:
            flash("لم يتم إدخال ملاحظة جديدة.", "warning")

        # إعادة التوجيه لصفحة التفاصيل بعد الحفظ
        return redirect(url_for('doctor_child_details', child_id=child_id))

    # 5. عرض القالب (GET Request)
    return render_template('doctor_child_details.html',
                           child=child,
                           medicines=medicines,
                           reviews=doctor_reviews)

@app.route('/generate_qr')
def generate_qr():

    login_url = "http://192.168.0.219:5000/mother_login"  # غيّريه حسب اسم صفحة اللوجن عندك

    qr = qrcode.make(login_url)

    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@app.route('/mother_login', methods=['GET', 'POST'])
def mother_login():
    error_message = None
    if request.method == 'POST':
        username = request.form['user_name']
        password = request.form['password']

        mother = MotherRegister.query.filter_by(user_name=username, password=password).first()
        if mother:
            # نخزن الـ ID حتى نسترجع بياناتها بسهولة لاحقًا
            session['mother_id'] = mother.mother_id
            session['mother_name'] = mother.user_name

            return redirect(url_for('mother_dashboard'))
        else:
            error_message = "Invalid username or password"

    return render_template('mother_login.html', error_message=error_message)

@app.route('/mother_dashboard')
def mother_dashboard():
    mother_id = session.get('mother_id')
    if not mother_id:
        return redirect(url_for('mother_login'))

    mother = MotherRegister.query.get(mother_id)
    children = Child.query.filter_by(mother_id=mother.mother_id).all()

    return render_template('mother_dashboard.html', mother=mother, children=children,date=date)

@app.route('/child_evaluation/<int:child_id>', methods=['GET', 'POST'])
def child_evaluation(child_id):
    child = Child.query.get_or_404(child_id)

    if request.method == 'POST':
        # بعدين هنا نضيف كود حفظ التقييم من الفورم
        flash("تم حفظ التقييم بنجاح ✅", "success")
        return redirect(url_for('mother_dashboard'))

    return render_template('child_evaluation.html', child=child)

@app.route('/save_child_rating/<int:child_id>', methods=['POST'])
def save_child_rating(child_id):
    child = Child.query.get(child_id)
    if not child:
        flash("Child not found", "danger")
        return redirect(url_for('mother_dashboard'))

    ratings = {
        "eye": request.form.get("eye"),
        "name_call": request.form.get("name_call"),
        "express": request.form.get("express"),
        "follow_instr": request.form.get("follow_instr"),
        "conversation": request.form.get("conversation"),
        "family": request.form.get("family"),
        "play": request.form.get("play"),
        "emotion": request.form.get("emotion"),
        "patience": request.form.get("patience"),
        "imitate": request.form.get("imitate"),
        "repetitive": request.form.get("repetitive"),
        "routine": request.form.get("routine"),
        "anger": request.form.get("anger"),
        "calm": request.form.get("calm"),
        "sensitivity": request.form.get("sensitivity"),
        "eat": request.form.get("eat"),
        "toilet": request.form.get("toilet"),
        "dress": request.form.get("dress"),
        "sleep": request.form.get("sleep"),
        "daily": request.form.get("daily"),
        "focus": request.form.get("focus"),
        "interest": request.form.get("interest"),
        "complete": request.form.get("complete"),
        "switch_activity": request.form.get("switch_activity"),
        "cooperation": request.form.get("cooperation"),
        "happy": request.form.get("happy"),
        "calm_new": request.form.get("calm_new"),
        "empathy": request.form.get("empathy"),
        "sadness": request.form.get("sadness"),
        "response": request.form.get("response")
    }


    for key, value in ratings.items():
        if value:

            activity = Activities.query.filter_by(activity_name=key).first()


            if not activity:
                activity = Activities(activity_name=key, child_id=child_id)
                db.session.add(activity)
                db.session.commit()

            new_rating = Rating(
                child_id=child_id,
                activity_id=activity.activity_id,
                rating=int(value),
                date=datetime.now(),
                duration=0
            )
            db.session.add(new_rating)

    db.session.commit()

    flash("تم حفظ التقييم بنجاح ✅", "success")
    return redirect(url_for('mother_dashboard'))

@app.route('/mother/reports/<int:child_id>')
def mother_reports(child_id):

    has_access, child, error_msg = check_user_access(child_id)
    if not has_access or 'doctor_id' not in session:
        flash(error_msg or "غير مصرح لك بالوصول لبيانات هذا الطفل.", "danger")
        return redirect(url_for('doctor_dashboard'))


    return render_template('doctor_report.html', child=child)

@app.route('/mother/update_info', methods=['GET', 'POST'])
def mother_update_info():

    mother_id = session.get('mother_id')
    if not mother_id:
        flash("الرجاء تسجيل الدخول أولاً.", "warning")
        return redirect(url_for('mother_login'))


    mother = db.session.get(MotherRegister, mother_id)

    if request.method == 'POST':
        new_username = request.form.get('user_name')

        new_password = request.form.get('new_password')


        if new_username and new_username != mother.user_name:

            mother.user_name = new_username


        if new_password:

            mother.password = new_password
            flash("تم تحديث كلمة المرور واسم المستخدم بنجاح. ✅", "success")
        else:
            flash("تم تحديث اسم المستخدم بنجاح. ✅", "success")

        db.session.commit()
        return redirect(url_for('mother_dashboard'))

    return render_template('mother_update_info.html', mother=mother)

@app.route('/mother/logout')
def mother_logout():

    session.pop('mother_id', None)
    session.pop('mother_name', None)
    flash("تم تسجيل خروجك بنجاح. نلقاك قريباً!", "info")
    return redirect(url_for('mother_login'))

def check_user_access(child_id):


    child = db.session.get(Child, child_id)
    if not child:
        return False, None, "Child not found."

    mother_id = session.get('mother_id')
    doctor_id = session.get('doctor_id')

    # 1. التحقق للأم:
    if mother_id and child.mother_id == mother_id:
        return True, child, None

    # 2. التحقق للطبيب:
    if doctor_id:
        # 💡 استخدام DoctorsChild للربط
        is_linked = db.session.query(DoctorsChild).filter(
            DoctorsChild.doctor_id == doctor_id,
            DoctorsChild.child_id == child_id
        ).first()
        if is_linked:
            return True, child, None

    return False, None, "Unauthorized access to this child's data."

@app.route('/api/report/list/<report_type>')
def api_reports_list(report_type):
    child_id = request.args.get('child_id', type=int)


    has_access, child, error_msg = check_user_access(child_id)
    if not has_access:
        return jsonify({"error": error_msg or "Unauthorized"}), 403

    report_items = []


    mother_id = session.get('mother_id')
    doctor_id = session.get('doctor_id')

    if not mother_id and not doctor_id:
        return jsonify({"error": "Unauthorized"}), 401


    child = db.session.get(Child, child_id)
    if not child:
        return jsonify({"error": "Child not found"}), 404

    # ✅ التحقق من صلاحية الوصول
    if mother_id:
        if child.mother_id != mother_id:
            return jsonify({"error": "Unauthorized child access"}), 403
    elif doctor_id:
        link_exists = DoctorsChild.query.filter_by(
            child_id=child_id,
            doctor_id=doctor_id
        ).first()
        if not link_exists:
            return jsonify({"error": "Unauthorized doctor access"}), 403


    oldest_rating = db.session.query(func.min(Rating.date)).filter(Rating.child_id == child_id).scalar()

    if report_type == 'daily':
        title = "التقارير اليومية"
        dates = db.session.query(func.date(Rating.date))\
            .filter(Rating.child_id == child_id)\
            .distinct()\
            .order_by(func.date(Rating.date).desc())\
            .limit(30).all()

        for d in dates:
            date_str = d[0]
            report_items.append({
                'id': date_str,
                'title': f"تقرير يوم: {date_str}",
                'child_id': child_id
            })

    elif report_type == 'weekly':
        title = "التقارير الأسبوعية"
        today = date.today()
        for i in range(1, 9):
            end_date = today - timedelta(weeks=i - 1)
            start_date = today - timedelta(weeks=i)
            has_data = db.session.query(Rating).filter(
                Rating.child_id == child_id,
                Rating.date.between(start_date, end_date)
            ).first()
            if has_data:
                report_items.append({
                    'id': f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}",
                    'title': f"تقرير الفترة: {start_date.strftime('%d-%m')} إلى {end_date.strftime('%d-%m-%Y')}",
                    'child_id': child_id
                })

    elif report_type == 'monthly':
        title = "التقارير الشهرية"
        today = date.today()
        for i in range(12):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            first_day_of_month = date(year, month, 1)
            if month == 12:
                last_day_of_month = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day_of_month = date(year, month + 1, 1) - timedelta(days=1)
            has_data = db.session.query(Rating).filter(
                Rating.child_id == child_id,
                Rating.date.between(first_day_of_month, last_day_of_month)
            ).first()
            if has_data:
                report_items.append({
                    'id': f"{year}-{month:02d}",
                    'title': f"تقرير شهر: {month:02d}-{year}",
                    'child_id': child_id
                })
        report_items.reverse()

    return jsonify({"title": title, "items": report_items})

@app.route('/api/report/data/<report_type>/<report_id>/<int:child_id>')
def api_report_data(report_type, report_id, child_id):
    has_access, child, error_msg = check_user_access(child_id)
    if not has_access:
        return jsonify({"error": error_msg or "Unauthorized"}), 403

    chart_data = {'labels': [], 'data': [], 'child_name': child.name}

    mother_id = session.get('mother_id')
    if not mother_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 💡 استخدام get الحديثة
    child = db.session.get(Child, child_id)
    if not child or child.mother_id != mother_id:
        return jsonify({"error": "Child not found or unauthorized"}), 404

    chart_data = {'labels': [], 'data': [], 'child_name': child.name}

    if report_type == 'daily':
        ratings = db.session.query(Rating, Activities).join(Activities).filter(
            Rating.child_id == child_id,
            func.date(Rating.date) == report_id
        ).all()

        if ratings:
            for rating, activity in ratings:
                chart_data['labels'].append(activity.activity_name)
                chart_data['data'].append(rating.rating)
        else:
            return jsonify({"error": f"لا توجد بيانات تقييم ليوم {report_id}."}), 404

    elif report_type == 'weekly':
        start_date_str, end_date_str = report_id.split('-')

        # 💡 الخطوة 1: قراءة التواريخ وتحويلها
        start_date = datetime.strptime(start_date_str, '%Y%m%d').date()
        end_date = datetime.strptime(end_date_str, '%Y%m%d').date()

        end_date_inclusive = end_date + timedelta(days=1)

        daily_averages = db.session.query(
            func.date(Rating.date),
            func.avg(Rating.rating)
        ).filter(
            Rating.child_id == child_id,
            Rating.date.between(start_date, end_date_inclusive)
        ).group_by(func.date(Rating.date)).order_by(func.date(Rating.date)).all()

        date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # 💡 الخطوة 2: التصحيح لضمان التحويل الصحيح للتواريخ النصية إلى مفتاح القاموس
        results_dict = {}
        has_valid_data = False

        for date_str, avg_rating in daily_averages:
            # date_str هنا هو النص، نقوم بتنسيقه مباشرة ليكون مفتاحاً
            results_dict[date_str] = avg_rating
            has_valid_data = True

        for single_date in date_range:
            date_key = single_date.strftime('%Y-%m-%d')
            chart_data['labels'].append(single_date.strftime('%A'))

            if date_key in results_dict:
                chart_data['data'].append(round(results_dict[date_key], 2))
            else:
                chart_data['data'].append(None)

        if not has_valid_data:
            return jsonify({"error": "لا توجد بيانات تقييم في هذه الفترة الأسبوعية."}), 404


    elif report_type == 'monthly':
        year, month = map(int, report_id.split('-'))

        weekly_averages = db.session.query(
            extract('week', Rating.date),
            func.avg(Rating.rating)
        ).filter(
            Rating.child_id == child_id,
            extract('year', Rating.date) == year,
            extract('month', Rating.date) == month
        ).group_by(extract('week', Rating.date)).order_by(extract('week', Rating.date)).all()


        if not weekly_averages:
            return jsonify({"error": "لا توجد بيانات كافية لعرض التقرير الشهري."}), 404

        for week_num, avg_rating in weekly_averages:
            chart_data['labels'].append(f"الأسبوع {int(week_num)}")
            chart_data['data'].append(round(avg_rating, 2))

    # ❗ إزالة التحقق النهائي المكرر من أسفل الدالة
    # if not chart_data['data']:
    #     return jsonify({"error": "لا توجد بيانات كافية لعرض التقرير في هذه الفترة."}), 404

    # ❗ نرجع البيانات بصيغة JSON
    return jsonify(chart_data)

@app.route('/doctor/reports/<int:child_id>')
def doctor_reports(child_id):

    has_access, child, error_msg = check_user_access(child_id)
    if not has_access or 'doctor_id' not in session:
        flash(error_msg or "غير مصرح لك بالوصول لبيانات هذا الطفل.", "danger")
        return redirect(url_for('doctor_dashboard'))

    # 2. نحتاج فقط لتمرير كائن الطفل لـ HTML
    return render_template('doctor_report.html', child=child)  # نمرر child وليس children

@app.route('/doctor/add_prescription/<int:child_id>', methods=['GET', 'POST'])
def add_prescription(child_id):
    child = Child.query.get_or_404(child_id)

    if request.method == 'POST':
        medicine_name = request.form['medicine_name']
        dosage = request.form['dosage']
        time_per_day = request.form['time_per_day']
        finishdate_str = request.form['finishdate']
        note = request.form.get('note')

        finishdate = datetime.strptime(finishdate_str, "%Y-%m-%d").date()
        start_date = datetime.now().date()

        new_medicine = Medicine(
            child_id=child_id,
            doctor_id=session.get('doctor_id'),  # ✅ الطبيب الحالي
            medicine_name=medicine_name,
            dosage=dosage,
            time_per_day=time_per_day,
            start_date=start_date,
            finishdate=finishdate,
            note=note
        )

        db.session.add(new_medicine)
        db.session.commit()
        flash('Prescription added successfully.', 'success')
        return redirect(url_for('doctor_child_details', child_id=child_id))

    return render_template('add_prescription.html', child=child)

@app.route('/child_details/<int:child_id>', methods=['GET', 'POST'])
def child_details(child_id):
    child = Child.query.get_or_404(child_id)
    medicines = Medicine.query.filter_by(child_id=child_id).all()
    ratings = Rating.query.filter_by(child_id=child_id).order_by(Rating.date.desc()).limit(5).all()  # آخر 5 تقييمات
    upcoming_appointments = (
        db.session.query(DoctorAppointment)
        .join(ChildAppointment, DoctorAppointment.appointment_id == ChildAppointment.appointment_id)
        .filter(ChildAppointment.child_id == child_id,
                # يمكن تصفية المواعيد التي لم تكتمل بعد
                DoctorAppointment.status.in_(['booked', 'available', 'canceled']))
        .order_by(DoctorAppointment.day_of_week.asc(), DoctorAppointment.time.asc())
        .all()
    )

    # 2. جلب المواعيد المتاحة (يجب أن تكون دالة get_available_appointments متاحة هنا)
    try:
        # ⚠️ يجب التأكد أن دالة get_available_appointments تسترجع قيمة قابلة للتحويل إلى JSON
        available_response = get_available_appointments(child_id)
        if available_response.status_code == 200:
            available_appointments = available_response.json.get('items', [])
        else:
            available_appointments = []
    except NameError:
        available_appointments = []  # في حال عدم توفر دالة get_available_appointments
    except Exception:
        available_appointments = []

    # 3. إرجاع القالب بالبيانات الصحيحة
    return render_template(
        'mother_child_details.html',
        child=child,
        medicines=medicines,
        # 💡 هذا المتغير يمثل المواعيد المحجوزة التي ستظهر في القائمة العلوية
        appointments=upcoming_appointments,
        available_appointments=available_appointments,
        date=date
    )


@app.route('/api/appointment/book', methods=['POST'])
def api_book_appointment():

    try:
        # 1. جلب البيانات والتحقق الأساسي
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        child_id = data.get('child_id')
        mother_id = session.get('mother_id')

        if not (appointment_id and child_id and mother_id):
            return jsonify({"error": "بيانات الحجز (الموعد/الطفل/الأم) ناقصة."}), 400

        # 2. جلب الموعد
        appointment = DoctorAppointment.query.get(appointment_id)


        if not appointment or appointment.status != 'available':
            return jsonify({"error": "الموعد غير موجود أو غير متاح الآن."}), 400

        # 3. 🛡️ التحقق من عدم التكرار
        existing_booking = ChildAppointment.query.filter_by(
            appointment_id=appointment_id,
            child_id=child_id
        ).first()

        if existing_booking:
            return jsonify({"error": "هذا الطفل حجز هذا الموعد مسبقاً."}), 400

        # 4. الحجز الفعلي والتحديث في قاعدة البيانات

        # أ. تحديث الحالة
        appointment.status = 'booked'
        db.session.add(appointment) # إضافة: لفرض ربط الكائن بالجلسة قبل الحفظ

        # ب. إضافة سجل ChildAppointment
        new_booking = ChildAppointment(
            appointment_id=appointment.appointment_id,
            child_id=child_id,
            mother_id=mother_id,
            reason="حجز من قبل الأم عبر الواجهة"
        )
        db.session.add(new_booking)

        db.session.commit()

        # 5. إرجاع بيانات الموعد لتحديث الواجهة في JS (بما في ذلك اسم الطبيب)
        return jsonify({
            "message": "تم حجز الموعد بنجاح!",
            "appointment": {
                "id": appointment.appointment_id,
                "day": appointment.day_of_week,
                "time": appointment.time,
                "doctor_name": appointment.doctor.name  # 💡 هذا هو الحقل الضروري
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        # current_app.logger.error(f"Error booking appointment: {e}")
        return jsonify({"error": "حدث خطأ داخلي أثناء حجز الموعد."}), 500

@app.route('/api/appointments/available/<int:child_id>')
def get_available_appointments(child_id):
    print(123)
    try:

        # 🔹 نجيب كل الـ doctor_id المرتبطين بهذا الطفل من الجدول الوسيط
        doctor_ids = (
            db.session.query(DoctorsChild.doctor_id)
            .filter(DoctorsChild.child_id == child_id)
            .all()
        )
        doctor_ids = [d[0] for d in doctor_ids]  # تحويل النتيجة إلى قائمة عادية
        print(1234)
        if not doctor_ids:
            return jsonify({"error": "لا يوجد أطباء مرتبطين بهذا الطفل."}), 404

        # 🔹 نجيب فقط المواعيد التابعة لهؤلاء الأطباء
        available_appointments = (
            db.session.query(DoctorAppointment)
            .filter(
                DoctorAppointment.doctor_id.in_(doctor_ids),
                DoctorAppointment.status == 'available',
                DoctorAppointment.day_of_week != None,
                DoctorAppointment.time != None
            )
            .order_by(DoctorAppointment.day_of_week.asc(), DoctorAppointment.time.asc())
            .all()
        )

        # 🔹 تجهيز النتائج للواجهة
        items = []
        for app in available_appointments:
            items.append({
                "id": app.appointment_id,
                "day": app.day_of_week,
                "datetime": str(app.time),
                "doctor_name": app.doctor.name if app.doctor else "غير معروف",
                "status": app.status
            })
        print(items)

        return jsonify({"items": items})

    except Exception as e:
        print("Error fetching appointments:", e)
        return jsonify({"error": "حدث خطأ أثناء تحميل المواعيد."}), 500

# 💡 يجب أن تكون هذه الدالة متاحة لديك وتقوم بحساب الإحصائيات
def get_dashboard_stats(doctor_id):

    return {"waiting_patients": "RELOAD", "seen_today": "RELOAD"}


@app.route('/api/appointment/complete', methods=['POST'])
def complete_appointment():

    try:
        data = request.get_json()
        child_id = data.get('child_id')
        doctor_id = session.get('doctor_id')  # نحتاج Doctor ID للفلترة

        if not child_id or not doctor_id:
            return jsonify({"error": "مُعرّف الطفل أو الطبيب مطلوب."}), 400

        # 1. 🎯 البحث عن سجل الحجز (ChildAppointment) الأحدث لهذا الطفل
        booking_record = (
            db.session.query(ChildAppointment)
            .filter(
                ChildAppointment.child_id == child_id,
            )
            .order_by(ChildAppointment.created_at.desc())
            .first()
        )

        if not booking_record:
            return jsonify({"error": "لم يتم العثور على سجل حجز لهذا الطفل."}), 404

        # 2. جلب وتحديث حالة الموعد الأصلي (DoctorAppointment)
        appointment = DoctorAppointment.query.get(booking_record.appointment_id)

        # 3. 🛡️ شروط التحقق من الصلاحية (موقعها الصحيح)
        if appointment.doctor_id != doctor_id:
            return jsonify({"error": "هذا الموعد لا يخص الطبيب الحالي."}), 403

        if appointment.status != 'booked':
            return jsonify({"error": f"حالة الموعد الحالية هي {appointment.status}. يجب أن تكون 'booked'."}), 400

        # 4. تحديث الحالة والحفظ في قاعدة البيانات
        appointment.status = 'completed'
        db.session.add(appointment)  # تأكيد ربط الكائن بالجلسة
        db.session.commit()

        print(f"✅ APPOINTMENT COMPLETED: Child ID {child_id} - Appt ID {appointment.appointment_id}")

        # 💡 نعود بإشارة إلى الواجهة الأمامية (Frontend) بأن الصفحة يجب أن تُحدث نفسها
        return jsonify({
            "message": "تم إكمال الموعد بنجاح.",
            "status": "completed",
            "reload_needed": True  # 👈 إشارة للإعادة تحميل
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ DB FAILED TO COMPLETE APPOINTMENT: {e}")
        return jsonify({"error": f"حدث خطأ داخلي أثناء إكمال الموعد: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)