from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from models import Student, User

# Blueprint for admin routes
admin_routes = Blueprint('admin', __name__)


@admin_routes.route('/admin', methods=['GET'])
def admin_dashboard():
    students = Student.query.all()
    return render_template('admin/admin_dashboard.html', students=students)


@admin_routes.route('/admin/add_student', methods=['POST'])
def add_student():
    user_id = request.form['user_id']
    class_id = request.form['class_id']
    parent_id = request.form['parent_id']
    uid = request.form['uid']

    new_student = Student(user_id=user_id, class_id=class_id, parent_id=parent_id, uid=uid)
    db.session.add(new_student)
    db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))


# Blueprint for user routes (for students, teachers, etc.)
user_routes = Blueprint('user', __name__)


@user_routes.route('/user/<int:user_id>', methods=['GET'])
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user/admin_dashboard.html', user=user)
