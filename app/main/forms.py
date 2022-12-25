
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, InputRequired


class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired(), InputRequired()])
    submit = SubmitField('Submit')
