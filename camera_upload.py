import cv2
import requests
import os
from flask import Flask, request, jsonify

# Серверная часть (Flask)
app = Flask(__name__)

# Папка для хранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Устанавливаем URL-статический путь, чтобы доступ к файлам был через веб
app.config['STATIC_URL_PATH'] = '/uploads'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Нет файла в запросе", 400
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400

    # Сохранение файла
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Формируем ссылку на файл, который теперь доступен через веб
    file_url = f"http://127.0.0.1:5000/uploads/{file.filename}"

    # Возвращаем ссылку на файл
    return jsonify({"file_url": file_url}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return app.send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == 'main':
    app.run(debug=True, use_reloader=False)  # use_reloader=False чтобы избежать двойного запуска


# Клиентская часть (захват изображения с камеры и отправка на сервер)
def capture_image():
    # Открытие камеры (по умолчанию камера с индексом 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Не удалось открыть камеру.")
        return None

    # Захват одного кадра
    ret, frame = cap.read()
    if not ret:
        print("Не удалось захватить кадр.")
        cap.release()
        return None

    # Сохранение кадра в файл
    filename = "captured_image.jpg"
    cv2.imwrite(filename, frame)

    # Закрытие камеры
    cap.release()

    return filename

def send_image_to_server(image_path):
    # URL сервера (замени на свой сервер)
    url = "http://127.0.0.1:5000/upload"
    
    # Открытие изображения и отправка на сервер
    with open(image_path, 'rb') as img_file:
        files = {'file': img_file}
        response = requests.post(url, files=files)
    
    # Проверка ответа от сервера
    if response.status_code == 200:
        file_url = response.json().get('file_url')
        print(f"Изображение успешно отправлено! Ссылка на файл: {file_url}")
    else:
        print(f"Ошибка при отправке изображения: {response.status_code}")

if __name__ == "main":
    # Запуск сервера в отдельном процессе
    from threading import Thread
    server_thread = Thread(target=lambda: app.run(debug=True, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

    # Даем серверу немного времени на запуск
    import time
    time.sleep(2)

    # Захват изображения с камеры
    image_path = capture_image()

    # Если изображение успешно захвачено, отправляем его на сервер
    if image_path:
        send_image_to_server(image_path)