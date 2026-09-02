from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    local_mode = app.config.get('LOCAL_DEVELOPMENT', False)
    app.run(
        host='127.0.0.1' if local_mode else '0.0.0.0',
        port=5001,
        debug=not local_mode,
        use_reloader=not local_mode,
    )
