from flask import Flask, render_template, request, send_file
import main
import os
from apscheduler.schedulers.background import BackgroundScheduler

#def create_app():
app = Flask(__name__, template_folder="templates")

def cleanup_pdf_files(directory, file_extension='.pdf'):
    """
    Delete all files with a specific extension from a directory.
    """
    for filename in os.listdir(directory):
        if filename.endswith(file_extension):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")

scheduler = BackgroundScheduler()
# Schedule the cleanup job to run every hour
scheduler.add_job(cleanup_pdf_files, 'interval', hours=1, args=[os.getcwd(), '.pdf'])
scheduler.start()

@app.route('/')
def hello():
    return render_template('index.html', message='Tab-list')

@app.route('/generate-tabs', methods =['POST'])
def generate_tabs():
    link = request.form['link']
    file= main.main(link=link)
        # Send the file to the client
    response = send_file(file[0], as_attachment=False, download_name = file[1], mimetype='application/pdf')
    return response
    
    #return app

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80)


