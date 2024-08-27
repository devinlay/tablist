from flask import Flask, render_template, request, send_file
import main

app = Flask(__name__, template_folder="templates")
@app.route('/')
def hello():
    return render_template('index.html', message='Tablist')

@app.route('/generate-tabs', methods =['POST'])
def generate_tabs():
    link = request.form['link']
    file = main.main(link=link)
    return send_file(file, as_attachment= False, mimetype='application/pdf')


if __name__ == '__main__':
    app.run()