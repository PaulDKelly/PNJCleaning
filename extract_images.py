import docx
import os

def extract_images_from_docx(docx_path, output_dir):
    doc = docx.Document(docx_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_count = 0
    for i, rel in enumerate(doc.part.rels.values()):
        if "image" in rel.target_ref:
            image_count += 1
            image_data = rel.target_part.blob
            ext = os.path.splitext(rel.target_ref)[1]
            image_path = os.path.join(output_dir, f"image_{image_count}{ext}")
            with open(image_path, "wb") as f:
                f.write(image_data)
            print(f"Extracted: {image_path}")
            
    return image_count

if __name__ == "__main__":
    path = r"E:\Code\Projects\PNJCleaning\08012026 Chuck and Blade Dolphin Centre.docx"
    # Put them in backend/app/static/images
    out_dir = r"E:\Code\Projects\PNJCleaning\backend\app\static\images"
    count = extract_images_from_docx(path, out_dir)
    print(f"Total images extracted: {count}")
