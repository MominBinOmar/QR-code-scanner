import cv2
import cv2
import numpy as np
import time
import streamlit as st

def detect_qr_code_continuous():
    # Initialize the QR code detector
    qr_detector = cv2.QRCodeDetector()
    
    # Initialize the camera (0 is usually the default camera)
    camera_id = 0
    cap = cv2.VideoCapture(camera_id)
    
    # Check if the camera opened successfully
    if not cap.isOpened():
        st.error("Error: Could not open camera.")
        return None
    
    st.info("Camera opened successfully. Scanning for QR codes...")
    
    # Create a placeholder for the video feed
    video_placeholder = st.empty()
    
    # Variable to store the QR code value
    qr_value = None
    
    # Create a status placeholder
    status_placeholder = st.empty()
    status_placeholder.info("Scanning for QR codes...")
    
    while True:
        # Read a frame from the camera
        ret, frame = cap.read()
        
        if not ret:
            st.error("Error: Failed to capture frame.")
            break
        
        # Create a copy of the frame for display
        display_frame = frame.copy()
        
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
                        display_frame = cv2.putText(display_frame, s, p[0].astype(int), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                        # Convert BGR to RGB for Streamlit display
                        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                        
                        # Show the final frame with the detected QR code
                        video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                        status_placeholder.success(f"QR Code detected: {s}")
                        
                        # Break the loop after detecting a QR code
                        break
                
                # If we found a valid QR code, break the main loop
                if qr_value:
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
                    display_frame = cv2.putText(display_frame, data, (bbox[0][0], bbox[0][1] - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    # Convert BGR to RGB for Streamlit display
                    rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    
                    # Show the final frame with the detected QR code
                    video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                    status_placeholder.success(f"QR Code detected: {data}")
                    
                    # Break the loop after detecting a QR code
                    break
            except Exception as e:
                # Just continue if there's an error
                pass
        
        # Add status text to the frame
        status_text = "QR Code Scanner - Scanning..."
        cv2.putText(display_frame, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Convert BGR to RGB for Streamlit display
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Display the frame in Streamlit
        video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
        
        # Add a small delay to reduce CPU usage
        time.sleep(0.03)
    
    # Release the camera
    cap.release()
    
    return qr_value
    
    return qr_value

# Run the continuous QR code detection
if __name__ == "__main__":
    print("Starting continuous QR code detection...")
    result = detect_qr_code_continuous()
    
    if result:
        print(f"\nLast detected QR Code Value: {result}")
    else:
        print("\nNo QR code was detected or the camera was closed before detection.")