import cv2
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from tktooltip import ToolTip
import os
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim
from PIL import Image
import tempfile
import shutil

# main window
root = tk.Tk()
root.title("video2pdf")
root.geometry()
# Stylemanagement
s = ttk.Style()
s.theme_use('clam')
s.configure("green.Horizontal.TProgressbar", foreground='grey', background='#62f1b4')

file_path = ""
folder_path = ""

# function to select file
def select_file(entry):
    global file_path
    file_path = filedialog.askopenfilename(title="Select Video", filetypes=(("Video files", "*.mp4"), ("All files", "*.*")))
    if file_path == "":
        tk.messagebox.showerror("Error", "Please chose a video file. It has to be in the .mp4 format.")
        return
    entry.delete(0, tk.END)
    entry.insert(0, file_path)

# function to select folder
def select_folder(entry):
    global folder_path
    folder_path = filedialog.askdirectory(title = "Select folder")
    if folder_path == "":
        tk.messagebox.showerror("Error", "Please chose a output directory for the .pdf file.")
        return
    entry.delete(0, tk.END)
    entry.insert(0, folder_path)

def check_variables():
    value1 = entry1.get()
    value2 = entry2.get()
    value3 = entry3.get()
    if not value1:
        tk.messagebox.showerror("Error", "Please enter a value for the PDF name")
        return False
    if not value2:
        tk.messagebox.showerror("Error", "Please enter a value for the frame rate")
        return False
    if not value3:
        tk.messagebox.showerror("Error", "Please enter a value for the threshold")
        return False
    return True

def stop_comparing_frames():
    global stop_comparing
    answer = tk.messagebox.askyesno("Stop Comparison", "Are you sure you want to stop the comparison?")
    if answer:
        stop_comparing = True

def compare_frames(video_path):
    global stop_comparing
    stop_comparing = False
    value2 = entry2.get()
    value3 = entry3.get()
    value2 = int(value2)
    value3 = float(value3)
    #load vid
    cap = cv2.VideoCapture(video_path)
    #get total frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    #defines progress bar
    progress = tk.ttk.Progressbar(inbetween_frame, style="green.Horizontal.TProgressbar", orient="horizontal", length=500, mode="determinate")
    progress.pack(side="top")
    
    previous_frame = None
    frame_counter = 0
    i = 0
    screenshot_paths = []
    while True:
        if stop_comparing:
            break
        ret, frame = cap.read()
        if not ret:
            break

        if frame_counter % value2 == 0:
            if previous_frame is not None:
                #does the actual comparison
                ssim = compare_ssim(np.array(previous_frame), np.array(frame), channel_axis=2)
                if ssim < (1-value3/100):
                    # Take screenshot
                    screenshot_path = os.path.join(temp_dir, "screenshot_{}.png".format(i))
                    cv2.imwrite(screenshot_path, frame)
                    screenshot_paths.append(screenshot_path)
                    i += 1          

            previous_frame = frame
            # Update progressbar
            progress["value"] = ((frame_counter / total_frames)*100)
            root.update()       
            
        frame_counter += 1        

    cap.release()
    cv2.destroyAllWindows()
    return screenshot_paths

def create_pdf(screenshot_paths, pdf_path):
    if stop_comparing:
        return
    images = [Image.open(screenshot) for screenshot in screenshot_paths]
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    # Delete temporary directory and its contents
    shutil.rmtree(temp_dir)
    messagebox.showinfo("Processing Finished", "Processing finished")

# function to start script
def start_script():
    start_button.config(state="disabled")
    start_button.after(2000, lambda: start_button.config(state="normal"))
    global file_path, folder_path
    # check for missing input
    if not file_path:
        select_file(input_entry)
    if not folder_path:
        select_folder(output_entry)
    if not file_path or not folder_path:
        return
    if not check_variables():
        return
    # Create temporary directory
    global temp_dir
    temp_dir = tempfile.mkdtemp()
    # main code
    value1 = entry1.get()
    screenshot_paths = compare_frames(file_path)
    pdf_path = os.path.join(folder_path, value1 + ".pdf")
    create_pdf(screenshot_paths, pdf_path)

# top area
top_frame = tk.Frame(root)
top_frame.pack(side="top", fill="both", expand=True)

