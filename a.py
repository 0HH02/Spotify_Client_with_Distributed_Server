from flask import Flask, request, jsonify
import whisper
import os

app = Flask(__name__)

# Cargar el modelo Whisper una vez al iniciar el servidor
print("Cargando el modelo Whisper...")
model = whisper.load_model("small")

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Recibe un archivo de audio y devuelve la transcripción utilizando Whisper.
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No se encontró el archivo de audio"}), 400

    audio_file = request.files['audio']
    filename = "uploaded_audio.wav"
    
    # Guardar el archivo temporalmente
    audio_file.save(filename)

    try:
        # Transcribir el audio
        print("Transcribiendo el audio...")
        result = model.transcribe(filename)

        # Eliminar el archivo después de procesarlo
        os.remove(filename)

        return jsonify({"transcription": result["text"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
