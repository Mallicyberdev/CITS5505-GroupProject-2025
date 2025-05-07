from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class DiaryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField(
        "Save Diary"
    )  # This submit can be hidden in template if using FAB