from marshmallow import fields
from marshmallow import validate

from ops.extensions import marshmallow


class ResearchSchema(marshmallow.Schema):
    class Meta:
        fields = ("created_on", "id", "question", "answer")


class AddResearchSchema(marshmallow.Schema):
    question = fields.Str(
        required=True, validate=validate.Length(min=1, max=2000)
    )


research_schema = ResearchSchema()
researches_schema = ResearchSchema(many=True)
add_research_schema = AddResearchSchema()
