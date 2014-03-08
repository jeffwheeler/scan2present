import os
import web

import process

import tikz
import email_pdf

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

            rectified = process.prepare_img(input_path, output_path)

            web.last_upload = rectified
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
        user_data = web.input()

        if web.last_upload:
            web.slides.append(web.last_upload)

        print 'Generating PDFs'
        tikz.build_pdf(web.slides)

        print 'Sending to email address ', user_data.email
        email_pdf.send_pdf(user_data.email)

        # print 'Clearing'
        web.slides = []
        web.last_upload = None

        return 'Emailed!'


urls = (
    '/', 'index',
    '/sample_image', 'sample_image',
    '/save', 'save',
    '/email', 'email_me'
)

if __name__ == '__main__':
    web.last_upload = None
    web.slides = []

    app = web.application(urls, globals())
    app.run()
