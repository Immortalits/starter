from flask import Blueprint, render_template, request, url_for, send_from_directory
from flask.helpers import flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, redirect
import os
from python_cms.models.post import PostModel
from python_cms.forms.post_form import PostForm
import python_cms
import html

from flask_ckeditor import upload_success, upload_fail

import bleach
# https://bleach.readthedocs.io/en/latest/

pages_blueprint = Blueprint("pages", __name__)


@pages_blueprint.route("/")
def index():
  posts = PostModel.get_all()
  return render_template('index.html.j2', posts=posts)


@pages_blueprint.route('/about')
def about():
  return render_template('about.html.j2')


@pages_blueprint.route("/add", methods=['GET', 'POST'])
@login_required
def create_post():
  form = PostForm()
  if request.method == 'POST' and form.validate_on_submit():
    unescaped_body = html.unescape(request.form.get('body'))
    clean_body = bleach.clean(unescaped_body,
                              tags=bleach.sanitizer.ALLOWED_TAGS +
                              ['div', 'br', 'p', 'h1', 'h2', 'img', 'h3'],
                              attributes=['src', 'alt', 'style'])
    title = request.form.get('title')
    # body = clean_body
    file = request.files['teaser_image']  #bekéri a fájlokat
    if file:
      filename = secure_filename(file.filename)
      file.save(os.path.join(python_cms.ROOT_PATH, 'files_upload', filename))
    else:
      filename = ""

    post = PostModel(title, clean_body, current_user.get_id(), filename)
    post.save()
    flash(f'Post with title: {title} is created')
    return redirect(url_for('pages.create_post'))

  return render_template('create_post.html.j2', form=form)


@pages_blueprint.route('/files/<path:filename>')
def uploaded_files(filename):
  path = os.path.join(python_cms.ROOT_PATH, 'files_upload')
  return send_from_directory(path, filename)


@pages_blueprint.route("/post/<string:post_id>")
def single_post(post_id):
  post = PostModel.get(post_id)
  return render_template('post.html.j2', post=post)


@pages_blueprint.route("/post/delete/<string:post_id>")
@login_required
def delete_post(post_id):
  post = PostModel.get(post_id)

  if post.author_id == current_user.id:
    #töröljük a postot
    post.delete()

    #flash üzenet
    flash(f"Post with title {post.title} is deleted!")
    return redirect(url_for("pages.index"))
  else:
    return "You are not authorized to delete this content.", 403


@pages_blueprint.route("/post/edit/<string:post_id>", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
  if request.method == "GET":
    post = PostModel.get(post_id)
    if post.author_id == current_user.id:
      #saját post
      form = PostForm()
      form.title.data = post.title
      form.teaser_image.data = post.teaser_image
      form.body.data = post.body
      form.submit.label.text = "Save"

      return render_template('create_post.html.j2',
                             form=form,
                             edit=True,
                             post_id=post_id)

    else:
      return "You are not authorized to edit this content!", 403
  elif request.method == "POST":
    unescaped_body = html.unescape(request.form.get('body'))
    clean_body = bleach.clean(unescaped_body,
                              tags=bleach.sanitizer.ALLOWED_TAGS +
                              ['div', 'br', 'p', 'h1', 'h2', 'img', 'h3'],
                              attributes=['src', 'alt', 'style'])

    post = PostModel.get(post_id)
    post.title = request.form.get('title')
    post.body = clean_body

    # body = clean_body
    file = request.files['teaser_image']  #bekéri a fájlokat

    if file:
      filename = secure_filename(file.filename)
      file.save(os.path.join(python_cms.ROOT_PATH, 'files_upload', filename))
    else:
      filename = request.form.get("original_teaser_image")

    post.teaser_image = filename

    post.save()
    flash(f'Post with title: {post.title} is updated')
    return redirect(url_for('pages.index'))


@pages_blueprint.route('/upload', methods=['POST'])
def upload():
  f = request.files.get('upload')
  # Add more validations here
  extension = f.filename.split('.')[-1].lower()
  if extension not in ['jpg', 'gif', 'png', 'jpeg']:
    return upload_fail(message='Image only!')
  file_name = os.path.join(python_cms.ROOT_PATH, 'files_upload', f.filename)
  f.save(os.path.join(file_name))
  url = url_for('pages.uploaded_files', filename=f.filename)
  return upload_success(url=url)  # return upload_success call