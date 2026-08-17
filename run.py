import os
from app import create_app

app = create_app()

# Serve static files efficiently in production using WhiteNoise
from whitenoise import WhiteNoise
app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder, prefix=app.static_url_path + '/')

if __name__ == '__main__':
    # Run server on port read from environment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
