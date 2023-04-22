#video_split.py version 1.0
import os
import psutil
import ctypes
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import speedx
from concurrent.futures import ThreadPoolExecutor

ctypes.windll.kernel32.SetConsoleTitleW("Video Split")

# Hàm để tách và xuất video
def split_and_save_video(input_file, duration, output_dir, segment):
    # Load file video gốc
    video = VideoFileClip(input_file)

    # Tính toán thời gian bắt đầu và kết thúc của phân đoạn
    start_time = segment * duration
    end_time = min((segment + 1) * duration, video.duration)

    # Cắt phân đoạn và tăng tốc video
    subclip = video.subclip(start_time, end_time)
    subclip = speedx(subclip, 1.0)

    # Đặt tên file xuất ra
    output_file = os.path.join(output_dir, f'output_{segment}.mp4')

    # Giới hạn tài nguyên của luồng
    process = psutil.Process(os.getpid())
    cpu_count = psutil.cpu_count(logical=True)
    cpu_limit = int(cpu_count * 0.5) # Giới hạn 50% mỗi luồng, có thể tùy chỉnh số 0.5 thành số nào mà bạn muốn, tối đa 1.0 (không khuyến khích)
    process.cpu_affinity(list(range(cpu_count)))  # Giới hạn tất cả các luồng theo cpu_limit ở trên

    # Giới hạn CPU sử dụng tối đa của luồng đang chạy
    os.system(f"taskset -cp {os.getpid()}")

    # Xuất phân đoạn thành file .mp4 với độ phân giải 1080p và tốc độ khung hình 60fps
    subclip.write_videofile(output_file, fps=60, codec='libx264', audio_codec='aac', bitrate='5000k', preset='ultrafast', remove_temp=True, threads=1)

    # Giải phóng tài nguyên
    video.close()

# Hàm chính
def main():
    # Thêm đoạn code tìm kiếm file video trong thư mục hiện tại
    video_files = []
    for file_name in os.listdir():
        if file_name.endswith(".mp4"):
            video_files.append(file_name)

    # Kiểm tra nếu không có file video nào trong thư mục
    if not video_files:
        print("Không tìm thấy file video trong thư mục.\n5 giây sau sẽ tắt chương trình...")
        time.sleep(5)
        return

    # In danh sách các file video
    print("Các file video trong thư mục:")
    for i, file_name in enumerate(video_files):
        print(f"{i+1}. {file_name}")

    # Yêu cầu người dùng chọn file video
    selection = int(input("Nhập số thứ tự của file video muốn tách: "))
    input_file = video_files[selection-1]

    duration = int(input('Nhập số giây cần tách: '))

    # Lấy đường dẫn thư mục hiện tại
    current_dir = os.getcwd()

    # Tạo đường dẫn đến thư mục xuất output
    output_dir = os.path.join(current_dir, 'output')

    # Tạo thư mục để lưu output nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load file video gốc
    video = VideoFileClip(input_file)

    # Tính toán số phân đoạn cần cắt
    num_segments = int(video.duration // duration)

    # Sử dụng ThreadPoolExecutor để tách và xuất các phân đoạn video cùng lúc
    with ThreadPoolExecutor(max_workers=psutil.cpu_count(logical=True)) as executor:
        # Tạo danh sách các đối tượng Future để theo dõi các tiến trình xử lý
        futures = []
        for i in range(num_segments):
            future = executor.submit(split_and_save_video, input_file, duration, output_dir, i)
            futures.append(future)

        # Đợi cho tất cả các tiến trình xử lý hoàn thành
        for future in futures:
            future.result()

    # Lưu phần còn lại của video
    last_duration = video.duration - num_segments * duration
    last_segment = VideoFileClip(input_file).subclip(num_segments * duration, video.duration)
    last_segment = speedx(last_segment, 1.0)
    last_output_file = os.path.join(output_dir, f'output_{num_segments}.mp4')
    last_segment.write_videofile(last_output_file, fps=60, codec='libx264', audio_codec='aac', bitrate='5000k', preset='ultrafast', remove_temp=True, threads=1)

    # Giải phóng tài nguyên
    video.close()

    print('Hoàn thành!')

if __name__ == '__main__':
    main()