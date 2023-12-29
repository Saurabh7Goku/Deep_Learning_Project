from flask import Flask, render_template, Response, request
import socketio
import tensorflow as tf
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired
import cv2
import numpy as np
import imageio
from fun.invisibleMinds import *

app = Flask(__name__)
app.config['SECRET_KEY'] = '4cf659de047f5ec423725d1574c942e9'
violence_detections = []

# Your model loading code here
model = videoFightModel2(tf, wight='invisibleminds.hdfs')

class VideoForm(FlaskForm):
    video_url = StringField('Video URL')
    video_file = FileField('Upload Video File')
    submit = SubmitField('Start Analysis')



def resize(frame, size=(160, 160)):
    # Resize the frame to the specified size
    return cv2.resize(frame, size)

def gen(video_source, model):
    vid = imageio.get_reader(video_source, 'ffmpeg')

    i = 0
    frames = np.zeros((30, 160, 160, 3), dtype=np.float16)
    old = []
    j = 0

    for frame in vid.iter_data():
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert imageio frame to OpenCV format

        font = cv2.FONT_HERSHEY_SIMPLEX
        if i > 29:
            ysdatav2 = np.zeros((1, 30, 160, 160, 3), dtype=np.float16)
            ysdatav2[0][:][:] = frames
            predaction = pred_fight(model, ysdatav2, acuracy=0.96)
            if predaction[0]:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                vio = cv2.VideoWriter("./videos/output-"+str(j)+".avi", fourcc, 10.0, (frame.shape[1], frame.shape[0]))
                print('Violence detected here ...')
                print("timestamp is: ", i * vid.get_meta_data()['duration'] / len(vid))
                for x in old:
                    vio.write(x)
                vio.release()
                cv2.putText(frame, 
                            'Violence Detected!!!', 
                            (100, 200), 
                            font, 3, 
                            (238, 75, 43), 
                            5, 
                            cv2.LINE_4)
                 # Store violence detection information
                # detection_info = {
                #     'timestamp': str(cap.get(cv2.CAP_PROP_POS_MSEC)),
                #     'video_url': f'/videos/output-{len(violence_detections)}.mp4'
                # }
                # violence_detections.append(detection_info)

                # Update the sidebar dynamically
                # update_sidebar()        
            i = 0
            j += 1
            frames = np.zeros((30, 160, 160, 3), dtype=np.float16)
            old = []
        else:
            frm = resize(frame, (160, 160))
            old.append(frame)
            frm = np.expand_dims(frm, axis=0)
            if np.max(frm) > 1:
                frm = frm / 255.
            frames[i][:] = frm
            i += 1

        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    vid.close()

# def update_sidebar():
#     global violence_detections
#     data = {
#         'violence_detections': violence_detections
#     }
#     # Broadcast the updated data to all connected clients
#     socketio.emit('update_sidebar', data)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = VideoForm()
    if form.validate_on_submit():
        video_url = form.video_url.data
        video_file = form.video_file.data
        if video_url:
            video_source = video_url
        elif video_file:
            video_source = save_uploaded_file(video_file)
        else:
            # Handle case where neither URL nor file is provided
            return render_template('index.html', form=form)

        return render_template('index.html', form=form, video_source=video_source)

    return render_template('index.html', form=form)

@app.route('/video_feed')
def video_feed():
    video_source = request.args.get('video_source', 0)
    return Response(gen(video_source, model), mimetype='multipart/x-mixed-replace; boundary=frame')

def save_uploaded_file(file):
    # Save the uploaded file and return the file path
    # You might want to save it in a folder and return the path
    # For simplicity, this example saves the file in the current working directory
    file_path = file.filename
    file.save(file_path)
    return file_path

if __name__ == '__main__':
    app.run(debug=True)
