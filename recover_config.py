import subprocess
import os
import re

# === Configuration ===
nginx_base = "/etc/nginx"
conf_dir = f"{nginx_base}/conf.d"
log_dir = "/var/log/nginx"
ssl_base = "/etc/letsencrypt/live"

# Domain to config mapping
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

# === Step 1: Ensure NGINX directories and base config ===
def setup_nginx_structure():
    print("📁 Checking NGINX structure...")
    os.makedirs(conf_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    nginx_conf_path = f"{nginx_base}/nginx.conf"
    if not os.path.exists(nginx_conf_path):
        print("⚠️ nginx.conf not found. Recreating...")
        minimal_conf = """\
user nginx;
worker_processes auto;
error_log  /var/log/nginx/error.log;
pid        /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    keepalive_timeout  65;

    include /etc/nginx/conf.d/*.conf;
}
"""
        with open(nginx_conf_path, "w") as f:
            f.write(minimal_conf)
        print(f"✅ Recreated nginx.conf at {nginx_conf_path}")
    else:
        print("✅ nginx.conf exists")

# === Step 2: Get NGINX master process PID ===
def get_nginx_master_pid():
    ps_output = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
    for line in ps_output.splitlines():
        if "nginx: master process" in line:
            return int(line.strip().split()[0])
    raise RuntimeError("❌ NGINX master process not found")

# === Step 3: Dump memory with gcore ===
def dump_memory(pid):
    dump_file = f"nginx_dump.{pid}"
    print(f"💾 Dumping NGINX memory to {dump_file}")
    subprocess.run(["gcore", "-o", "nginx_dump", str(pid)], check=True)
    return dump_file

# === Step 4: Extract server blocks for domains ===
def extract_server_blocks(dump_file):
    print("🔍 Scanning memory dump for server blocks...")
    server_blocks = {}
    strings_output = subprocess.check_output(["strings", dump_file], text=True)
    full_text = "\n".join(strings_output.splitlines())

    for domain, info in domains.items():
        block = ""
        pattern = re.compile(rf"(server\s*\{{[^{{}}]*?{re.escape(domain)}.*?\}})", re.DOTALL)
        match = pattern.search(full_text)
        if match:
            block = match.group(1)
            if "listen" not in block:
                block = "    listen 443 ssl;\n" + block
            else:
                block = re.sub(r"listen\s+\d+;", "listen 443 ssl;", block, count=1)

            ssl_path = info["ssl_path"]
            if os.path.exists(ssl_path):
                ssl_block = f"""
    ssl_certificate     {ssl_path}/fullchain.pem;
    ssl_certificate_key {ssl_path}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
"""
                block += ssl_block
            else:
                print(f"⚠️ SSL path not found for {domain}: {ssl_path}")
        else:
            # Fallback basic config
            print(f"⚠️ Server block for {domain} not found in memory. Using fallback.")
            ssl_path = info["ssl_path"]
            block = f"""
server {{
    listen 443 ssl;
    server_name {domain} www.{domain};
    root /usr/share/nginx/html;

    ssl_certificate     {ssl_path}/fullchain.pem;
    ssl_certificate_key {ssl_path}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}}
"""
        server_blocks[domain] = block
    return server_blocks

# === Step 5: Save recovered config files ===
def save_config_files(blocks):
    for domain, config in blocks.items():
        conf_file = domains[domain]["conf_file"]
        path = os.path.join(conf_dir, conf_file)
        with open(path, "w") as f:
            f.write(config.strip() + "\n")
        print(f"✅ Saved config: {path}")

# === Step 6: Test nginx configuration ===
def test_nginx_config():
    print("🧪 Testing NGINX configuration...")
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ NGINX configuration is valid.")
    else:
        print("❌ NGINX config test failed:\n")
        print(result.stderr)

# === Main Execution ===
def main():
    try:
        print("🚀 Starting NGINX recovery script...\n")
        setup_nginx_structure()
        pid = get_nginx_master_pid()
        dump_file = dump_memory(pid)
        blocks = extract_server_blocks(dump_file)
        save_config_files(blocks)
        test_nginx_config()
        print("\n🎉 Recovery complete.")
        print("⚠️ NGINX has NOT been restarted. If test passed, run:")
        print("   sudo systemctl reload nginx")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
                
