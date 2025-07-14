import subprocess
import os
import re

# === Configuration ===
nginx_base = "/etc/nginx"
conf_dir = f"{nginx_base}/conf.d"
log_dir = "/var/log/nginx"
ssl_base = "/etc/letsencrypt/live"

# Domain to conf mapping
domains = {
    "skinpulse.online": {
        "conf_file": "odoo.conf",
        "ssl_path": f"{ssl_base}/skinpulse.online"
    },
    "idywarrie.com": {
        "conf_file": "idywarrie.conf",
        "ssl_path": f"{ssl_base}/idywarrie.com"
    }
}

# === Step 1: Ensure basic nginx directory structure and config ===
def setup_nginx_directories_and_config():
    print("📁 Checking nginx directory structure...")
    os.makedirs(conf_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    nginx_conf_path = f"{nginx_base}/nginx.conf"
    if not os.path.exists(nginx_conf_path):
        print("⚠️ nginx.conf missing. Recreating minimal config...")
        minimal_conf = f"""
user nginx;
worker_processes auto;
error_log  {log_dir}/error.log;
pid        /run/nginx.pid;

events {{
    worker_connections 1024;
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  {log_dir}/access.log  main;

    sendfile        on;
    keepalive_timeout  65;

    include {conf_dir}/*.conf;
}}
"""
        with open(nginx_conf_path, "w") as f:
            f.write(minimal_conf.strip())
        print(f"✅ Recreated nginx.conf at {nginx_conf_path}")
    else:
        print("✅ nginx.conf exists.")

# === Step 2: Get NGINX master PID ===
def get_nginx_master_pid():
    ps_output = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
    for line in ps_output.splitlines():
        if "nginx: master process" in line:
            return int(line.strip().split()[0])
    raise RuntimeError("❌ NGINX master process not found")

# === Step 3: Dump memory ===
def dump_memory(pid):
    dump_file = f"nginx_dump.{pid}"
    print(f"💾 Dumping NGINX memory to {dump_file}")
    subprocess.run(["gcore", "-o", "nginx_dump", str(pid)], check=True)
    return dump_file

# === Step 4: Extract server blocks for domains ===
def extract_server_blocks(dump_file, domains):
    print("🔍 Extracting server blocks from memory...")
    server_blocks = {}

    strings_output = subprocess.check_output(["strings", dump_file], text=True)
    full_text = "\n".join(strings_output.splitlines())

    for domain, info in domains.items():
        block = ""
        pattern = re.compile(rf"(server\s*\{{[^{{}}]*?{re.escape(domain)}.*?\}})", re.DOTALL)
        match = pattern.search(full_text)
        if match:
            block = match.group(1)
            block = re.sub(r"(listen\s+\d+;)?", "listen 443 ssl;", block, count=1)

            ssl_path = info["ssl_path"]
            if os.path.exists(ssl_path):
                block += f"""
    ssl_certificate     {ssl_path}/fullchain.pem;
    ssl_certificate_key {ssl_path}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
