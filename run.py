from Backend.app import app, load_deepfake_model
import webbrowser
import threading

if __name__ == '__main__':
    load_deepfake_model()
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
