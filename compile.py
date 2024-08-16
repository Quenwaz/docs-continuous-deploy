import py_compile
from python_obfuscator import obfuscator

source_file = "server.py"
# target_file = "server_encryption.py"
target_code = ""
# with open(source_file, 'r', encoding="utf-8") as fp:
#     target_code = obfuscator().obfuscate(code = fp.read())

# if target_code:
#     with open(target_file, 'w', encoding="utf-8") as fp:
#         fp.write(target_code)

py_compile.compile(source_file,'server.pyc')