# First row
input_label = tk.Label(top_frame, text="Input file", font=(15))
input_label.grid(row=0, column=0, sticky="nesw")
input_button = tk.Button(top_frame, text="select", font=(12), width=5, height=1, command=lambda: select_file(input_entry))
ToolTip(input_button, msg="Select the .mp4 file here. Alternatively if you have a directory link you can although post that. There is no drag and drop support yet", delay=1.5)
input_button.grid(row=0, column=1, sticky="nesw")
input_entry = tk.Entry(top_frame, font=(12), width=40)
input_entry.grid(row=0, column=2, sticky="nesw")
# Second row
output_label = tk.Label(top_frame, text="Output Folder", font=(15))
output_label.grid(row=1, column=0, sticky="nesw")
output_button = tk.Button(top_frame, text="select", font=(12), width=5, height=1, command=lambda: select_folder(output_entry))
ToolTip(output_button, msg="Choose the output folder for the pdf here", delay=1.5)
output_button.grid(row=1, column=1, sticky="nesw")
output_entry = tk.Entry(top_frame, font=(12), width=40)
output_entry.grid(row=1, column=2, sticky="nesw")

# middle area
middle_frame = tk.Frame(root)
middle_frame.pack(side="top", fill="both", expand=True)

#input1 Name of PDF File
label1 = tk.Label(middle_frame, text="PDF name:", font=(15))
ToolTip(label1, msg="Name the designated PDF file", delay=1.5)
label1.grid(row=0, column=0, sticky="ne")
entry1 = tk.Entry(middle_frame, font=(15), width=14)
entry1.grid(row=0, column=1, sticky="nesw")

#input2 Amount of frames skipped
label2 = tk.Label(middle_frame, text="Frames to skip each cycle:", font=(15))
ToolTip(label2, msg="This script uses single core heavy comparison. To speed up the process not every frame is being analyzed. Usually a .mp4 file runs with 30 to 60 fps. That said, entering 60 in the field will copare every 60th frame, so in case of 60 fps it will compare the video every second. If the progress takes really long and there is rarely anything happening in the video, this value can be adjusted to as high as you want it to go. The speed increases nearly linear", delay=1.5)
label2.grid(row=1, column=0, sticky="ne")
entry2 = tk.Entry(middle_frame, font=(15), width=2)
entry2.grid(row=1, column=1, sticky="nesw")
entry2.insert(0, "60")

#input3 Similarity Index
label3 = tk.Label(middle_frame, text="Difference to trigger a screenshot:", font=(15))
ToolTip(label3, msg="This is the minimum difference that triggers a screenshot being saved in the pdf. The underlying mechanism is SSIM/Structural Similarity comparison. This is very robust to changes in image quality and artifacts and wont trigger off those like greyscale comparison. I have found that 2.5 is somewhat a sweetspot to trigger when around 1/4 of a regular PowerPoint with the same background changes. Depending on your needs you will have to experiment with this setting to decrease false discovery and increase precision. This although can be adjusted further in casse you have moving elements in the video aswell, but dont want to trigger a screenshot. Like an recording of a speech or zoom call, where a presentation is the main interest but there are although video snapshots of people talking", delay=1.5)
label3.grid(row=2, column=0, sticky="ne")
entry3 = tk.Entry(middle_frame, font=(15), width=2)
entry3.grid(row=2, column=1, sticky="nesw")
entry3.insert(0, "2.5")

# progressbar area
inbetween_frame = tk.Frame(root)
inbetween_frame.pack(side="top", fill="both", expand=True)

# bottom area
bottom_frame = tk.Frame(root)
bottom_frame.pack(side="bottom", fill="both", expand=True)

start_button = tk.Button(bottom_frame, text="Start", height=2, width=6, command=start_script)
ToolTip(start_button, msg="Start the process", delay=2)
start_button.pack(side='left', fill="x", expand=True)

stop_button = tk.Button(bottom_frame, text="Stop", height=2, width=6, command=stop_comparing_frames)
ToolTip(stop_button, msg="You will get asked if you really want to stop the process. All progress will be lost and you will have to restart. Depending on your settings and the lenth of the video it might take some minutes to finish. If the progress bar is moving, everything should be working", delay=2)
stop_button.pack(side='right', fill="x", expand=True)

#keep window open
root.mainloop()
