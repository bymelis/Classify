
from flask import render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime
from Classify import app, db
from Classify.models import Assignment, User, Class, Submission, class_students
from werkzeug.utils import secure_filename
from .services.plagiarism_checker import PlagiarismChecker
import os

plagiarism_checker = PlagiarismChecker()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'assignments')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/landing')
def landing_page():
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        role = request.form.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'error')
            return redirect(url_for('signup_page'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup_page'))

        user = User(
            name=name,
            email=email,
            role=role
        )
        user.set_password(password)

        if role == 'teacher':
            user.institution = request.form.get('institution')
            user.faculty = request.form.get('faculty')
        else:
            user.department = request.form.get('department')

        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Account created successfully! Welcome to Classify!', 'success')
            return redirect(url_for('dashboard_page'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('signup_page'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            # Redirect based on user role
            if user.role == 'student':
                return redirect(url_for('dashboard_page'))  # Use the main dashboard route
            else:
                return redirect(url_for('dashboard_page'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login_page'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    if current_user.role == 'teacher':
        # Get assignments created by this teacher
        assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher_dashboard.html',
                             assignments=assignments,
                             classes=classes,
                             active_tab='assignments')

    # Student dashboard logic remains the same
    assignments = Assignment.query.join(Class).join(
        class_students
    ).filter(class_students.c.student_id == current_user.id).all()

    submitted_assignments = set()
    submissions_data = {}

    submissions = Submission.query.filter_by(student_id=current_user.id).all()
    for submission in submissions:
        submitted_assignments.add(submission.assignment_id)
        submissions_data[submission.assignment_id] = {
            'grade': submission.grade,
            'feedback': submission.feedback
        }

    return render_template('student_dashboard.html',
                          assignments=assignments,
                          submitted_assignments=submitted_assignments,
                          submissions_data=submissions_data,
                          active_tab='assignments')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing_page'))

@app.route('/classes')
@login_required
def classes():
    if current_user.role == 'teacher':
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher_classes.html', classes=classes, active_tab='classes')
    else:
        enrolled_classes = current_user.classes_enrolled
        return render_template('student_classes.html', classes=enrolled_classes, active_tab='classes')

@app.route('/create_class', methods=['POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        return redirect(url_for('classes'))

    name = request.form.get('name')
    description = request.form.get('description')

    new_class = Class(
        name=name,
        description=description,
        code=Class.generate_code(),
        teacher_id=current_user.id
    )

    db.session.add(new_class)
    db.session.commit()

    flash('Class created successfully!', 'success')
    return redirect(url_for('classes'))

@app.route('/join_class', methods=['POST'])
@login_required
def join_class():
    if current_user.role != 'student':
        return redirect(url_for('classes'))

    code = request.form.get('code')
    class_to_join = Class.query.filter_by(code=code).first()

    if not class_to_join:
        flash('Invalid class code!', 'error')
        return redirect(url_for('classes'))

    if current_user in class_to_join.students:
        flash('You are already enrolled in this class!', 'error')
        return redirect(url_for('classes'))

    class_to_join.students.append(current_user)
    db.session.commit()

    flash('Successfully joined the class!', 'success')
    return redirect(url_for('classes'))


@app.route('/create_assignment', methods=['POST'])
@login_required
def create_assignment():
    if current_user.role != 'teacher':
        flash('Only teachers can create assignments', 'error')
        return redirect(url_for('dashboard_page'))

    title = request.form.get('title')
    description = request.form.get('description')
    class_id = request.form.get('class_id')
    due_date = request.form.get('due_date')

    if not all([title, description, class_id, due_date]):
        flash('All fields are required', 'error')
        return redirect(url_for('dashboard_page'))

    try:
        due_date = datetime.fromisoformat(due_date)
        assignment = Assignment(
            title=title,
            description=description,
            class_id=class_id,
            due_date=due_date,
            teacher_id=current_user.id
        )

        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating assignment. Please try again.', 'error')

    return redirect(url_for('dashboard_page'))


@app.route('/submit_assignment', methods=['POST'])
@login_required
def submit_assignment():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    assignment_id = request.form.get('assignment_id')
    file = request.files.get('submission_file')
    notes = request.form.get('notes', '')  # Get the notes from the form

    if not assignment_id or not file:
        return jsonify({'error': 'Please provide a file for submission'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    assignment = Assignment.query.get_or_404(assignment_id)

    # Check if the student is enrolled in the class
    if current_user not in assignment.class_.students:
        return jsonify({'error': 'You are not enrolled in this class'}), 403

    # Check if the assignment is past due
    if datetime.utcnow() > assignment.due_date:
        return jsonify({'error': 'This assignment is past due'}), 400

    # Handle file upload
    filename = secure_filename(f"{current_user.id}_{assignment_id}_{file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': 'Error saving file'}), 500

    try:
        existing_submission = Submission.query.filter_by(
            student_id=current_user.id,
            assignment_id=assignment_id
        ).first()

        if existing_submission:
            if existing_submission.file_path and os.path.exists(existing_submission.file_path):
                try:
                    os.remove(existing_submission.file_path)
                except:
                    pass
            existing_submission.content = notes  # Save the notes
            existing_submission.file_path = file_path
            existing_submission.submitted_at = datetime.utcnow()
        else:
            submission = Submission(
                content=notes,  # Save the notes
                file_path=file_path,
                student_id=current_user.id,
                assignment_id=assignment_id
            )
            db.session.add(submission)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'error': 'Database error'}), 500

@app.route('/submissions')
@login_required
def submissions():
    # Fetch assignments and their submissions
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()

    assignments_data = []
    for assignment in assignments:
        submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
        assignments_data.append({
            'assignment': assignment,
            'submissions': submissions
        })

    return render_template('submissions.html',
                           assignments=assignments_data,
                           active_tab='submissions')


@app.route('/get_assignment/<int:assignment_id>')
@login_required
def get_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    # Get existing submission for this student
    submission = Submission.query.filter_by(
        student_id=current_user.id,
        assignment_id=assignment_id
    ).first()

    submission_data = None
    if submission:
        submission_data = {
            'submitted_at': submission.submitted_at.isoformat(),
            'grade': submission.grade,
            'feedback': submission.feedback,
            'file_path': submission.file_path
        }

    assignment_data = {
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat(),
        'class_name': assignment.class_.name,
        'submission': submission_data
    }

    return jsonify(assignment_data)

@app.route('/grade_submission', methods=['POST'])
@login_required
def grade_submission():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    submission_id = request.form.get('submission_id')
    grade = request.form.get('grade')
    feedback = request.form.get('feedback')

    submission = Submission.query.get_or_404(submission_id)

    # Verify the teacher owns this assignment
    if submission.assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        submission.grade = float(grade)
        submission.feedback = feedback
        submission.graded_at = datetime.utcnow()
        db.session.commit()
        flash('Submission graded successfully!', 'success')
        return jsonify({'success': True})
    except ValueError:
        return jsonify({'error': 'Invalid grade format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/download_submission/<int:submission_id>')
@login_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    # Check permissions (either the teacher who owns the assignment or the student who submitted)
    if not (
            (current_user.role == 'teacher' and submission.assignment.teacher_id == current_user.id) or
            (current_user.role == 'student' and submission.student_id == current_user.id)
    ):
        return jsonify({'error': 'Unauthorized'}), 403

    if not submission.file_path or not os.path.exists(submission.file_path):
        flash('File not found', 'error')
        return redirect(url_for('dashboard_page'))

    try:
        return send_file(
            submission.file_path,
            as_attachment=True,
            download_name=os.path.basename(submission.file_path)
        )
    except Exception as e:
        flash('Error downloading file', 'error')
        return redirect(url_for('dashboard_page'))


@app.route('/get_submission/<int:submission_id>')
@login_required
def get_submission(submission_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    submission = Submission.query.get_or_404(submission_id)

    # Verify the teacher owns this submission's assignment
    if submission.assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    submission_data = {
        'id': submission.id,
        'content': submission.content,
        'submitted_at': submission.submitted_at.isoformat(),
        'student_name': submission.student.name,
        'assignment_title': submission.assignment.title,
        'file_path': submission.file_path,
        'grade': submission.grade,
        'feedback': submission.feedback
    }

    return jsonify(submission_data)


@app.route('/get_all_submissions/<int:assignment_id>')
@login_required
def get_all_submissions(assignment_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    submissions_data = [{
        'id': s.id,
        'student_name': s.student.name,
        'submitted_at': s.submitted_at.isoformat(),
        'grade': s.grade,
        'content': s.content,
        'file_path': s.file_path
    } for s in submissions]

    return jsonify(submissions_data)


@app.route('/delete_assignment/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    assignment = Assignment.query.get_or_404(assignment_id)

    # Verify the teacher owns this assignment
    if assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Delete associated submissions first
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        for submission in submissions:
            # Delete submission files if they exist
            if submission.file_path and os.path.exists(submission.file_path):
                try:
                    os.remove(submission.file_path)
                except:
                    pass
            db.session.delete(submission)

        # Delete the assignment
        db.session.delete(assignment)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/update_assignment/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    assignment = Assignment.query.get_or_404(assignment_id)

    # Verify the teacher owns this assignment
    if assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    try:
        assignment.title = data['title']
        assignment.description = data['description']
        assignment.due_date = datetime.fromisoformat(data['due_date'])
        assignment.class_id = data['class_id']

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/check_plagiarism/<int:submission_id>', methods=['POST'])
@login_required
def check_plagiarism(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    # Ensure the user has permission to check this submission
    if not (current_user.role == 'teacher' and submission.assignment.teacher_id == current_user.id):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    # Get the file path from the submission
    if not submission.file_path or not os.path.exists(submission.file_path):
        return jsonify({
            'status': 'error',
            'message': 'Submission file not found'
        }), 404

    # Submit the file for plagiarism checking
    try:
        result = plagiarism_checker.check_submission(
            file_path=submission.file_path,
            student_name=submission.student.name
        )

        if result['status'] == 'submitted':
            # Store the scan ID in the submission record
            submission.plagiarism_scan_id = result['scan_id']
            submission.plagiarism_status = 'pending'  # Add this field to your Submission model
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Plagiarism check initiated - results will be available shortly',
                'scan_id': result['scan_id']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Failed to initiate plagiarism check')
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/plagiarism_results/<int:submission_id>', methods=['GET'])
@login_required
def get_plagiarism_results(submission_id):
    try:
        submission = Submission.query.get_or_404(submission_id)

        # Check if we have a scan ID
        if not submission.plagiarism_scan_id:
            return jsonify({
                'status': 'error',
                'message': 'No plagiarism scan found for this submission'
            }), 404

        # Get results from Copyleaks
        results = plagiarism_checker.get_results(submission.plagiarism_scan_id)

        if results['status'] == 'completed':
            # Store the results in the database
            submission.plagiarism_status = 'completed'
            submission.plagiarism_results = results['results']  # You'll need to add this field
            db.session.commit()

            return jsonify({
                'status': 'completed',
                'results': results['results'],
                'message': 'Plagiarism check completed'
            })
        elif results['status'] == 'error':
            return jsonify({
                'status': 'error',
                'message': results.get('message', 'Failed to retrieve results')
            }), 500
        else:
            return jsonify({
                'status': 'pending',
                'message': 'Scan still in progress, please check back later'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
