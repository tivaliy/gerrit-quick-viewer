from flask import Flask


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

    @app.context_processor
    def utility_processor():
        def message_category_mapper(severity_level):
            category_mapper = {'error': 'alert-danger',
                               'note': 'alert-info'}
            return category_mapper[severity_level]

        return dict(get_category=message_category_mapper)

    return app
