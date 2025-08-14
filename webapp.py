import streamlit as st
import requests
import io
import os
from PIL import Image
try:
    from pyzbar import pyzbar
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

st.set_page_config(page_title="P2P File Receiver", layout="centered")

st.title("📱 P2P File Receiver")
st.markdown("Scan QR code or enter URL to download shared files")

# Option 1: QR Code Scanner
st.header("🔍 QR Code Scanner")

if not QR_AVAILABLE:
    st.warning("QR scanning requires 'pyzbar' library. For now, use direct URL input below.")
    st.info("To enable QR scanning: `pip install pyzbar`")
else:
    uploaded_qr = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg'])

    if uploaded_qr:
        image = Image.open(uploaded_qr)
        
        # Decode QR code
        try:
            decoded_objects = pyzbar.decode(image)
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                st.success(f"QR Code detected: {qr_data}")
                
                if st.button("Download from QR URL"):
                    try:
                        response = requests.get(qr_data, stream=True)
                        if response.status_code == 200:
                            # Extract filename from header
                            filename = "downloaded_file"
                            if 'Content-Disposition' in response.headers:
                                disp = response.headers['Content-Disposition']
                                if 'filename=' in disp:
                                    filename = disp.split('filename=')[1].strip('"')
                            
                            # Create download button
                            st.download_button(
                                label=f"📥 Download {filename}",
                                data=response.content,
                                file_name=filename,
                                mime="application/octet-stream"
                            )
                            st.success("File ready for download!")
                        else:
                            st.error("Failed to connect to sender")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.error("No QR code found in image")
        except Exception as e:
            st.error(f"QR scanning error: {str(e)}")

# Option 2: Direct URL Input
st.header("🔗 Direct URL")
url_input = st.text_input("Enter the sharing URL:")

if url_input and st.button("Download from URL"):
    try:
        response = requests.get(url_input, stream=True)
        if response.status_code == 200:
            filename = "downloaded_file"
            if 'Content-Disposition' in response.headers:
                disp = response.headers['Content-Disposition']
                if 'filename=' in disp:
                    filename = disp.split('filename=')[1].strip('"')
            
            st.download_button(
                label=f"📥 Download {filename}",
                data=response.content,
                file_name=filename,
                mime="application/octet-stream"
            )
            st.success("File ready for download!")
        else:
            st.error("Failed to connect to sender")
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown("💡 **How to use:**")
st.markdown("1. Run the desktop app and select a file")
st.markdown("2. Click 'Generate QR & Start Sharing'") 
st.markdown("3. Upload the QR code here or copy the URL")
st.markdown("4. Download the shared file!")
