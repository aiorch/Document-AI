import os
import shutil

from pdf2image import convert_from_path
from PIL import Image, ImageDraw


def get_script_directory():
    """
    Get the directory where the current script is located.

    Returns:
        str: The absolute path of the script's directory.
    """
    return os.path.dirname(os.path.abspath(__file__))


def extract_signatures(coordinates_dir, document_pages_dir, output_base_dir):
    """
    Extract signatures from document pages based on bounding box coordinates.

    Args:
        coordinates_dir (str): Directory containing text files with bounding box coordinates.
        document_pages_dir (str): Directory containing document pages as images.
        output_base_dir (str): Directory to save the extracted signatures.
    """
    if os.path.exists(output_base_dir):
        shutil.rmtree(output_base_dir)
    os.makedirs(output_base_dir)

    for coordinates_file in os.listdir(coordinates_dir):
        if coordinates_file.endswith(".txt"):
            page_number = (
                coordinates_file.split("-")[-1].split(".")[0].replace("page_", "")
            )

            image_path = os.path.join(document_pages_dir, f"page_{page_number}.jpg")
            if not os.path.exists(image_path):
                print(f"Image for {coordinates_file} not found. Skipping...")
                continue

            page_image = Image.open(image_path)
            img_width, img_height = page_image.size

            output_folder = os.path.join(output_base_dir, f"page{page_number}")
            os.makedirs(output_folder, exist_ok=True)

            # Read bounding box coordinates
            bounding_boxes = []
            with open(os.path.join(coordinates_dir, coordinates_file), "r") as file:
                for line in file:
                    values = line.strip().split()
                    _, x_center, y_center, width, height = map(float, values)

                    x_center *= img_width
                    y_center *= img_height
                    box_width = width * img_width
                    box_height = height * img_height

                    x_min = int(x_center - box_width / 2)
                    y_min = int(y_center - box_height / 2)
                    x_max = int(x_center + box_width / 2)
                    y_max = int(y_center + box_height / 2)

                    bounding_boxes.append((x_min, y_min, x_max, y_max))

            # Sort bounding boxes by y-coordinate (top to bottom)
            sorted_boxes = sorted(bounding_boxes, key=lambda box: box[1])

            # Draw boxes and save cropped signatures
            for i, box in enumerate(sorted_boxes):
                x_min, y_min, x_max, y_max = box
                # Uncomment to visualize bounding boxes on the page
                # draw.rectangle(box, outline="red", width=2)

                # Crop and save the detected signature
                cropped_signature = page_image.crop((x_min, y_min, x_max, y_max))
                cropped_signature.save(
                    os.path.join(output_folder, f"signature_{i+1}.png")
                )

            print(f"Processed {coordinates_file} and saved to {output_folder}")


def pdf_to_images(pdf_path, output_dir, dpi=300):
    """
    Convert a PDF into a directory of JPG images.

    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save the images.
        dpi (int): Resolution of the output images (default: 300).
    """
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)

    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i + 1}.jpg")
        image.save(image_path, "JPEG")
        print(f"Saved: {image_path}")


if __name__ == "__main__":
    # Set up paths relative to the script's directory
    script_dir = get_script_directory()
    pdf_path = os.path.join(script_dir, "uploads", "574 (1).pdf")
    coordinates_dir = os.path.join(script_dir, "yolov5_data", "original_labels")
    document_pages_dir = os.path.join(script_dir, "images", "pages")
    output_base_dir = os.path.join(
        script_dir, "images", "signatures", "detected_signatures"
    )

    # Process the PDF and extract signatures
    pdf_to_images(pdf_path, document_pages_dir)
    extract_signatures(coordinates_dir, document_pages_dir, output_base_dir)
