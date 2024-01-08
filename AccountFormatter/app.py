import tkinter as tk
from tkinter import filedialog, messagebox, Label, Button, Text

root = tk.Tk()
root.title("Chuyển định dạng file")
root.geometry("500x400")
root.configure(bg='#f5f5f5')

main_frame = tk.Frame(root, bg='#f5f5f5')
main_frame.pack(pady=20)

title = Label(main_frame, text="Chuyển định dạng file", 
              font=("Arial",24,"bold"), bg='#f5f5f5')
title.pack(pady=10)

instruction = Label(main_frame, text="Hướng dẫn:",  
                    font=("Arial",14), bg='#f5f5f5')
instruction.pack(pady=5)

text = Text(main_frame, width=40, height=5, 
             font=("Arial",12), bg='#fff')
text.insert(tk.END, "tk////thông tin////mk////cookie -> tk:mk:cookie\n")
text.insert(tk.END, "1. Chọn file input.txt\n")
text.insert(tk.END, "2. Chọn file output.txt\n")  
text.config(state='disabled', relief=tk.FLAT)
text.pack(pady=10)

def convert_file():
    input_file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])
    if not input_file_path:
        return
    output_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[('Text Files', '*.txt')])
    if not output_file_path:
        return

    with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
        for line in input_file:
            parts = line.split('////')
            if len(parts) == 4:
                new_line = parts[0] + ':' + parts[2] + ':' + parts[3]
                output_file.write(new_line)

    messagebox.showinfo("Thông báo", "Chuyển đổi file thành công!")
    root.destroy()

button = Button(main_frame, text="Chuyển đổi", 
                command=convert_file)
button.pack(pady=20) 

root.mainloop()
