import streamlit as st
import base64

# Function to get the image as a base64 string
def get_image_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

st.set_page_config(layout="wide")

try:
    with open("form.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("CSS file not found. Please make sure 'form.css' is in the same folder.")

# Get the base64 string of the image
try:
    image_path = "resources/icons/profile.png"
    image_base64 = get_image_as_base64(image_path)

    # The icon itself, now an image
    st.markdown(f"""
    <div class="profile-icon">
        <a href="#" title="Profil beállítások">
            <img src="data:image/png;base64,{image_base64}" class="profile-img">
        </a>
    </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Profile image not found. Please make sure the file exists at 'resources/icons/profile.png'")

st.title("HR System", text_alignment="center")

if st.button(label="Permissions", width="content", icon_position="right", type="primary"):
    st.switch_page("pages/Permissions.py")

