import tkinter as tk
from PIL import Image, ImageTk

from camera_tracker import CameraTracker

class GCS(tk.Tk):
    def __init__(self, *args, **kwargs):
        
        # Init Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("AMSL GCS")
        self.canvas = tk.Canvas(self, height=432, width=1536)
        self.canvas.pack()

        self.tracker = CameraTracker()
        self.tracker.start()

        self.update()

        self.frame_tk = None
        self.canvas_image = None
        self.canvas_marker = None



    def update(self):
        img,pose = self.tracker.latest()
        
        if img is not None:
            self.frame_tk = ImageTk.PhotoImage(image=Image.fromarray(img))
            if self.canvas_image is None:
                self.canvas_image = self.canvas.create_image(0,0,anchor='nw',image=self.frame_tk)
            else:
                self.canvas.itemconfig(self.canvas_image,image=self.frame_tk)
        if pose is not None:
            if self.canvas_marker is None:
                self.canvas_marker = self.canvas.create_oval(pose[0]-5,pose[1]-5,pose[0]+5,pose[1]+5,fill='blue',outline='blue')
            else:
                self.canvas.coords(self.canvas_marker,pose[0]-5,pose[1]-5,pose[0]+5,pose[1]+5)
        self.after(50,self.update)


if __name__ == '__main__':
    gcs = GCS()
    gcs.mainloop()
