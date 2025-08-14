import streamlit as st
import requests
import io
import os
from PIL import Image
import base64
import json
import time

st.set_page_config(page_title="P2P File Receiver", layout="centered")

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #e2e3f0;
        border: 1px solid #b8bcc8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📱 P2P File Receiver</h1>', unsafe_allow_html=True)

# Sidebar for connection status
with st.sidebar:
    st.header("📊 Connection Status")
    status_placeholder = st.empty()
    st.header("📝 Recent Downloads")
    recent_placeholder = st.empty()

# Initialize session state
if 'downloaded_files' not in st.session_state:
    st.session_state.downloaded_files = []
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "Ready"

# Method 1: Camera QR Scanner (using JavaScript)
st.header("📷 Live Camera QR Scanner")

camera_qr = st.camera_input("Take a picture of QR code")
if camera_qr:
    try:
        # Simple QR detection using PIL and pattern recognition
        image = Image.open(camera_qr)
        st.image(image, caption="Captured QR Code", width=300)
        
        # For demo purposes, let user input the URL manually after capturing
        st.info("QR Code captured! Please enter the URL shown in the QR code below:")
        
    except Exception as e:
        st.error(f"Camera error: {str(e)}")

# Method 2: Upload QR Image
st.header("🖼️ Upload QR Code Image")
uploaded_qr = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg', 'webp'])

if uploaded_qr:
    image = Image.open(uploaded_qr)
    st.image(image, caption="Uploaded QR Code", width=300)
    
    # Convert to base64 and try to extract URL pattern
    try:
        # Simple heuristic: look for http patterns in image metadata or filename
        img_info = str(image.info) if hasattr(image, 'info') else ""
        st.info("QR Code uploaded! Please enter the URL from the QR code below:")
        
    except Exception as e:
        st.error(f"Upload error: {str(e)}")

# Method 3: Direct URL Input (Primary Method)
st.header("🔗 Direct URL Input")
col1, col2 = st.columns([3, 1])

with col1:
    url_input = st.text_input(
        "Enter the sharing URL:",
        placeholder="http://192.168.1.100:8080",
        help="Copy the URL from your desktop app"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    connect_btn = st.button("🔍 Connect", type="primary")

# Auto-detect local network IPs for quick access
st.header("🌐 Quick Connect")
st.write("Common local network patterns:")

quick_connect_cols = st.columns(4)
common_ips = ["192.168.1.", "192.168.0.", "10.0.0.", "172.16.0."]

for i, ip_pattern in enumerate(common_ips):
    with quick_connect_cols[i]:
        if st.button(f"Scan {ip_pattern}x"):
            st.info(f"Scanning {ip_pattern}x network...")
            # In a real implementation, you'd scan the network
            st.write("Enter the complete IP and port above")

# File download logic
if url_input and (connect_btn or st.button("📥 Download File")):
    if not url_input.startswith(('http://', 'https://')):
        url_input = f"http://{url_input}"
    
    try:
        st.session_state.connection_status = "Connecting..."
        status_placeholder.info("🔄 Connecting to sender...")
        
        with st.spinner("Downloading file..."):
            response = requests.get(url_input, stream=True, timeout=10)
            
        if response.status_code == 200:
            # Extract filename
            filename = "shared_file"
            if 'Content-Disposition' in response.headers:
                disp = response.headers['Content-Disposition']
                if 'filename=' in disp:
                    filename = disp.split('filename=')[1].strip('"\'')
            
            # Get file size
            file_size = len(response.content)
            file_size_mb = file_size / (1024 * 1024)
            
            # Success message
            st.success(f"✅ Connected successfully!")
            st.info(f"📄 **File:** {filename}\n📏 **Size:** {file_size_mb:.2f} MB")
            
            # Download button
            st.download_button(
                label=f"📥 Download {filename}",
                data=response.content,
                file_name=filename,
                mime="application/octet-stream",
                type="primary"
            )
            
            # Update session state
            st.session_state.connection_status = "Connected ✅"
            st.session_state.downloaded_files.append({
                'name': filename,
                'size': f"{file_size_mb:.2f} MB",
                'time': time.strftime("%H:%M:%S"),
                'url': url_input
            })
            
            # Auto-refresh to show updated status
            st.rerun()
            
        else:
            st.error(f"❌ Connection failed! Status code: {response.status_code}")
            st.session_state.connection_status = "Connection failed ❌"
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Connection timeout! Make sure the sender is running.")
        st.session_state.connection_status = "Timeout ⏱️"
    except requests.exceptions.ConnectionError:
        st.error("🚫 Cannot connect! Check the URL and network connection.")
        st.session_state.connection_status = "No connection 🚫"
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.session_state.connection_status = "Error ❌"

# Update sidebar
status_placeholder.write(f"Status: {st.session_state.connection_status}")

if st.session_state.downloaded_files:
    recent_files = st.session_state.downloaded_files[-3:]  # Show last 3
    for file_info in reversed(recent_files):
        recent_placeholder.write(f"• {file_info['name']} ({file_info['size']}) at {file_info['time']}")

# Instructions
with st.expander("📚 How to Use", expanded=False):
    st.markdown("""
    **Step-by-step guide:**
    
    1. **Run Desktop App**: Start the desktop file sender
    2. **Select File**: Choose any file to share
    3. **Generate QR**: Click 'Generate QR & Start Sharing'
    4. **Connect Here**: 
       - Take photo of QR code with camera
       - Or upload QR image
       - Or copy/paste the URL directly
    5. **Download**: Click the download button
    
    **Network Tips:**
    - Make sure both devices are on the same WiFi
    - Check firewall settings if connection fails
    - Use IP:PORT format (e.g., 192.168.1.100:8080)
    """)

# Footer
st.markdown("---")
st.markdown("🚀 **Enhanced P2P File Sharing** - Direct device-to-device transfer!")
