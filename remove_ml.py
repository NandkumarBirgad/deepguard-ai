import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('def get_models():'):
        skip = True
    if line.startswith('@app.route("/uploads/<filename>")'):
        skip = False
        new_lines.append('@app.route("/")\n')
        new_lines.append('def index():\n')
        new_lines.append('    return render_template("index.html")\n\n\n')

    if not skip:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
