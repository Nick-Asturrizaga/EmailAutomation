from flask import jsonify


def register_routes(app, db):
    @app.route("/health")
    def health():
        return jsonify({
            'status': 'ok'
        })
