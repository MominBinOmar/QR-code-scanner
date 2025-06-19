import cv2
import numpy as np
from PIL import Image, ImageTk
import io
import re
import json
import time
import qrcode
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread

class QRPaymentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Payment System")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set app icon if available
        try:
            self.root.iconbitmap("app_icon.ico")
        except:
            pass
        
        # Initialize user data
        self.user_logged_in = False
        self.username = ""
        self.user_cnic = ""
        self.balance = 0.0
        self.qr_result = None
        self.scanning = False
        self.payment_confirmed = False
        self.payment_amount = 0.0
        self.payment_recipient = ""
        self.payment_cnic = ""
        self.transaction_history = []
        self.show_my_qr = False
        self.scan_state = "idle"  # idle, scanning, detected, confirmed
        self.parsed_payment_data = None
        self.live_scanning_active = False
        self.camera_started = False
        
        # Camera variables
        self.cap = None
        self.camera_thread = None
        self.camera_active = False
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create sidebar frame and main content frame
        self.sidebar_frame = ttk.Frame(self.main_frame, width=250)
        self.content_frame = ttk.Frame(self.main_frame)
        
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create header
        self.header_label = ttk.Label(self.content_frame, text="QR Payment System", font=("Arial", 24, "bold"))
        self.header_label.pack(pady=(0, 20))
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab1 = ttk.Frame(self.notebook)  # My QR Code
        self.tab2 = ttk.Frame(self.notebook)  # Generate Payment QR
        self.tab3 = ttk.Frame(self.notebook)  # Scan & Pay
        self.tab4 = ttk.Frame(self.notebook)  # Transaction History
        
        self.notebook.add(self.tab1, text="My QR Code")
        self.notebook.add(self.tab2, text="Generate Payment QR")
        self.notebook.add(self.tab3, text="Scan & Pay")
        self.notebook.add(self.tab4, text="Transaction History")
        
        # Setup sidebar
        self.setup_sidebar()
        
        # Setup tab content
        self.setup_my_qr_tab()
        self.setup_generate_qr_tab()
        self.setup_scan_pay_tab()
        self.setup_transaction_history_tab()
        
        # Create footer
        self.footer_label = ttk.Label(self.root, text="© 2025 QR Payment System")
        self.footer_label.pack(side=tk.BOTTOM, pady=10)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_sidebar(self):
        # Clear all existing widgets in the sidebar frame
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()
            
        # Create a frame for login/account info
        self.sidebar_top_frame = ttk.Frame(self.sidebar_frame)
        self.sidebar_top_frame.pack(fill=tk.X, pady=10)
        
        if not self.user_logged_in:
            # Login form
            ttk.Label(self.sidebar_top_frame, text="Create Account / Login", font=("Arial", 12, "bold")).pack(pady=5)
            
            ttk.Label(self.sidebar_top_frame, text="Your Name:").pack(anchor="w", pady=(10, 0))
            self.username_entry = ttk.Entry(self.sidebar_top_frame, width=30)
            self.username_entry.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(self.sidebar_top_frame, text="Your CNIC (00000-0000000-0):").pack(anchor="w", pady=(0, 0))
            self.cnic_entry = ttk.Entry(self.sidebar_top_frame, width=30)
            self.cnic_entry.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(self.sidebar_top_frame, text="Initial Balance (PKR):").pack(anchor="w", pady=(0, 0))
            self.balance_entry = ttk.Entry(self.sidebar_top_frame, width=30)
            self.balance_entry.insert(0, "5000.00")
            self.balance_entry.pack(fill=tk.X, pady=(0, 10))
            
            self.login_button = ttk.Button(self.sidebar_top_frame, text="Create Account & Login", command=self.login)
            self.login_button.pack(fill=tk.X, pady=10)
            
            self.login_error_label = ttk.Label(self.sidebar_top_frame, text="", foreground="red")
            self.login_error_label.pack(fill=tk.X, pady=(0, 10))
        else:
            # User info display
            ttk.Label(self.sidebar_top_frame, text="User Information", font=("Arial", 12, "bold")).pack(pady=5)
            
            ttk.Label(self.sidebar_top_frame, text=f"Name: {self.username}").pack(anchor="w", pady=2)
            ttk.Label(self.sidebar_top_frame, text=f"CNIC: {self.user_cnic}").pack(anchor="w", pady=2)
            
            # Balance display with custom style
            balance_frame = ttk.Frame(self.sidebar_top_frame, relief=tk.GROOVE, borderwidth=2)
            balance_frame.pack(fill=tk.X, pady=10)
            ttk.Label(balance_frame, text=f"Balance: PKR {self.balance:.2f}", 
                      font=("Arial", 12, "bold")).pack(pady=10)
            
            self.logout_button = ttk.Button(self.sidebar_top_frame, text="Logout", command=self.logout)
            self.logout_button.pack(fill=tk.X, pady=10)
        
        # About section
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=10)
        ttk.Label(self.sidebar_frame, text="About", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        about_text = """This app allows you to:
- Generate QR codes for payments
- Scan QR codes to make payments
- Track your account balance
- View transaction history"""
        
        ttk.Label(self.sidebar_frame, text=about_text, wraplength=230, justify="left").pack(anchor="w", pady=5)
    
    def setup_my_qr_tab(self):
        # Create a frame for the tab content
        content_frame = ttk.Frame(self.tab1, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Your Personal QR Code", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Button to show QR code
        self.show_qr_button = ttk.Button(content_frame, text="Show My QR Code", command=self.show_my_qr_code)
        self.show_qr_button.pack(pady=10)
        
        # Frame for QR code display
        self.qr_display_frame = ttk.Frame(content_frame)
        self.qr_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Initially show instructions
        self.qr_instructions_label = ttk.Label(self.qr_display_frame, 
                                            text="Click the 'Show My QR Code' button to generate a QR code containing your account information."
                                            "\nThis QR code can be scanned by others to view your account details.",
                                            wraplength=500, justify="center")
        self.qr_instructions_label.pack(pady=50)
    
    def setup_generate_qr_tab(self):
        # Create a frame for the tab content
        content_frame = ttk.Frame(self.tab2, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Create Payment QR Code", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Create two columns
        left_frame = ttk.Frame(content_frame)
        right_frame = ttk.Frame(content_frame)
        
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Left frame - Payment form
        form_frame = ttk.LabelFrame(left_frame, text="Payment Information")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(form_frame, text=f"Sender: {self.username} (You)").pack(anchor="w", pady=(10, 5))
        
        ttk.Label(form_frame, text="Amount (PKR):").pack(anchor="w", pady=(10, 0))
        self.payment_amount_entry = ttk.Entry(form_frame)
        self.payment_amount_entry.insert(0, "100.00")
        self.payment_amount_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.generate_payment_qr_button = ttk.Button(form_frame, text="Generate Payment QR Code", 
                                                  command=self.generate_payment_qr)
        self.generate_payment_qr_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Right frame - QR display
        qr_frame = ttk.LabelFrame(right_frame, text="Generated QR Code")
        qr_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.payment_qr_display_frame = ttk.Frame(qr_frame)
        self.payment_qr_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially show instructions
        self.payment_qr_instructions = ttk.Label(self.payment_qr_display_frame, 
                                              text="Enter the amount and click 'Generate Payment QR Code' to create a QR code for payment."
                                              "\nThe generated QR code can be scanned by another user to make a payment to you.",
                                              wraplength=300, justify="center")
        self.payment_qr_instructions.pack(pady=50)
    
    def setup_scan_pay_tab(self):
        # Create a frame for the tab content
        content_frame = ttk.Frame(self.tab3, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Scan & Pay", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Create notebook for Live Camera and Upload Image tabs
        scan_notebook = ttk.Notebook(content_frame)
        scan_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        live_camera_tab = ttk.Frame(scan_notebook)
        upload_image_tab = ttk.Frame(scan_notebook)
        
        scan_notebook.add(live_camera_tab, text="Live Camera")
        scan_notebook.add(upload_image_tab, text="Upload Image")
        
        # Live Camera Tab
        live_left_frame = ttk.Frame(live_camera_tab)
        live_right_frame = ttk.Frame(live_camera_tab)
        
        live_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        live_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Camera controls
        camera_control_frame = ttk.Frame(live_left_frame)
        camera_control_frame.pack(fill=tk.X, pady=10)
        
        self.start_camera_button = ttk.Button(camera_control_frame, text="🎥 Start Camera", 
                                           command=self.start_camera)
        self.start_camera_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_camera_button = ttk.Button(camera_control_frame, text="⏹️ Stop Camera", 
                                          command=self.stop_camera, state=tk.DISABLED)
        self.stop_camera_button.pack(side=tk.LEFT, padx=5)
        
        # Camera feed frame
        self.camera_frame = ttk.LabelFrame(live_left_frame, text="Camera Feed")
        self.camera_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.video_label = ttk.Label(self.camera_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status label
        self.camera_status_label = ttk.Label(live_left_frame, text="Camera Inactive", foreground="blue")
        self.camera_status_label.pack(pady=5)
        
        # Payment details frame (right side)
        self.live_payment_frame = ttk.LabelFrame(live_right_frame, text="Payment Details")
        self.live_payment_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.live_payment_details_frame = ttk.Frame(self.live_payment_frame)
        self.live_payment_details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially show instructions
        self.live_payment_instructions = ttk.Label(self.live_payment_details_frame, 
                                                text="Start the camera and point it at a QR code to scan.",
                                                wraplength=300, justify="center")
        self.live_payment_instructions.pack(pady=50)
        
        # Upload Image Tab
        upload_left_frame = ttk.Frame(upload_image_tab)
        upload_right_frame = ttk.Frame(upload_image_tab)
        
        upload_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        upload_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Upload controls
        ttk.Label(upload_left_frame, text="Upload QR Code Image", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        self.upload_button = ttk.Button(upload_left_frame, text="Choose Image File", command=self.upload_image)
        self.upload_button.pack(pady=10)
        
        # Image display frame
        self.upload_image_frame = ttk.LabelFrame(upload_left_frame, text="Uploaded Image")
        self.upload_image_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.uploaded_image_label = ttk.Label(self.upload_image_frame)
        self.uploaded_image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.scan_uploaded_button = ttk.Button(upload_left_frame, text="🔍 Scan Uploaded Image", 
                                             command=self.scan_uploaded_image, state=tk.DISABLED)
        self.scan_uploaded_button.pack(pady=10)
        
        # Payment details frame (right side)
        self.upload_payment_frame = ttk.LabelFrame(upload_right_frame, text="Payment Details")
        self.upload_payment_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.upload_payment_details_frame = ttk.Frame(self.upload_payment_frame)
        self.upload_payment_details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially show instructions
        self.upload_payment_instructions = ttk.Label(self.upload_payment_details_frame, 
                                                  text="Upload an image containing a QR code and click 'Scan Uploaded Image'.",
                                                  wraplength=300, justify="center")
        self.upload_payment_instructions.pack(pady=50)
        
        # Payment success frame (hidden initially)
        self.payment_success_frame = ttk.Frame(content_frame)
        # Will be packed when payment is successful
    
    def setup_transaction_history_tab(self):
        # Create a frame for the tab content
        content_frame = ttk.Frame(self.tab4, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Transaction History", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Balance display
        self.transaction_balance_label = ttk.Label(content_frame, 
                                                text=f"Current Balance: PKR {self.balance:.2f}",
                                                font=("Arial", 12, "bold"))
        self.transaction_balance_label.pack(pady=10)
        
        # Scrollable frame for transactions
        self.transaction_canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.transaction_canvas.yview)
        self.scrollable_transaction_frame = ttk.Frame(self.transaction_canvas)
        
        self.scrollable_transaction_frame.bind(
            "<Configure>",
            lambda e: self.transaction_canvas.configure(scrollregion=self.transaction_canvas.bbox("all"))
        )
        
        self.transaction_canvas.create_window((0, 0), window=self.scrollable_transaction_frame, anchor="nw")
        self.transaction_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.transaction_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initially show no transactions message
        self.no_transactions_label = ttk.Label(self.scrollable_transaction_frame, 
                                            text="No Transactions Yet\n\nYour transaction history will appear here after you make your first payment.",
                                            wraplength=500, justify="center")
        self.no_transactions_label.pack(pady=50)
    
    def login(self):
        # Get values from entries
        username = self.username_entry.get().strip()
        cnic = self.cnic_entry.get().strip()
        
        try:
            balance = float(self.balance_entry.get().strip())
        except ValueError:
            self.login_error_label.config(text="Balance must be a valid number.")
            return
        
        # Validate inputs
        if not username:
            self.login_error_label.config(text="Please enter your name.")
            return
        
        if not self.validate_cnic(cnic):
            self.login_error_label.config(text="CNIC must be in the exact format: 00000-0000000-0")
            return
        
        # Set user data
        self.user_logged_in = True
        self.username = username
        self.user_cnic = cnic
        self.balance = balance
        
        # Clear login form and rebuild sidebar
        for widget in self.sidebar_top_frame.winfo_children():
            widget.destroy()
        
        self.setup_sidebar()
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
    
    def logout(self):
        # Reset all user data
        self.user_logged_in = False
        self.username = ""
        self.user_cnic = ""
        self.balance = 0.0
        self.qr_result = None
        self.scanning = False
        self.payment_confirmed = False
        self.payment_amount = 0.0
        self.payment_recipient = ""
        self.payment_cnic = ""
        self.transaction_history = []
        self.show_my_qr = False
        self.scan_state = "idle"
        self.parsed_payment_data = None
        self.live_scanning_active = False
        
        # Stop camera if active
        if self.camera_active:
            self.stop_camera()
        
        # Clear sidebar and rebuild
        for widget in self.sidebar_top_frame.winfo_children():
            widget.destroy()
        
        self.setup_sidebar()
        
        # Reset tab content
        self.setup_my_qr_tab()
        self.setup_generate_qr_tab()
        self.setup_scan_pay_tab()
        self.setup_transaction_history_tab()
    
    def validate_cnic(self, cnic):
        # Pattern for CNIC: 00000-0000000-0 (exactly this format)
        pattern = r'^\d{5}-\d{7}-\d{1}$'
        return bool(re.match(pattern, cnic))
    
    def generate_qr_code(self, data, box_size=10):
        # Convert data to JSON string
        json_data = json.dumps(data)
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,  # Adjustable box size parameter
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
    
    def show_my_qr_code(self):
        if not self.user_logged_in:
            messagebox.showwarning("Not Logged In", "Please log in first to generate your QR code.")
            return
        
        # Clear the display frame
        for widget in self.qr_display_frame.winfo_children():
            widget.destroy()
        
        # Create user data dictionary
        user_data = {
            "type": "user_info",
            "name": self.username,
            "cnic": self.user_cnic,
            "balance": self.balance
        }
        
        # Generate QR code
        qr_img = self.generate_qr_code(user_data, box_size=10)
        
        # Convert PIL image to Tkinter PhotoImage
        tk_img = ImageTk.PhotoImage(qr_img)
        
        # Display QR code
        qr_label = ttk.Label(self.qr_display_frame, image=tk_img)
        qr_label.image = tk_img  # Keep a reference to prevent garbage collection
        qr_label.pack(pady=10)
        
        # Display QR code information
        info_frame = ttk.LabelFrame(self.qr_display_frame, text="Your QR Code Information")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(info_frame, text=f"Name: {self.username}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"CNIC: {self.user_cnic}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"Balance: PKR {self.balance:.2f}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text="You can save the QR code by right-clicking on the image.", 
                 font=("Arial", 9, "italic")).pack(anchor="w", padx=10, pady=(10, 5))
    
    def generate_payment_qr(self):
        if not self.user_logged_in:
            messagebox.showwarning("Not Logged In", "Please log in first to generate a payment QR code.")
            return
        
        try:
            amount = float(self.payment_amount_entry.get().strip())
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError as e:
            messagebox.showerror("Invalid Amount", str(e))
            return
        
        # Clear the display frame
        for widget in self.payment_qr_display_frame.winfo_children():
            widget.destroy()
        
        # Create payment data dictionary
        payment_data = {
            "type": "payment",
            "sender": self.username,
            "sender_cnic": self.user_cnic,
            "amount": amount
        }
        
        # Generate QR code
        qr_img = self.generate_qr_code(payment_data, box_size=10)
        
        # Convert PIL image to Tkinter PhotoImage
        tk_img = ImageTk.PhotoImage(qr_img)
        
        # Display QR code
        qr_label = ttk.Label(self.payment_qr_display_frame, image=tk_img)
        qr_label.image = tk_img  # Keep a reference to prevent garbage collection
        qr_label.pack(pady=10)
        
        # Display payment information
        info_frame = ttk.LabelFrame(self.payment_qr_display_frame, text="Payment QR Code Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Sender: {self.username}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"CNIC: {self.user_cnic}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"Amount: PKR {amount:.2f}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text="You can save the QR code by right-clicking on the image.", 
                 font=("Arial", 9, "italic")).pack(anchor="w", padx=10, pady=(10, 5))
    
    def start_camera(self):
        if not self.user_logged_in:
            messagebox.showwarning("Not Logged In", "Please log in first to use the camera.")
            return
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera. Please check your camera connection.")
            return
        
        # Update UI
        self.camera_active = True
        self.start_camera_button.config(state=tk.DISABLED)
        self.stop_camera_button.config(state=tk.NORMAL)
        self.camera_status_label.config(text="Camera Active - Scanning for QR codes...")
        
        # Clear payment details
        for widget in self.live_payment_details_frame.winfo_children():
            widget.destroy()
        
        scanning_label = ttk.Label(self.live_payment_details_frame, 
                                 text="Point your camera at a QR code to scan it.",
                                 wraplength=300, justify="center")
        scanning_label.pack(pady=20)
        
        # Start camera thread
        self.camera_thread = Thread(target=self.camera_loop)
        self.camera_thread.daemon = True
        self.camera_thread.start()
    
    def camera_loop(self):
        # Initialize the QR code detector
        qr_detector = cv2.QRCodeDetector()
        
        while self.camera_active:
            ret, frame = self.cap.read()
            
            if not ret:
                self.camera_status_label.config(text="Error: Failed to capture frame.")
                break
            
            # Create a copy of the frame for display
            display_frame = frame.copy()
            qr_value = None
            
            # Try to detect and decode QR codes in the frame
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
            
            # Add status text to the frame
            status_text = "QR Code Scanner - Scanning..."
            cv2.putText(display_frame, status_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Convert BGR to RGB for Tkinter display
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img = ImageTk.PhotoImage(image=img)
            
            # Update the video label
            self.video_label.config(image=img)
            self.video_label.image = img  # Keep a reference to prevent garbage collection
            
            # If QR code detected, process it
            if qr_value:
                self.process_detected_qr(qr_value)
                break
            
            # Add a small delay to reduce CPU usage
            time.sleep(0.03)
    
    def process_detected_qr(self, qr_data):
        # Stop the camera
        self.stop_camera()
        
        # Parse the QR data
        try:
            payment_data, is_valid, message = self.parse_qr_data(qr_data)
            
            if is_valid:
                self.qr_result = qr_data
                self.parsed_payment_data = payment_data
                self.scan_state = "detected"
                
                # Update UI with payment details
                self.show_payment_details(payment_data, "live")
            else:
                messagebox.showerror("Invalid QR Code", message)
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse QR code data: {str(e)}")
    
    def show_payment_details(self, payment_data, source):
        # Clear the payment details frame
        if source == "live":
            for widget in self.live_payment_details_frame.winfo_children():
                widget.destroy()
            
            details_frame = self.live_payment_details_frame
        else:  # upload
            for widget in self.upload_payment_details_frame.winfo_children():
                widget.destroy()
            
            details_frame = self.upload_payment_details_frame
        
        # Display payment details
        ttk.Label(details_frame, text="Payment Detected", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        ttk.Label(details_frame, text=f"Recipient: {payment_data['sender']}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(details_frame, text=f"CNIC: {payment_data['sender_cnic']}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(details_frame, text=f"Amount: PKR {payment_data['amount']:.2f}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(details_frame, text=f"Your Balance: PKR {self.balance:.2f}").pack(anchor="w", padx=10, pady=2)
        
        # Payment buttons
        buttons_frame = ttk.Frame(details_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        if self.balance >= payment_data['amount']:
            pay_button = ttk.Button(buttons_frame, text="💰 Pay Now", 
                                 command=lambda: self.process_payment(payment_data, source))
            pay_button.pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(buttons_frame, text="💸 Insufficient funds", foreground="red").pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(buttons_frame, text="🚫 Cancel", 
                                command=lambda: self.cancel_payment(source))
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def process_payment(self, payment_data, source):
        if self.balance >= payment_data['amount']:
            # Update user balance
            self.balance -= payment_data['amount']
            
            # Record the transaction
            transaction = {
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "payment",
                "amount": payment_data['amount'],
                "recipient": payment_data['sender'],
                "recipient_cnic": payment_data['sender_cnic'],
                "balance_after": self.balance
            }
            
            self.transaction_history.append(transaction)
            
            # Update UI
            self.scan_state = "confirmed"
            self.show_payment_success(transaction, source)
            
            # Update sidebar balance display
            self.setup_sidebar()
            
            # Update transaction history tab
            self.update_transaction_history()
            
            return True, f"Payment of PKR {payment_data['amount']:.2f} to {payment_data['sender']} was successful."
        else:
            messagebox.showerror("Payment Failed", f"Insufficient funds. Your balance is PKR {self.balance:.2f}.")
            return False, f"Insufficient funds. Your balance is PKR {self.balance:.2f}."
    
    def show_payment_success(self, transaction, source):
        # Clear the payment details frame
        if source == "live":
            for widget in self.live_payment_details_frame.winfo_children():
                widget.destroy()
            
            details_frame = self.live_payment_details_frame
        else:  # upload
            for widget in self.upload_payment_details_frame.winfo_children():
                widget.destroy()
            
            details_frame = self.upload_payment_details_frame
        
        # Display success message
        success_frame = ttk.LabelFrame(details_frame, text="Payment Successful!")
        success_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(success_frame, text=f"Amount Paid: PKR {transaction['amount']:.2f}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(success_frame, text=f"Recipient: {transaction['recipient']}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(success_frame, text=f"New Balance: PKR {transaction['balance_after']:.2f}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(success_frame, text=f"Transaction Time: {transaction['date']}").pack(anchor="w", padx=10, pady=2)
        
        # Buttons
        buttons_frame = ttk.Frame(details_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        scan_another_button = ttk.Button(buttons_frame, text="🔄 Scan Another QR Code", 
                                      command=lambda: self.reset_scan_state(source))
        scan_another_button.pack(side=tk.LEFT, padx=5)
        
        view_transactions_button = ttk.Button(buttons_frame, text="📊 View Transactions", 
                                           command=self.show_transaction_tab)
        view_transactions_button.pack(side=tk.LEFT, padx=5)
    
    def reset_scan_state(self, source):
        self.scan_state = "idle"
        self.qr_result = None
        self.parsed_payment_data = None
        
        # Reset UI
        if source == "live":
            for widget in self.live_payment_details_frame.winfo_children():
                widget.destroy()
            
            self.live_payment_instructions = ttk.Label(self.live_payment_details_frame, 
                                                    text="Start the camera and point it at a QR code to scan.",
                                                    wraplength=300, justify="center")
            self.live_payment_instructions.pack(pady=50)
        else:  # upload
            for widget in self.upload_payment_details_frame.winfo_children():
                widget.destroy()
            
            self.upload_payment_instructions = ttk.Label(self.upload_payment_details_frame, 
                                                      text="Upload an image containing a QR code and click 'Scan Uploaded Image'.",
                                                      wraplength=300, justify="center")
            self.upload_payment_instructions.pack(pady=50)
            
            # Reset uploaded image
            self.uploaded_image_label.config(image='')
            self.scan_uploaded_button.config(state=tk.DISABLED)
    
    def cancel_payment(self, source):
        self.reset_scan_state(source)
    
    def show_transaction_tab(self):
        # Switch to transaction history tab
        self.notebook.select(self.tab4)
    
    def stop_camera(self):
        # Stop the camera
        self.camera_active = False
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        # Update UI
        self.start_camera_button.config(state=tk.NORMAL)
        self.stop_camera_button.config(state=tk.DISABLED)
        self.camera_status_label.config(text="Camera Inactive")
        
        # Clear video display
        self.video_label.config(image='')
    
    def upload_image(self):
        if not self.user_logged_in:
            messagebox.showwarning("Not Logged In", "Please log in first to upload an image.")
            return
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select QR Code Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if not file_path:  # User cancelled
            return
        
        try:
            # Open and display the image
            image = Image.open(file_path)
            
            # Resize image for display if needed
            max_size = (300, 300)
            image.thumbnail(max_size, Image.LANCZOS)
            
            # Convert to Tkinter PhotoImage
            tk_img = ImageTk.PhotoImage(image)
            
            # Display image
            self.uploaded_image_label.config(image=tk_img)
            self.uploaded_image_label.image = tk_img  # Keep a reference
            
            # Store original image for processing
            self.uploaded_image = Image.open(file_path)
            
            # Enable scan button
            self.scan_uploaded_button.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image: {str(e)}")
    
    def scan_uploaded_image(self):
        if not hasattr(self, 'uploaded_image'):
            messagebox.showerror("Error", "No image uploaded.")
            return
        
        # Convert PIL image to numpy array for OpenCV
        img_array = np.array(self.uploaded_image)
        
        # Convert RGB to BGR for OpenCV if needed
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Process image
        _, qr_value = self.detect_qr_code(img_array)
        
        if qr_value:
            # Parse the QR data
            payment_data, is_valid, message = self.parse_qr_data(qr_value)
            
            if is_valid:
                self.qr_result = qr_value
                self.parsed_payment_data = payment_data
                self.scan_state = "detected"
                
                # Update UI with payment details
                self.show_payment_details(payment_data, "upload")
            else:
                messagebox.showerror("Invalid QR Code", message)
        else:
            messagebox.showerror("No QR Code Detected", "No QR code was found in the uploaded image.")
    
    def detect_qr_code(self, frame):
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
    
    def parse_qr_data(self, qr_data):
        try:
            payment_data = json.loads(qr_data)
            if 'type' in payment_data and payment_data['type'] == 'payment':
                return payment_data, True, "Valid payment QR code detected."
            else:
                return None, False, "Invalid QR code: Not a payment request."
        except Exception as e:
            return None, False, f"Error: Could not parse QR code data. {str(e)}"
    
    def update_transaction_history(self):
        # Update balance display
        self.transaction_balance_label.config(text=f"Current Balance: PKR {self.balance:.2f}")
        
        # Clear transaction frame
        for widget in self.scrollable_transaction_frame.winfo_children():
            widget.destroy()
        
        if self.transaction_history:
            # Display transactions in reverse order (newest first)
            for i, transaction in enumerate(reversed(self.transaction_history)):
                transaction_frame = ttk.LabelFrame(
                    self.scrollable_transaction_frame, 
                    text=f"Transaction #{len(self.transaction_history) - i}"
                )
                transaction_frame.pack(fill=tk.X, padx=10, pady=5)
                
                ttk.Label(transaction_frame, text=f"Date: {transaction['date']}").pack(anchor="w", padx=10, pady=2)
                ttk.Label(transaction_frame, text=f"Type: {transaction['type'].title()}").pack(anchor="w", padx=10, pady=2)
                ttk.Label(transaction_frame, text=f"Amount: PKR {transaction['amount']:.2f}").pack(anchor="w", padx=10, pady=2)
                ttk.Label(transaction_frame, text=f"Recipient: {transaction['recipient']}").pack(anchor="w", padx=10, pady=2)
                ttk.Label(transaction_frame, text=f"Recipient CNIC: {transaction['recipient_cnic']}").pack(anchor="w", padx=10, pady=2)
                ttk.Label(transaction_frame, text=f"Balance After: PKR {transaction['balance_after']:.2f}").pack(anchor="w", padx=10, pady=2)
        else:
            # Show no transactions message
            self.no_transactions_label = ttk.Label(self.scrollable_transaction_frame, 
                                                text="No Transactions Yet\n\nYour transaction history will appear here after you make your first payment.",
                                                wraplength=500, justify="center")
            self.no_transactions_label.pack(pady=50)
    
    def on_closing(self):
        # Stop camera if active
        if self.camera_active:
            self.stop_camera()
        
        # Close the application
        self.root.destroy()

# Main function to run the application
def main():
    root = tk.Tk()
    app = QRPaymentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()