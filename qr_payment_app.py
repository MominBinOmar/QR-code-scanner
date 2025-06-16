import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import re
import json
import time
import qrcode

# Set page configuration
st.set_page_config(
    page_title="QR Payment System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #3F51B5;
    text-align: center;
    margin-bottom: 1rem;
    font-weight: bold;
}
.sub-header {
    font-size: 1.5rem;
    color: #303F9F;
    margin-bottom: 1rem;
}
.info-box {
    background-color: #E8EAF6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #3F51B5;
    color: #000000;
}
.success-box {
    background-color: #E8F5E9;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #4CAF50;
    color: #000000;
}
.error-box {
    background-color: #FFEBEE;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #F44336;
    color: #000000;
}
.warning-box {
    background-color: #FFF8E1;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #FFC107;
    color: #000000;
}
.qr-container {
    display: flex;
    justify-content: center;
    margin: 2rem 0;
}
.result-text {
    font-size: 1.2rem;
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #4CAF50;
    color: #000000;
}
.status-text {
    font-size: 1rem;
    color: #FF5722;
}
.success-text {
    font-size: 1.2rem;
    color: #4CAF50;
    font-weight: bold;
}
.centered-image {
    display: flex;
    justify-content: center;
}
.balance-display {
    font-size: 1.5rem;
    font-weight: bold;
    color: #3F51B5;
    text-align: center;
    padding: 1rem;
    background-color: #E8EAF6;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.tab-content {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 0.5rem;
    margin-top: 1rem;
}
.transaction-details {
    background-color: #E3F2FD;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border-left: 5px solid #2196F3;
    color: #000000;
}
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown('<p class="main-header">QR Payment System</p>', unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_cnic' not in st.session_state:
    st.session_state.user_cnic = ""
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0
if 'qr_result' not in st.session_state:
    st.session_state.qr_result = None
if 'scanning' not in st.session_state:
    st.session_state.scanning = False
if 'payment_confirmed' not in st.session_state:
    st.session_state.payment_confirmed = False
if 'payment_amount' not in st.session_state:
    st.session_state.payment_amount = 0.0
if 'payment_recipient' not in st.session_state:
    st.session_state.payment_recipient = ""
if 'payment_cnic' not in st.session_state:
    st.session_state.payment_cnic = ""
if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []
if 'show_my_qr' not in st.session_state:
    st.session_state.show_my_qr = False
if 'scan_state' not in st.session_state:
    st.session_state.scan_state = "idle"  # idle, scanning, detected, confirmed
if 'parsed_payment_data' not in st.session_state:
    st.session_state.parsed_payment_data = None

# Function to validate CNIC format
def validate_cnic(cnic):
    # Pattern for CNIC: 00000-0000000-0 (exactly this format)
    pattern = r'^\d{5}-\d{7}-\d{1}$'
    return bool(re.match(pattern, cnic))

# Function to generate QR code
# Function to generate QR code (simplified version)
def generate_qr_code(data):
    # Convert data to JSON string
    json_data = json.dumps(data)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(json_data)
    qr.make(fit=True)
    
    # Create an image from the QR Code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return img

# Function to detect QR codes
def detect_qr_code(frame):
    # Initialize the QR code detector
    qr_detector = cv2.QRCodeDetector()
    
    # Create a copy of the frame for display
    display_frame = frame.copy()
    qr_value = None
    
    try:
        # For OpenCV 4.5.4 and above, use detectAndDecodeMulti
        ret_qr, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
        
        # If QR codes are detected
        if ret_qr:
            for s, p in zip(decoded_info, points):
                # If the QR code contains data
                if s:
                    qr_value = s  # Assign the QR code value to the variable
                    color = (0, 255, 0)  # Green color for successful decode
                    
                    # Draw a polygon around the QR code
                    display_frame = cv2.polylines(display_frame, [p.astype(int)], True, color, 8)
                    
                    # Display the decoded text on the frame
                    display_frame = cv2.putText(display_frame, "QR Code Detected", p[0].astype(int), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    break
    except Exception as e:
        # For older versions of OpenCV, use detectAndDecode
        try:
            data, bbox, _ = qr_detector.detectAndDecode(frame)
            
            # If a QR code is detected and contains data
            if bbox is not None and data:
                qr_value = data  # Assign the QR code value to the variable
                
                # Draw a polygon around the QR code
                bbox = bbox.astype(int)
                display_frame = cv2.polylines(display_frame, [bbox], True, (0, 255, 0), 8)
                
                # Display the decoded text on the frame
                display_frame = cv2.putText(display_frame, "QR Code Detected", (bbox[0][0], bbox[0][1] - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        except Exception as e:
            # Just continue if there's an error
            pass
    
    return display_frame, qr_value

# Function to process payment
def process_payment(amount, recipient, cnic):
    if st.session_state.balance >= amount:
        # Update user balance
        st.session_state.balance -= amount
        
        # Record the transaction
        transaction = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "payment",
            "amount": amount,
            "recipient": recipient,
            "recipient_cnic": cnic,
            "balance_after": st.session_state.balance
        }
        
        st.session_state.transaction_history.append(transaction)
        
        return True, f"Payment of PKR {amount:.2f} to {recipient} was successful."
    else:
        return False, f"Insufficient funds. Your balance is PKR {st.session_state.balance:.2f}."

# Function to parse QR data
def parse_qr_data(qr_data):
    try:
        payment_data = json.loads(qr_data)
        if 'type' in payment_data and payment_data['type'] == 'payment':
            return payment_data, True, "Valid payment QR code detected."
        else:
            return None, False, "Invalid QR code: Not a payment request."
    except Exception as e:
        return None, False, "Error: Could not parse QR code data."

# Sidebar with user information and options
with st.sidebar:
    if not st.session_state.user_logged_in:
        st.markdown('<p class="sub-header">Create Account / Login</p>', unsafe_allow_html=True)
        
        # Account creation form
        with st.form("account_form"):
            username = st.text_input("Your Name")
            user_cnic = st.text_input("Your CNIC", placeholder="00000-0000000-0", help="Format must be exactly: 00000-0000000-0")
            initial_balance = st.number_input("Initial Balance (PKR)", min_value=0.0, value=5000.0, format="%.2f")
            
            submitted = st.form_submit_button("Create Account & Login")
            
            if submitted:
                if not username:
                    st.error("Please enter your name.")
                elif not validate_cnic(user_cnic):
                    st.error("CNIC must be in the exact format: 00000-0000000-0")
                else:
                    st.session_state.user_logged_in = True
                    st.session_state.username = username
                    st.session_state.user_cnic = user_cnic
                    st.session_state.balance = initial_balance
                    st.success(f"Welcome, {username}!")
                    st.rerun()
    else:
        st.markdown('<p class="sub-header">User Information</p>', unsafe_allow_html=True)
        st.markdown(f"**Name:** {st.session_state.username}")
        st.markdown(f"**CNIC:** {st.session_state.user_cnic}")
        st.markdown(f'<div class="balance-display">Balance: PKR {st.session_state.balance:.2f}</div>', unsafe_allow_html=True)
        
        if st.button("Logout"):
            # Reset all session state variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app allows you to:
    - Generate QR codes for payments
    - Scan QR codes to make payments
    - Track your account balance
    - View transaction history
    """)

# Main content
if not st.session_state.user_logged_in:
    st.markdown('<div class="info-box"><h3>Please create an account to use the app</h3></div>', unsafe_allow_html=True)
else:
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["My QR Code", "Generate Payment QR", "Scan & Pay", "Transaction History"])
    
    # Tab 1: My QR Code
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Your Personal QR Code</p>', unsafe_allow_html=True)
        
        # Create user data dictionary
        user_data = {
            "type": "user_info",
            "name": st.session_state.username,
            "cnic": st.session_state.user_cnic,
            "balance": st.session_state.balance
        }
        
        # Button to show QR code
        if st.button("Show My QR Code"):
            st.session_state.show_my_qr = True
        
        # Display QR code if button was clicked
        if st.session_state.show_my_qr:
            # Generate QR code
            qr_img = generate_qr_code(user_data)
            
            # Convert PIL image to bytes for Streamlit
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            # Display QR code
            st.markdown('<div class="qr-container"></div>', unsafe_allow_html=True)
            st.image(byte_im, caption=f"QR Code for {st.session_state.username}", use_container_width=True)
            
            # Display QR code information
            st.markdown(f'''
            <div class="success-box">
                <h3>Your QR Code Information</h3>
                <ul>
                    <li><strong>Name:</strong> {st.session_state.username}</li>
                    <li><strong>CNIC:</strong> {st.session_state.user_cnic}</li>
                    <li><strong>Balance:</strong> PKR {st.session_state.balance:.2f}</li>
                </ul>
                <p>You can download the QR code by right-clicking on the image and selecting "Save Image As..."</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div class="info-box">
                <h3>Instructions</h3>
                <p>Click the "Show My QR Code" button to generate a QR code containing your account information.</p>
                <p>This QR code can be scanned by others to view your account details.</p>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Generate Payment QR
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Create Payment QR Code</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Payment information form
            with st.form("payment_info_form"):
                # Automatically use the logged-in user's information
                st.markdown(f"**Sender:** {st.session_state.username} (You)")
                amount = st.number_input("Amount (PKR)", min_value=1.0, format="%.2f")
                
                submitted = st.form_submit_button("Generate Payment QR Code")
        
        with col2:
            st.markdown('<p class="sub-header">Generated QR Code</p>', unsafe_allow_html=True)
            qr_placeholder = st.empty()
        
        # Process form submission
        if submitted:
            # Create data dictionary with the logged-in user's information
            payment_data = {
                "type": "payment",
                "sender": st.session_state.username,
                "sender_cnic": st.session_state.user_cnic,
                "amount": amount
            }
            
            # Generate QR code
            qr_img = generate_qr_code(payment_data)
            
            # Convert PIL image to bytes for Streamlit
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            # Display QR code
            qr_placeholder.markdown('<div class="qr-container"></div>', unsafe_allow_html=True)
            qr_placeholder.image(byte_im, caption=f"Payment QR Code for PKR {amount:.2f}", use_container_width=True)
            
            # Display success message with data preview
            st.markdown(f'''
            <div class="success-box">
                <h3>Payment QR Code Generated Successfully!</h3>
                <p>The QR code contains the following payment information:</p>
                <ul>
                    <li><strong>Sender:</strong> {st.session_state.username}</li>
                    <li><strong>CNIC:</strong> {st.session_state.user_cnic}</li>
                    <li><strong>Amount:</strong> PKR {amount:.2f}</li>
                </ul>
                <p>You can download the QR code by right-clicking on the image and selecting "Save Image As..."</p>
            </div>
            ''', unsafe_allow_html=True)
        
        # Display instructions if no QR code has been generated yet
        if not submitted:
            qr_placeholder.markdown('''
            <div class="info-box">
                <h3>Instructions</h3>
                <p>Enter the amount and click "Generate Payment QR Code" to create a QR code for payment.</p>
                <p>The generated QR code can be scanned by another user to make a payment to you.</p>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 3: Scan & Pay
    with tab3:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Scan QR Code to Make Payment</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Camera section
            st.markdown("### Camera Feed")
            camera_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Control buttons
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                if st.button("📷 Start Scanning", type="primary", disabled=(st.session_state.scan_state == "scanning")):
                    st.session_state.scan_state = "scanning"
                    st.session_state.qr_result = None
                    st.session_state.parsed_payment_data = None
                    st.rerun()
            
            with button_col2:
                if st.button("⏹️ Stop Scanning", disabled=(st.session_state.scan_state != "scanning")):
                    st.session_state.scan_state = "idle"
                    st.rerun()
        
        with col2:
            # Payment details section
            st.markdown("### Payment Details")
            
            # Show different content based on scan state
            if st.session_state.scan_state == "idle":
                st.markdown('''
                <div class="info-box">
                    <h4>Ready to Scan</h4>
                    <p>Click "Start Scanning" to activate the camera and scan a payment QR code.</p>
                </div>
                ''', unsafe_allow_html=True)
            
            elif st.session_state.scan_state == "scanning":
                st.markdown('''
                <div class="warning-box">
                    <h4>Scanning Active</h4>
                    <p>Point your camera at a payment QR code to detect it.</p>
                </div>
                ''', unsafe_allow_html=True)
            
            elif st.session_state.scan_state == "detected" and st.session_state.parsed_payment_data:
                payment_data = st.session_state.parsed_payment_data
                
                st.markdown(f'''
                <div class="result-text">
                    <h4>Payment Request Detected</h4>
                    <p><strong>Recipient:</strong> {payment_data['sender']}</p>
                    <p><strong>CNIC:</strong> {payment_data['sender_cnic']}</p>
                    <p><strong>Amount:</strong> PKR {payment_data['amount']:.2f}</p>
                    <p><strong>Your Balance:</strong> PKR {st.session_state.balance:.2f}</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Payment confirmation buttons
                if st.session_state.balance >= payment_data['amount']:
                    if st.button("✅ Confirm Payment", type="primary", key="confirm_payment"):
                        success, message = process_payment(
                            payment_data['amount'],
                            payment_data['sender'],
                            payment_data['sender_cnic']
                        )
                        if success:
                            st.session_state.scan_state = "confirmed"
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.markdown(f'''
                    <div class="error-box">
                        <h4>Insufficient Funds</h4>
                        <p>You need PKR {payment_data['amount']:.2f} but only have PKR {st.session_state.balance:.2f}</p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                if st.button("❌ Cancel", key="cancel_payment"):
                    st.session_state.scan_state = "idle"
                    st.session_state.qr_result = None
                    st.session_state.parsed_payment_data = None
                    st.rerun()
            
            elif st.session_state.scan_state == "confirmed":
                # Show payment success
                if st.session_state.transaction_history:
                    last_transaction = st.session_state.transaction_history[-1]
                    
                    st.markdown(f'''
                    <div class="success-box">
                        <h4>✅ Payment Successful!</h4>
                        <p><strong>Amount Paid:</strong> PKR {last_transaction['amount']:.2f}</p>
                        <p><strong>Recipient:</strong> {last_transaction['recipient']}</p>
                        <p><strong>New Balance:</strong> PKR {last_transaction['balance_after']:.2f}</p>
                        <p><strong>Transaction Time:</strong> {last_transaction['date']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                if st.button("🔄 Scan Another QR Code", key="scan_another"):
                    st.session_state.scan_state = "idle"
                    st.session_state.qr_result = None
                    st.session_state.parsed_payment_data = None
                    st.rerun()
        
        # Camera scanning logic
        if st.session_state.scan_state == "scanning":
            status_placeholder.markdown('<p class="status-text">📷 Camera active - Looking for QR codes...</p>', unsafe_allow_html=True)
            
            # Use a more efficient approach with manual frame capture
            # This is a simplified version - in a real app, you'd use st.camera_input or similar
            camera_placeholder.markdown('''
            <div class="info-box">
                <h4>Camera Simulation</h4>
                <p>In a real deployment, this would show the live camera feed.</p>
                <p>Upload a QR code image below to simulate scanning:</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # File uploader for QR code simulation
            uploaded_file = st.file_uploader("Upload QR Code Image", type=['jpg', 'jpeg', 'png'], key="qr_upload")
            
            if uploaded_file is not None:
                # Process uploaded image
                image = Image.open(uploaded_file)
                img_array = np.array(image)
                
                # Convert to OpenCV format if needed
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Try to detect QR code
                display_frame, qr_value = detect_qr_code(img_array)
                
                if qr_value:
                    # Parse the QR data
                    parsed_data, is_valid, message = parse_qr_data(qr_value)
                    
                    if is_valid:
                        st.session_state.qr_result = qr_value
                        st.session_state.parsed_payment_data = parsed_data
                        st.session_state.scan_state = "detected"
                        st.rerun()
                    else:
                        st.error(message)
                        st.session_state.scan_state = "idle"
                        st.rerun()
                else:
                    st.error("No QR code detected in the image. Please try again.")
        
        elif st.session_state.scan_state == "idle":
            status_placeholder.markdown('<p class="status-text">📷 Camera inactive</p>', unsafe_allow_html=True)
            camera_placeholder.markdown('''
            <div class="centered-image">
                <p style="text-align: center; color: #666; padding: 50px;">
                    📷<br>
                    Camera Ready<br>
                    Click "Start Scanning" to begin
                </p>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 4: Transaction History
    with tab4:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Transaction History</p>', unsafe_allow_html=True)
        
        if st.session_state.transaction_history:
            st.markdown(f'<div class="balance-display">Current Balance: PKR {st.session_state.balance:.2f}</div>', unsafe_allow_html=True)
            
            # Display transactions
            for i, transaction in enumerate(reversed(st.session_state.transaction_history)):
                st.markdown(f'''
                <div class="transaction-details">
                    <h4>Transaction #{len(st.session_state.transaction_history) - i}</h4>
                    <p><strong>Date:</strong> {transaction['date']}</p>
                    <p><strong>Type:</strong> {transaction['type'].title()}</p>
                    <p><strong>Amount:</strong> PKR {transaction['amount']:.2f}</p>
                    <p><strong>Recipient:</strong> {transaction['recipient']}</p>
                    <p><strong>Recipient CNIC:</strong> {transaction['recipient_cnic']}</p>
                    <p><strong>Balance After:</strong> PKR {transaction['balance_after']:.2f}</p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div class="info-box">
                <h3>No Transactions Yet</h3>
                <p>Your transaction history will appear here after you make your first payment.</p>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>© 2025 QR Payment System | Built with Streamlit</p>", 
    unsafe_allow_html=True
)
