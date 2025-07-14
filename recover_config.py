import subprocess
import os
import re

# --- Config ---
conf_dir = "/etc/nginx/conf.d"
domains = {
    "idywarrie.com": "idywarrie.conf",
    "skinpulse.online": "odoo.conf"
}

# --- Step 1: Find nginx master process ---
def get_nginx_master_pid():
    ps_output = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
    for line in ps_output.splitlines():
        if "nginx: master process" in line:
            return int(line.strip().split()[0])
    raise RuntimeError("NGINX master process not found")

# --- Step 2: Dump memory using gcore ---
def dump_memory(pid):
    dump_file = f"nginx_dump.{pid}"
    subprocess.run(["gcore", "-o", "nginx_dump", str(pid)], check=True)
    return dump_file

# --- Step 3: Extract server blocks for each domain ---
def extract_server_blocks(dump_file, domains):
    server_blocks = {domain: "" for domain in domains}

    strings_output = subprocess.check_output(["strings", dump_file], text=True)

    lines = strings_output.splitlines()
    combined = "\n".join(lines)

    # Naively find server blocks containing each domain
    for domain in domains:
        pattern = re.compile(rf"(server\s*\{{[^{{}}]*?{re.escape(domain)}.*?\}})", re.DOTALL)
        match = pattern.search(combined)
        if match:
            server_blocks[domain] = match.group(1)
        else:
            print(f"Warning: Server block for {domain} not found.")
    return server_blocks

# --- Step 4: Save to /etc/nginx/conf.d ---
def save_config_files(blocks, conf_dir):
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    for domain, content in blocks.items():
        filename = domains[domain]
        filepath = os.path.join(conf_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✅ Recovered {domain} to {filepath}")

# --- MAIN ---
def main():
    try:
        print("🔍 Finding NGINX master process...")
        pid = get_nginx_master_pid()
        print(f"📌 NGINX master PID: {pid}")

        print("💾 Dumping memory using gcore...")
        dump_file = dump_memory(pid)

        print("🧠 Extracting server blocks from memory dump...")
        blocks = extract_server_blocks(dump_file, domains)

        print("📝 Saving recovered config files...")
        save_config_files(blocks, conf_dir)

        print("\n✅ Recovery complete. Run: sudo nginx -t && sudo systemctl reload nginx")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
