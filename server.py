import logging
from flask import Flask,send_from_directory,current_app, request, jsonify,abort
import os,subprocess,shutil, json


current_server_path = os.path.abspath(os.path.dirname(__file__))
wiki_path = os.path.join(current_server_path, "wiki")
sidebar_content = []
app_config = dict()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__,template_folder=os.path.join(current_server_path, "front"))


@app.before_request
def log_request_info():
    app.logger.info('%s %s %s',request.remote_addr, request.method, request.full_path)


@app.route('/')
@app.route('/<path:path>')
def index(path=''):
    resource = os.path.join(current_app.template_folder, path)
    
    if os.path.exists(resource):
        if os.path.isdir(resource):
            return send_from_directory(resource, 'index.html')
        else:
            if path.endswith("_sidebar.md"): 
                content = filter_sidebar_content()
                return "".join(content)
            return send_from_directory(current_app.template_folder, path)
    else:
        if not access(lambda rulekey: path.startswith(rulekey)): return "> 无权限访问"
        return send_from_directory(wiki_path, path)
    
    

@app.route('/algwiki/update',methods=['POST'])
def update():
    load_config()
    # args = request.args
    repository= request.json["repository"]
    pull_markdown_from_git(repository["git_ssh_url"])
    rename_file()
    update_sidebar()
    reset_coverpage()
    
    return jsonify({
        "status": True
    })


def load_config():
    global app_config
    with open(os.path.join(current_server_path, "config.json"), 'r', encoding="utf-8") as fp:
        app_config = json.load(fp)
    
def build_sidebar_tpl(data:dict, level, ppath, result:list):    
    for k, v in data.items():
        key_is_file = k.find(".") != -1
        title = k if v or not key_is_file else "".join(k.split('.')[:-1])
        title = title.replace(" ", "_")
        result.append("{}- [{}]({})".format("\t" * level, title, ppath + k if key_is_file else ppath + k + '/README.md'))
        if v:
            build_sidebar_tpl(v, level + 1, ppath + k + '/', result)

def access(resource_filter):
    for rulekey, ips in app_config["permission"].items():
        if resource_filter(rulekey) and not request.remote_addr in ips:
            return False
    return True

def filter_sidebar_content():
    return list(filter(lambda resource: access(lambda rulekey: resource.find(rulekey) != -1), sidebar_file_content()))

def sidebar_file_content():
    global sidebar_content
    if len(sidebar_content) == 0:
        with open(os.path.join(current_server_path, "front", "_sidebar.md"), 'r', encoding="utf-8") as fp:
            sidebar_content = fp.readlines()
    
    return sidebar_content

def update_sidebar():
    
    list_wiki = dict()
    for root, dirs, names in os.walk(wiki_path, topdown=True):
        curdir = os.path.relpath(root, wiki_path)
        if [True for f in app_config["fileFilter"]["ignName"] if curdir.endswith(f) or curdir.startswith(f)]:
            continue
        
        pdir = os.path.relpath(root,wiki_path)
        
        curwiki = list_wiki
        if root != wiki_path:
            for d in pdir.split(os.sep):
                curwiki = curwiki[d]
        subwiki = list(filter(lambda n: not any([True for f in app_config["fileFilter"]["ignName"] if n == f]), dirs))
        subwiki.extend(list(filter(lambda n: not n.lower() in app_config["fileFilter"]["ignName"] and any(True for f in app_config["fileFilter"]["supportedExt"] if n.lower().endswith(f)), names)))
        curwiki.update( {n:dict() for n in subwiki})
        
    level = 0
    ppath = "/"
    new_sidebar_list = ["- [首页](/)"]
    build_sidebar_tpl(list_wiki, level, ppath,new_sidebar_list)
    with open(os.path.join(current_server_path, "front", "_sidebar.md"), 'w', encoding="utf-8") as fp:
        fp.writelines([item + "\n" for item in new_sidebar_list])
    
    global sidebar_content
    sidebar_content = []
    
    


def pull_markdown_from_git(git_ssh_url):
    try:
        if os.listdir(wiki_path):
            subprocess.check_output(['git', '-C', wiki_path, 'pull']) 
        else:
            subprocess.check_output(['git', 'clone', git_ssh_url, wiki_path])
        return True
    except subprocess.CalledProcessError as e:
        print("Error executing git pull:", e)
    
    return False


def rename_file():
    
    for root, _, names in os.walk(wiki_path, topdown=True):
        curdir = os.path.relpath(root, wiki_path)
        if [True for f in app_config["fileFilter"]["ignName"] if curdir.endswith(f) or curdir.startswith(f)]:
            continue
        
        for n in names:
            if all(False for f in app_config["fileFilter"]["supportedExt"] if not n.lower().endswith(f)):
                continue
            
            if n.find(" ") == -1:
                continue
            
            os.rename(os.path.join(root, n),os.path.join(root, n.replace(" ","_")))
            

def reset_coverpage():
    readmes = list(filter(lambda item : item.lower().endswith("readme.md"), os.listdir(wiki_path)))
    if not readmes:
        return
    
    anchor = ""
    with open(os.path.join(wiki_path, readmes[0]), 'r', encoding="utf-8") as fp:
        for line in fp.readlines():
            if line.startswith("#"):
                anchor = line
                break
    
    if not anchor:
        return

    content = ""
    with open(os.path.join(current_server_path, "front", "_coverpage_tpl.md"), 'r', encoding="utf-8") as fp:
        content = fp.read()
        
    if not content:
        return 
    
    if anchor.endswith("\n"):anchor = anchor[:-1]
    with open(os.path.join(current_server_path, "front", "_coverpage.md"), 'w', encoding="utf-8") as fp:
        fp.write(content.replace("{{Start}}",anchor.replace(" ", "")))
    

if __name__ == "__main__":
    import sys
    load_config()
    port = 80 if len(sys.argv) < 2 else int(sys.argv[1])
    host = "0.0.0.0"
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
        
    except Exception as e:
        print(e)
        app.run(host=host, port=port, debug=False)
