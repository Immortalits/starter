from flask import Blueprint, render_template, request, url_for
from flask.helpers import flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, redirect
import os
from python_cms.models.post import PostModel
from python_cms.forms.post_form import PostForm
import python_cms

pages_blueprint = Blueprint("pages", __name__)


@pages_blueprint.route("/")
def index():
  return render_template('index.html.j2')


@pages_blueprint.route('/about')
def about():
  return render_template('about.html.j2')


@pages_blueprint.route("/add", methods=['GET', 'POST'])
@login_required
def create_post():
  form = PostForm()
  if request.method == 'POST' and form.validate_on_submit():
    title = request.form.get('title')
    body = request.form.get('body')
    file = request.files['teaser_image']
    filename = secure_filename(file.filename)
    file.save(os.path.join(python_cms.ROOT_PATH, 'files_upload', filename))
    post = PostModel(title, body, current_user.get_id(), filename)
    post.save()
    flash(f'Post with title: {title} is created')
    return redirect(url_for('pages.create_post'))

  return render_template('create_post.html.j2', form=form)
