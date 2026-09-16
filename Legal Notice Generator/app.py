from flask import (Flask,render_template)
from config.config import (SECRET_KEY,MAX_CONTENT_LENGTH)
from routes.chatbot import chatbot_bp
from routes.documents import documents_bp
from routes.forms import forms_bp
from routes.voice import voice_bp
from utils.file_cleanup import start_cleanup

start_cleanup("generated/blank")
start_cleanup("generated/filled")
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    # -----------------------------------------------------
    # Register Routes
    # -----------------------------------------------------
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(voice_bp)
    # -----------------------------------------------------
    # Home Page
    # -----------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")
    # -----------------------------------------------------
    # Health Check
    # -----------------------------------------------------
    @app.route("/health")
    def health():
        return {"status": "ok","application": "ALGDSS"}
    return app
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1",port=5000,debug=True)