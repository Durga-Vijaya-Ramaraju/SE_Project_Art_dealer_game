import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import threading
import time

import pygame

# Initialize pygame mixer
pygame.mixer.init()



suits = ["hearts", "diamonds", "spades", "clubs"]
values = list(range(1, 14))

suit_symbols = {
    "hearts": "♥",
    "diamonds": "♦",
    "spades": "♠",
    "clubs": "♣"
}
suit_colors = {
    "hearts": "red",
    "diamonds": "red",
    "spades": "black",
    "clubs": "black"
}

k2_patterns = [
    "All red", "All black", "All hearts", "All diamonds",
    "All spades", "All clubs", "All queens"
]

grade_3_5_extras = [
    "All single-digit primes",
    "Cards add to 9",
    "Ace and a black jack"
]

grade_6_8_extras = [
    "All face cards",
    "Pair",
    "Two pairs",
    "Three of a kind",
    "Straight",
    "Flush",
    "Full house"
]

def all_patterns():
    return {
        "K–2": k2_patterns,
        "3–5": k2_patterns + grade_3_5_extras,
        "6–8": k2_patterns + grade_3_5_extras + grade_6_8_extras
    }

def create_deck():
    return [{"value": v, "suit": s} for v in values for s in suits]

def card_matches(card, pattern):
    if pattern == "All red":
        return suit_colors[card["suit"]] == "red"
    elif pattern == "All black":
        return suit_colors[card["suit"]] == "black"
    elif pattern.startswith("All ") and pattern.split()[1] in suits:
        return card["suit"] == pattern.split()[1]
    elif pattern == "All queens":
        return card["value"] == 12
    elif pattern == "All single-digit primes":
        return card["value"] in [2, 3, 5, 7]
    elif pattern == "All face cards":
        return card["value"] in [11, 12, 13]
    return False

def group_matches(cards, pattern):
    vals = [card["value"] for card in cards]
    suits_only = [card["suit"] for card in cards]
    counts = {v: vals.count(v) for v in set(vals)}
    sorted_vals = sorted(set(min(v, 14) for v in vals))


    if pattern in k2_patterns or pattern in grade_3_5_extras or pattern == "All face cards":
        return all(card_matches(card, pattern) for card in cards)

    if pattern in k2_patterns or pattern in grade_3_5_extras or pattern == "All face cards":
        return all(card_matches(card, pattern) for card in cards)
    elif pattern == "Cards add to 9":
        return sum(min(v, 10) for v in vals) == 9
    elif pattern == "Ace and a black jack":
        return 1 in vals and any(card["value"] == 11 and suit_colors[card["suit"]] == "black" for card in cards)
    elif pattern == "Pair":
        return 2 in counts.values()
    elif pattern == "Two pairs":
        return list(counts.values()).count(2) == 2
    elif pattern == "Three of a kind":
        return 3 in counts.values()
    elif pattern == "Straight":
        return len(vals) == 4 and max(sorted_vals) - min(sorted_vals) == 3 and len(set(vals)) == 4
    elif pattern == "Flush":
        return len(set(suits_only)) == 1
    elif pattern == "Full house":
        return sorted(counts.values()) == [2, 3]
    return False

   

class ArtDealerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Art Dealer Game")
        self.root.configure(bg="#e6f2ff")
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.selected_cards = []
        self.guess_attempts = 0
        self.grade_level = tk.StringVar(value="K–2")
        self.pattern_sets = all_patterns()
        self.pattern_list = self.pattern_sets[self.grade_level.get()]
        self.dealer_pattern = random.choice(self.pattern_list)


        # Load sounds
        self.win_sound = pygame.mixer.Sound("win.mp3")
        self.lost_sound = pygame.mixer.Sound("lost.mp3")

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.root, text="Art Dealer Game", font=("Helvetica", 22, "bold"), bg="#e6f2ff", fg="#003366")
        title.pack(pady=10)

        grade_frame = tk.Frame(self.root, bg="#e6f2ff")
        grade_frame.pack(pady=5)

        tk.Label(grade_frame, text="Select Grade Level:", font=("Helvetica", 13), bg="#e6f2ff").pack(side=tk.LEFT)
        grade_menu = tk.OptionMenu(grade_frame, self.grade_level, *self.pattern_sets.keys(), command=self.set_grade_level)
        grade_menu.config(font=("Helvetica", 12), bg="#cce0ff")
        grade_menu.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.root, text="Pick 4 cards to sell as art!", font=("Helvetica", 16, "bold"), bg="#e6f2ff")
        self.info_label.pack(pady=10)

        self.card_frame = tk.Frame(self.root, bg="#e6f2ff")
        self.card_frame.pack()

        self.card_buttons = []
        self.display_deck()

        self.check_button = tk.Button(self.root, text="Check with Dealer", command=self.check_cards, font=("Helvetica", 12, "bold"), bg="#4caf50", fg="white")
        self.check_button.pack(pady=10)

        self.guess_frame = tk.Frame(self.root, bg="#e6f2ff")
        self.guess_frame.pack(pady=10)

        tk.Label(self.guess_frame, text="Guess Dealer's Pattern:", font=("Helvetica", 13), bg="#e6f2ff").pack(side=tk.LEFT, padx=5)
        self.guess_var = tk.StringVar(value=self.pattern_list[0])
        self.guess_menu = tk.OptionMenu(self.guess_frame, self.guess_var, *self.pattern_list)
        self.guess_menu.config(width=25, font=("Helvetica", 12), bg="#cce0ff")
        self.guess_menu.pack(side=tk.LEFT, padx=5)

        self.guess_button = tk.Button(self.guess_frame, text="Submit Guess", font=("Helvetica", 12, "bold"), bg="#2196f3", fg="white", command=self.submit_guess)
        self.guess_button.pack(side=tk.LEFT, padx=5)

        self.result_label = tk.Label(self.root, text="", font=("Helvetica", 13), bg="#e6f2ff")
        self.result_label.pack(pady=10)

        self.selected_frame = tk.Frame(self.root, bg="#e6f2ff")
        self.selected_frame.pack(pady=10)
        self.selected_label = tk.Label(self.selected_frame, text="Selected Cards:", font=("Helvetica", 13, "underline"), bg="#e6f2ff")
        self.selected_label.grid(row=0, column=0, columnspan=4, pady=(0, 5))
        self.selected_card_labels = []
        tk.Button(self.root, text="Exit", font=("Helvetica", 12, "bold"), bg="#f44336", fg="white",
                  command=self.root.quit).pack(pady=10)

    def set_grade_level(self, grade):
        self.pattern_list = self.pattern_sets[grade]
        self.dealer_pattern = random.choice(self.pattern_list)
        self.guess_var.set(self.pattern_list[0])

        self.guess_menu["menu"].delete(0, "end")
        for pattern in self.pattern_list:
            self.guess_menu["menu"].add_command(label=pattern, command=tk._setit(self.guess_var, pattern))

        self.reset_game()

    def get_card_name(self, value):
        names = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        return names.get(value, str(value))

    def display_deck(self):
        for widget in self.card_frame.winfo_children():
            widget.destroy()
        self.card_buttons.clear()

        for i, card in enumerate(self.deck[:52]):
            text = f"{self.get_card_name(card['value'])} {suit_symbols[card['suit']]}"
            btn = tk.Button(self.card_frame, text=text, width=6, height=2,
                            font=("Helvetica", 9, "bold"),
                            bg="white",
                            fg=suit_colors[card['suit']],
                            relief=tk.RAISED,
                            command=lambda i=i: self.select_card(i))
            btn.grid(row=i // 13, column=i % 13, padx=6, pady=6)
            self.card_buttons.append(btn)

    def select_card(self, index):
        if len(self.selected_cards) >= 4:
            return
        card = self.deck[index]
        if card not in self.selected_cards:
            self.selected_cards.append(card)
            self.card_buttons[index].config(relief=tk.SUNKEN, bg="#f0f0f0")
            self.update_selected_display()

    def update_selected_display(self):
        for label in self.selected_card_labels:
            label.destroy()
        self.selected_card_labels.clear()

        for i, card in enumerate(self.selected_cards):
            text = f"{self.get_card_name(card['value'])} {suit_symbols[card['suit']]}"
            lbl = tk.Label(self.selected_frame, text=text, width=8, font=("Helvetica", 12, "bold"),
                           fg=suit_colors[card["suit"]], bg="white", relief=tk.SOLID, borderwidth=1)
            lbl.grid(row=1, column=i, padx=6, pady=4)
            self.selected_card_labels.append(lbl)

    def check_cards(self):
        if len(self.selected_cards) != 4:
            messagebox.showinfo("Info", "Please select 4 cards.")
            return

        
        match = group_matches(self.selected_cards, self.dealer_pattern)
        match_count = sum(card_matches(card, self.dealer_pattern) for card in self.selected_cards)
        if match:
            self.result_label.config(text=f"Dealer bought ALL 4 cards!")
        else:
            self.result_label.config(text=f"Dealer bought {match_count} out of 4 cards.")

        self.selected_cards.clear()
        self.update_selected_display()
        self.display_deck()

    def animate_balloons(self):
        top = tk.Toplevel(self.root)
        top.title("You Won!")
        canvas = tk.Canvas(top, width=400, height=400, bg="skyblue")
        canvas.pack()
        balloon_img = Image.open("balloon.png")
        balloon = ImageTk.PhotoImage(balloon_img.resize((60, 80)))
        canvas.balloon = balloon

        canvas.create_text(200, 40, text="You Won!", font=("Helvetica", 20, "bold"), fill="darkblue")

        balloons = [canvas.create_image(x * 80 + 40, 400, image=balloon) for x in range(5)]

        def move_up():
            for _ in range(60):
                for b in balloons:
                    canvas.move(b, 0, -5)
                top.update()
                time.sleep(0.05)
            top.after(2000, top.destroy)

        threading.Thread(target=move_up).start()

    def show_lose_image(self):
        top = tk.Toplevel(self.root)
        top.title("Game Over")
        canvas = tk.Canvas(top, width=400, height=400, bg="gray90")
        canvas.pack()

        sad_img = Image.open("gameover.png")
        sad_face = ImageTk.PhotoImage(sad_img.resize((60, 80)))
        canvas.sad_face = sad_face

        canvas.create_text(200, 40, text="Game Over!", font=("Helvetica", 20, "bold"), fill="darkred")
        faces = [canvas.create_image(x * 80 + 40, 400, image=sad_face) for x in range(5)]

        def move_up():
            for _ in range(60):
                for f in faces:
                    canvas.move(f, 0, -5)
                canvas.update()
                time.sleep(0.05)


            self.root.after(2000, top.destroy)

        threading.Thread(target=move_up).start(
        self.root.wait_window(top)

    def submit_guess(self):
        guess = self.guess_var.get()
        if guess == self.dealer_pattern:
            self.win_sound.play()
            
            self.animate_balloons()
            self.reset_game()
        else:
            self.guess_attempts += 1
            tries_left = 3 - self.guess_attempts
            if self.guess_attempts >= 3:
                self.lost_sound.play()
                self.show_lose_image()
                messagebox.showinfo("Game Over", f"Out of guesses! The pattern was: {self.dealer_pattern}")
                self.reset_game()
            else:
                messagebox.showinfo("Oops!", f"Wrong guess. {tries_left} tries left.")

    def reset_game(self):
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.dealer_pattern = random.choice(self.pattern_list)
        self.selected_cards.clear()
        self.guess_attempts = 0
        self.result_label.config(text="")
        self.update_selected_display()
        self.display_deck()
        self.guess_var.set(self.pattern_list[0])

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("850x800")
    game = ArtDealerGame(root)
    root.mainloop()
