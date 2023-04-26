#open-tabs.py version 1.0
import webbrowser

# Đường dẫn tới file list.txt
file_path = "list.txt"

# Đường dẫn tới trang web cần mở
url_pattern = "https://www.roblox.com/search/users?keyword={}"

# Mở file list.txt và đọc các tên
with open(file_path, "r") as f:
    names = f.read().splitlines()

# Mở các trang web tương ứng với từng tên
for name in names:
    url = url_pattern.format(name)
    webbrowser.open_new_tab(url)