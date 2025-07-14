import subprocess
import os
import re

# === Configuration ===
conf_dir = "/etc/nginx/conf.d"
nginx_dirs = ["/etc/nginx", conf_dir]
ssl_base = "/etc/letsencrypt/live"

# Domain to config file and SSL cert mapping
domains = {
    "skinpulse.online": {
        "conf_file": "odoo.conf",
        "ssl_path": os.path.join(ssl_base, "skinpulse.online")
    },
    "idywarrie.com": {
        "conf_file": "idywarrie.conf",
        "ssl_path": os.path.join(ssl_base, "idywarrie.com")
    }
}

# === Step 1: Ensure base directories exist ===
def ensure_directories():
    for d in nginx_dirs:
        if not os.path.exists(d):
            print(f"📁 Creating missing directory: {d}")
            os.makedirs(d, exist_ok=True)

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
    print("🔍 Extracting server blocks...")
    server_blocks = {domain: "" for domain in domains}

    strings_output = subprocess.check_output(["strings", dump_file], text=True)
    full_text = "\n".join(strings_output.splitlines())

    for domain in domains:
        pattern = re.compile(rf"(server\s*\{{[^{{}}]*?{re.escape(domain)}.*?\}})", re.DOTALL)
        match = pattern.search(full_text)
        if match:
            block = match.group(1)
            # Add SSL config if path exists
            ssl_dir = domains[domain]["ssl_path"]
            if os.path.exists(ssl_dir):
                ssl_block = f"""
    ssl_certificate     {ssl_dir}/fullchain.pem;
    ssl_certificate_key {ssl_dir}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
"""
                block = re.sub(r"server\s*{", "server {\n    listen 443 ssl;", block, 1)
                block += ssl_block
            else:
                print(f"⚠️ SSL path not found for {domain}: {ssl_dir}")
            server_blocks[domain] = block
        else:
            print(f"⚠️ No server block found for {domain}")
    return server_blocks

# === Step 5: Save to conf.d ===
def save_configs(blocks):
    for domain, data in domains.items():
        conf_path = os.path.join(conf_dir, data["conf_file"])
        with open(conf_path, "w") as f:
            f.write(blocks[domain] or f"# Placeholder for {domain}")
        print(f"✅ Wrote config: {conf_path}")

# === Step 6: Test NGINX Config ===
def test_nginx_config():
    print("🧪 Testing NGINX configuration...")
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ NGINX config is valid.")
    else:
        print("❌ NGINX config test failed:\n")
        print(result.stderr)

# === Main Flow ===
def main():
    try:
        print("🚧 NGINX Recovery Script Starting...")
        ensure_directories()

        pid = get_nginx_master_pid()
        dump_file = dump_memory(pid)

        blocks = extract_server_blocks(dump_file, domains)
        save_configs(blocks)

        test_nginx_config()

        print("\n📝 Done. You can now manually run:\n  sudo systemctl reload nginx")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
    
