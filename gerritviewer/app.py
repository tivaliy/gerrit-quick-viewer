from flask import Flask, render_template


def create_app(config_file):
    app = Flask(__name__)
    app.config.from_object(config_file)

    # import blueprints
    from gerritviewer.views.accounts import accounts
    from gerritviewer.views.groups import groups
    from gerritviewer.views.home import home
    from gerritviewer.views.plugins import plugins
    from gerritviewer.views.projects import projects

    # register blueprints
    app.register_blueprint(accounts)
    app.register_blueprint(groups)
    app.register_blueprint(home)
    app.register_blueprint(plugins)
    app.register_blueprint(projects)

    # register error handlers
    register_errorhandlers(app)

    @app.context_processor
    def utility_processor():
        def message_category_mapper(severity_level):
            category_mapper = {'error': 'alert-danger',
                               'note': 'alert-info'}
            return category_mapper[severity_level]

        return dict(get_category=message_category_mapper)

    return app


def register_errorhandlers(app):
    def render_error(e):
        return render_template('errors/%s.html' % e.code,
                               error=e), e.code

    for e in (401, 404, 500):
        app.errorhandler(e)(render_error)
