from flask import Flask, render_template, redirect, url_for
from server.database import init_db, init_app, get_db
from server.routes.tasks import tasks_bp
from server.routes.profile import profile_bp
from server.routes.reflections import reflections_bp
from server.routes.breaks import breaks_bp
from server.routes.ai import ai_bp


def create_app(test_config=None):
    app = Flask(__name__, template_folder='templates', static_folder='static')

    if test_config:
        app.config.update(test_config)

    init_app(app)

    with app.app_context():
        init_db()

    app.register_blueprint(tasks_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(reflections_bp)
    app.register_blueprint(breaks_bp)
    app.register_blueprint(ai_bp)

    @app.route('/')
    def index():
        profile = get_db().execute(
            'SELECT * FROM user_profile ORDER BY id LIMIT 1'
        ).fetchone()
        if profile is None or not profile['onboarding_complete']:
            return redirect(url_for('onboarding'))
        return render_template('index.html', profile=profile)

    @app.route('/onboarding')
    def onboarding():
        return render_template('onboarding.html')

    @app.route('/reflect')
    def reflect():
        return render_template('reflect.html')

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
