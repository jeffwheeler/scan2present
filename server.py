import os
import web

import process

slides = []
last_upload = None

class index:
    def GET(self):
        return 'Hello world'

class sample_image:
    def POST(self):
        web.header('Content-Type', 'image/jpeg')
        x = web.input(uploadedfile={})

        if 'uploadedfile' in x:
            input_path = os.path.join('.', 'input-images', 'uploaded', x.uploadedfile.filename)
            output_path = os.path.join('.', 'output-images', x.uploadedfile.filename)
            print input_path, output_path

            fout = open(input_path, 'w')
            fout.write(x.uploadedfile.file.read())
            fout.close()

            process.prepare_img(input_path, output_path)
            web.last_upload = output_path
            print 'last_upload', web.last_upload

            return open(output_path).read()

class save:
    def GET(self):
        if web.last_upload:
            web.slides.append(web.last_upload)
            print web.slides
        else:
            print 'No last upload'

        return 'Success!'

class email_me:
    def GET(self):
        pass

urls = (
    '/', 'index',
    '/sample_image', 'sample_image',
    '/save', 'save'
)

if __name__ == '__main__':
    web.last_upload = None
    web.slides = []

    app = web.application(urls, globals())
    app.run()
