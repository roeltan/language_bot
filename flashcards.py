# Placeholder for flashcards
# TODO replace with actual database to store flashcards and user status
import pandas as pd

languages = ["french", "japanese"]

decks: dict[str, dict[str, str]] = {}
for language in languages:
    file = f"vocabulary/{language}.csv"
    df = pd.read_csv(file)
    english_vocab = list(df[df.columns[0]])
    target_vocab = list(df[df.columns[1]])
    deck = dict(zip(english_vocab, target_vocab))
    decks[language] = deck