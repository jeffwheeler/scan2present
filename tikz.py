import subprocess

header = '''
\\documentclass{beamer}
\\usepackage{tikz}

\\usetikzlibrary{backgrounds}

\\begin{document}
'''

footer = '''
\\end{document}
'''

frame_header = '''
\\begin{frame}
\\begin{tikzpicture}[show background rectangle]
'''

frame_footer = '''
\\end{tikzpicture}
\\end{frame}
'''

def build_frame(shapes):
    s = frame_header
    # s += '\path[draw] (0,0) -- (0,2.124) -- (10,8) -- cycle;'
    for shape in shapes:
        s += '\\path[draw] '
        s += ' -- '.join(['(%f, %f)' % v for v in shape])
        s += ' -- cycle;\n'
    s += frame_footer

    return s

def build_tex(slides):
    s = header
    for slide in slides:
        s += build_frame(slide)
    s += footer

    return s

def build_pdf(slides):
    print slides

    s = build_tex(slides)
    print s

    tikz_filename = './tikz_gen/slides.tex'
    f = open(tikz_filename, 'w')
    f.write(s)
    f.close()

    null = open('/dev/null', 'w')
    p = subprocess.Popen(['pdflatex', 'slides.tex'], cwd='./tikz_gen/', stdout=null)
    p.wait()

if __name__ == '__main__':
    build_pdf(['slide1', 'slide2'])
