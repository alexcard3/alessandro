import sqlite3


class StrOneApp:
    """Application class for STR_ONE."""

    def init_db(self):
        """Initialize the SQLite database and create the qa table."""
        conn = sqlite3.connect("str_one.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domanda TEXT,
                risposta TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def inserisci_dati(self):
        """Prompt the user for a question and answer and save them to the database."""
        domanda = input("Inserisci la domanda: ")
        risposta = input("Inserisci la risposta: ")
        conn = sqlite3.connect("str_one.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO qa (domanda, risposta) VALUES (?, ?)",
            (domanda, risposta),
        )
        conn.commit()
        conn.close()

    def cerca(self, keyword):
        """Search the qa table for a keyword in domanda or risposta."""
        conn = sqlite3.connect("str_one.db")
        cursor = conn.cursor()
        pattern = f"%{keyword}%"
        cursor.execute(
            "SELECT domanda, risposta FROM qa WHERE domanda LIKE ? OR risposta LIKE ?",
            (pattern, pattern),
        )
        results = cursor.fetchall()
        if results:
            for domanda, risposta in results:
                print(f"Domanda: {domanda} - Risposta: {risposta}")
        else:
            print("Nessun risultato trovato")
        conn.close()

    def run(self):
        self.init_db()
        self.inserisci_dati()
        print("Dati salvati correttamente")
        scelta = input("Vuoi fare una ricerca? (S/N): ")
        if scelta.strip().lower() == "s":
            keyword = input("Keyword: ")
            self.cerca(keyword)
        else:
            print("Operazione terminata")
