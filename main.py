# main.py
from ttkbootstrap import Window
from ui.vista_tareas import VistaTareas

def main():
    app = Window(themename="cosmo")
    app.title("Compromisos OCT - ISL")
    app.geometry("1400x800")

    vista = VistaTareas(app)
    vista.pack(fill="both", expand=True)

    app.mainloop()

if __name__ == "__main__":
    main()




