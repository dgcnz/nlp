from flask import Flask, Blueprint, request, jsonify, make_response
from lib.ner import parse_date, process

bp = Blueprint('api/nlp', __name__, template_folder='templates')


@bp.route("/")
def index():
    return "<h1>Welcome to the api/nlp endpoint. Refer to the documentation for help."


@bp.route("/process")
def ar_process():
    sent = request.args.get('sent')
    if sent is not None and sent != "":
        body = process(sent)
        code = 200
    else:
        body = {"message": "Bad Request"}
        code = 400
    res = make_response(jsonify(body), code)
    return res


@bp.route("/parse_date")
def ar_parse_date():
    sent = request.args.get('sent')
    if sent is not None and sent != "":
        body = parse_date(sent)
        code = 200
    else:
        body = {"message": "Bad Request"}
        code = 400
    res = make_response(jsonify(body), code)
    return res


if __name__ == "__main__":
    app = Flask(__name__)
    app.register_blueprint(bp, url_prefix='/api/nlp')
    app.run(host='0.0.0.0')
