import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from GPS_T2_Khalife import Read_rinex, process_prn, plot_all_paths

RINEX_PATH = "GODS00USA_R_20240010000_01D_GN.rnx"
LOGO_PATH = "logo.jpg"
BG_PATH = "background.jpg"

class IntroPage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GPS Satellite Tracker")
        self.geometry("700x500")
        self.configure(bg="#121212")

        try:
            bg_img = Image.open(BG_PATH).resize((700, 500), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(bg_img)
            bg_label = tk.Label(self, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print("Background image error:", e)

        frame = tk.Frame(self, bg="#1e1e1e", bd=0)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=600, height=450)

        title = tk.Label(frame, text="GPS Satellite Path Computation", font=("Arial", 20, "bold"),
                         bg="#1e1e1e", fg="cyan", justify="center")
        title.pack(pady=10)

        info_frame = tk.Frame(frame, bg="#1e1e1e")
        info_frame.pack(pady=10)

        labels = [
            "University of Tehran",
            "Global Positioning Systems",
            "Dr.Saeid Farzaneh",
            "Teaching Assistant: Mr.Alireza Atoofi",
            "Developed by َAmirali Khalife"
        ]
        for text in labels:
            lbl = tk.Label(info_frame, text=text, font=("Arial", 14), bg="#1e1e1e", fg="white", justify="center")
            lbl.pack(anchor="center")


        try:
            img = Image.open(LOGO_PATH).resize((120, 120), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            logo_label = tk.Label(frame, image=self.logo_image, bg="#1e1e1e")
            logo_label.pack(pady=15)
        except Exception as e:
            print("Logo error:", e)

        start_btn = ttk.Button(frame, text="Start", command=self.open_main_window)
        start_btn.pack(pady=20)

    def open_main_window(self):
        self.destroy()
        app = SatelliteSelector()
        app.mainloop()

class SatelliteSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Select Satellite")
        self.geometry("600x600")
        self.configure(bg="#121212")

        try:
            bg_img = Image.open(BG_PATH).resize((600, 600), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(bg_img)
            bg_label = tk.Label(self, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception as e:
            print("Background image error:", e)

        main_frame = tk.Frame(self, bg="#121212")
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=550, height=520)

        label = tk.Label(main_frame, text="Select a satellite PRN:", font=("Arial", 14, "bold"),
                         bg="#121212", fg="cyan", justify="center")
        label.pack(pady=10)

        try:
            self.nav_data = Read_rinex(RINEX_PATH)
            prns = sorted(self.nav_data.keys())
        except Exception as e:
            messagebox.showerror("File Error", str(e))
            self.destroy()
            return

        canvas = tk.Canvas(main_frame, bg="#121212", height=430, highlightthickness=0)
        frame = tk.Frame(canvas, bg="#121212")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=frame, anchor='nw')

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        columns = 4
        for i, prn in enumerate(prns):
            row = i // columns
            col = i % columns
            btn = ttk.Button(frame, text=prn, width=12, command=lambda p=prn: self.process_and_plot(p))
            btn.grid(row=row, column=col, padx=5, pady=5)

        total_rows = (len(prns) + columns - 1) // columns
        ttk.Button(frame, text="Plot All Satellites", command=self.plot_all).grid(row=total_rows + 1,
                                                                                  column=0, columnspan=columns, pady=20)

    def process_and_plot(self, prn):
        try:
            process_prn(RINEX_PATH, prn)
            messagebox.showinfo("Success", f"Path for {prn} plotted and CSV saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_all(self):
        try:
            plot_all_paths(self.nav_data)
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = IntroPage()
    app.mainloop()


print("this line was added for GIT test")