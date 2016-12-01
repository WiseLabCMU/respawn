#!/usr/bin/python

from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import subprocess

doc_root = 'www'
ds_root = 'bt_datastore'

class GetHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
       
        # parse request path
        # FIX: "../" issue
        parsed_path = urlparse.urlparse(self.path)
        fpath = doc_root + parsed_path.path
        fname = parsed_path.path.split('/')[-1]
        if('.' in fname): fext = fname.split('.')[-1] 
        else: fext = ''
   
        # handle info.json request
        if(parsed_path.path == '/info.json'):
            cmd = ds_root + '/info store.kvs -r 1'
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            (out, err) = p.communicate()
            self.wfile.write(out)
            return

        # handle tile request
        if(len(parsed_path.path.split('/')) == 5 and parsed_path.path.split('/')[1] == 'tiles'):
            patharr = parsed_path.path.split('/')
            devchan = patharr[3]
            level = patharr[4].split('.')[0]
            offset = patharr[4].split('.')[1]
            cmd = ds_root + '/gettile store.kvs 1 ' + devchan + ' ' + level + ' ' + offset
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            (out, err) = p.communicate()
            if(out == '{}'):
                out = '{"data" :[],"fields":["time","mean","stddev","count"],"level":'+level+',"offset":'+offset+'}'
            self.wfile.write(out)
            return

        # otherwise, handle file request
        try:
            f = open(fpath, 'r')
        except IOError:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write('404 Error: File not found')
            return
            
        self.send_response(200)
        if(fext == 'html'):
            self.send_header('Content-Type', 'text/html')
        elif(fext == 'css'):
            self.send_header('Content-Type', 'text/css')
        elif(fext == 'json'):
            self.send_header('Content-Type', 'application/json')
        elif(fext == 'js'):
            self.send_header('Content-Type', 'application/javascript')
        else:
            self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(f.read())
        f.close()
        return

if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('', 4720), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()


