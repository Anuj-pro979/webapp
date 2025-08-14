import streamlit as st
import qrcode
import io
import base64
from PIL import Image
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import tempfile
import os
import requests
import json
import time
from datetime import datetime

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def scan_for_desktop_apps():
    """Scan local network for desktop apps"""
    local_ip = get_local_ip()
    base_ip = ".".join(local_ip.split(".")[:-1]) + "."
    active_apps = []
    
    # Quick scan common ports
    for i in range(1, 255):
        for port in [8000, 8001, 8002, 8003]:
            try:
                test_ip = base_ip + str(i)
                response = requests.get(f"http://{test_ip}:{port}/ping", timeout=0.1)
                if response.status_code == 200:
                    active_apps.append(f"{test_ip}:{port}")
            except:
                pass
    
    return active_apps

def start_file_server(file_path, filename):
    class FileHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/download':
                try:
                    with open(file_path, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(f.read())
                except Exception as e:
                    self.send_error(404, f"File not found: {e}")
            elif self.path == '/info':
                # API endpoint for desktop app integration
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                info = {
                    "filename": filename,
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                }
                self.wfile.write(json.dumps(info).encode())
            else:
                self.send_response(404)
                self.end_headers()
    
    for port in range(8000, 8020):
        try:
            server = HTTPServer(('0.0.0.0', port), FileHandler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            return port, server
        except:
            continue
    return None, None

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

# Initialize session state
if 'server_running' not in st.session_state:
    st.session_state.server_running = False
if 'download_url' not in st.session_state:
    st.session_state.download_url = ""
if 'connected_apps' not in st.session_state:
    st.session_state.connected_apps = []

# Page config
st.set_page_config(page_title="P2P File Share", page_icon="🔗", layout="wide")

st.title("🔗 P2P File Sharing Hub")
st.markdown("*Connected with Desktop App*")
st.markdown("---")

# Sidebar for desktop app connection
st.sidebar.header("🖥️ Desktop Connection")
st.sidebar.markdown("Connect with desktop apps on your network")

if st.sidebar.button("🔍 Scan for Desktop Apps"):
    with st.sidebar:
        with st.spinner("Scanning network..."):
            found_apps = scan_for_desktop_apps()
            st.session_state.connected_apps = found_apps
            
        if found_apps:
            st.success(f"Found {len(found_apps)} desktop app(s)")
            for app in found_apps:
                st.info(f"📱 {app}")
        else:
            st.warning("No desktop apps found")

# Desktop app URL manual entry
manual_url = st.sidebar.text_input("Manual Desktop URL:", placeholder="192.168.1.100:8000")
if st.sidebar.button("🔗 Connect Manual"):
    if manual_url:
        if manual_url not in st.session_state.connected_apps:
            st.session_state.connected_apps.append(manual_url)
        st.sidebar.success("Connected!")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload & Share", "📥 Download from Desktop", "📊 Connection Status"])

with tab1:
    st.header("📁 Upload File & Generate QR")
    
    uploaded_file = st.file_uploader("Choose a file to share", type=None)
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        st.info(f"File size: {uploaded_file.size:,} bytes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Generate QR & Share", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    temp_file_path = tmp_file.name
                
                port, server = start_file_server(temp_file_path, uploaded_file.name)
                
                if port:
                    local_ip = get_local_ip()
                    download_url = f"http://{local_ip}:{port}/download"
                    
                    st.session_state.server_running = True
                    st.session_state.download_url = download_url
                    
                    qr_buffer = generate_qr_code(download_url)
                    
                    st.subheader("📱 QR Code")
                    st.image(qr_buffer, width=250)
                    
                    st.success("✅ File sharing started!")
                else:
                    st.error("❌ Could not start server")
        
        with col2:
            if st.session_state.server_running:
                st.subheader("🔗 Share Link")
                st.code(st.session_state.download_url)
                st.markdown(f"**[📥 Download File]({st.session_state.download_url})**")
                
                # Send to desktop apps
                if st.session_state.connected_apps:
                    st.subheader("📨 Send to Desktop Apps")
                    for app_url in st.session_state.connected_apps:
                        if st.button(f"Send to {app_url}", key=f"send_{app_url}"):
                            try:
                                # Send file info to desktop app
                                response = requests.post(f"http://{app_url}/receive", 
                                                       json={"download_url": st.session_state.download_url,
                                                            "filename": uploaded_file.name})
                                if response.status_code == 200:
                                    st.success(f"✅ Sent to {app_url}")
                                else:
                                    st.error(f"❌ Failed to send to {app_url}")
                            except:
                                st.error(f"❌ Could not reach {app_url}")

with tab2:
    st.header("📥 Download from Connected Desktop Apps")
    
    if st.session_state.connected_apps:
        for app_url in st.session_state.connected_apps:
            with st.expander(f"🖥️ Desktop App: {app_url}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"🔄 Check Files", key=f"check_{app_url}"):
                        try:
                            response = requests.get(f"http://{app_url}/info", timeout=5)
                            if response.status_code == 200:
                                file_info = response.json()
                                st.json(file_info)
                            else:
                                st.error("No files available")
                        except:
                            st.error(f"Could not connect to {app_url}")
                
                with col2:
                    # Generate QR for desktop app downloads
                    desktop_download_url = f"http://{app_url}/download"
                    qr_buffer = generate_qr_code(desktop_download_url)
                    st.image(qr_buffer, width=150)
                    st.caption("QR for desktop files")
    else:
        st.info("🔍 No desktop apps connected. Use sidebar to scan or connect manually.")

with tab3:
    st.header("📊 Connection & Status")
    
    # Network info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 Network Info")
        local_ip = get_local_ip()
        st.info(f"**Your IP:** {local_ip}")
        st.info(f"**Web App URL:** http://{local_ip}:8501")
        
        # Server status
        if st.session_state.server_running:
            st.success("🟢 File server active")
            st.code(st.session_state.download_url)
            
            if st.button("🛑 Stop Sharing"):
                st.session_state.server_running = False
                st.session_state.download_url = ""
                st.rerun()
        else:
            st.info("⚪ No files being shared")
    
    with col2:
        st.subheader("📱 Connected Desktop Apps")
        if st.session_state.connected_apps:
            for i, app in enumerate(st.session_state.connected_apps):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.info(f"🖥️ {app}")
                with col_b:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.connected_apps.remove(app)
                        st.rerun()
        else:
            st.warning("No desktop apps connected")

# Instructions
st.markdown("---")
st.header("📋 How to Use")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌐 Web to Desktop")
    st.markdown("""
    1. **Scan/Connect** to desktop apps
    2. **Upload files** via web interface
    3. **Send to desktop** apps automatically
    4. **Generate QRs** for any connected device
    """)

with col2:
    st.subheader("🖥️ Desktop Integration")
    st.markdown("""
    1. **Run desktop app** (`python main.py`)
    2. **Web app auto-detects** desktop instances
    3. **Bi-directional sharing** between web & desktop
    4. **Unified QR generation** for all files
    """)

st.success("🎉 **Seamless P2P ecosystem** - Desktop ↔ Web ↔ Mobile!")
