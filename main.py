import scripts.gui as g

def main():

    gui = g.GUI()
    while gui.running:
        gui.current_scene.__displayScene__()

if __name__ == "__main__":
    main()