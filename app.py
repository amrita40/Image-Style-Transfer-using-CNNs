from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from style_transfer import style_transfer  # Ensure this function works correctly

app = Flask(__name__)

# Define directories for uploads and outputs
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=["POST"])
def upload_file():
    try:
        # Check if both content and style images are provided
        if "content_image" not in request.files or "style_image" not in request.files:
            return jsonify({"error": "Both content and style images are required!"}), 400

        content_file = request.files["content_image"]
        style_file = request.files["style_image"]

        # Validate filenames
        if content_file.filename == "" or style_file.filename == "":
            return jsonify({"error": "No file selected!"}), 400

        # Define file paths
        content_path = os.path.join(app.config["UPLOAD_FOLDER"], content_file.filename)
        style_path = os.path.join(app.config["UPLOAD_FOLDER"], style_file.filename)
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], f"styled_{content_file.filename}")

        # Save files
        content_file.save(content_path)
        style_file.save(style_path)

        print(f"✅ Content Image Saved at: {content_path}")
        print(f"✅ Style Image Saved at: {style_path}")

        # Apply Style Transfer (Ensure `style_transfer` function is implemented correctly)
        styled_image_path = style_transfer(content_path, style_path, output_path)

        if not os.path.exists(styled_image_path):
            return jsonify({"error": "Failed to generate styled image."}), 500

        print(f"🎨 Styled Image Generated at: {styled_image_path}")

        # Return the path to the generated styled image
        return jsonify({"styled_image_url": f"/{styled_image_path}"})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/static/output/<filename>')
def get_output_image(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)
