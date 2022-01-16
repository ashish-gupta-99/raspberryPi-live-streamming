from flask import Flask, render_template, Response
import io
import picamera
from threading import Condition


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
                self.buffer.seek(0)
                return self.buffer.write(buf)


def generate_frames():
    while True:
        try:
            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                    yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(str(e))


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

with picamera.PiCamera(framerate=35) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    try:
        camera.start_recording(output, format='mjpeg')
        # debug=True restarts the app and ropen the camera which will produces mmal error
        app.run("0.0.0.0",debug=False)
    finally:
        camera.stop_recording()
        camera.close()
