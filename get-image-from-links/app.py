import os
import requests

# Đường dẫn tới tệp tin chứa danh sách liên kết
link_file_path = "link.txt"

# Tên thư mục để lưu trữ các tệp tin ảnh tải về
image_folder = "images"
if not os.path.exists(image_folder):
    os.mkdir(image_folder)

# Đọc danh sách liên kết từ tệp tin
with open(link_file_path, "r") as f:
    links = f.readlines()

# Tải các tệp tin ảnh từ danh sách liên kết
for link in links:
    link = link.strip()  # Loại bỏ các ký tự trống (space, newline) ở đầu và cuối liên kết
    filename = link.split("/")[-1]  # Lấy tên tệp tin từ liên kết
    filepath = os.path.join(image_folder, filename)  # Tạo đường dẫn đến tệp tin lưu trữ
    response = requests.get(link, stream=True)  # Tải tệp tin ảnh từ liên kết
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {filename}")
print("All images downloaded!")