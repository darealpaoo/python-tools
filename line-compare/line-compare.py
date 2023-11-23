def compare_files(file1_path, file2_path, output_path):
    # Đọc nội dung từ file 1
    with open(file1_path, 'r', encoding='utf-8') as file1:
        lines1 = set(file1.readlines())

    # Đọc nội dung từ file 2
    with open(file2_path, 'r', encoding='utf-8') as file2:
        lines2 = set(file2.readlines())

    # Tìm dòng có trong file 2 mà không có trong file 1
    missing_lines_2 = lines2 - lines1

    # Ghi kết quả vào file 3
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write("\n".join(sorted(missing_lines_2)))

if __name__ == "__main__":
    file1_path = "file1.txt"
    file2_path = "file2.txt"
    output_path = "file3.txt"

    compare_files(file1_path, file2_path, output_path)
