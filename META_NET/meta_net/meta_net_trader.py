class MetaNetTrader:
    """Base structure for Meta-Net trading system."""

    def __init__(self, R, C, F, M):
        """Initialize network parameters.

        Args:
            R (float): sensitivity parameter.
            C (float): precision parameter.
            F (float): false positives rate.
            M (float): missing data rate.
        """
        self.R = R
        self.C = C
        self.F = F
        self.M = M
        self.pesi = []
        self._input = []

    def calcola_pesi(self, indicatori):
        """Calcola i pesi adattivi per gli indicatori di trading.

        Args:
            indicatori (list[float]): valori numerici dei classificatori
                sottostanti.

        Returns:
            list[float]: pesi calcolati per ogni indicatore.
        """
        denominatore = (1 + self.F) * (1 + self.M)
        self.pesi = [
            (self.R * self.C * valore) / denominatore for valore in indicatori
        ]
        return self.pesi

    def input_segnali(self, segnali):
        """Converti i segnali textual in valori numerici.

        Args:
            segnali (dict[str, str]): mappa nome indicatore -> segnale
                ("buy", "sell" o "hold").

        Returns:
            list[int]: lista dei segnali convertiti nell'ordine di inserimento.
        """
        mapping = {"buy": 1, "hold": 0, "sell": -1}
        self._input = [mapping.get(v, 0) for v in segnali.values()]
        return self._input

    def genera_segnale(self):
        """Combina i segnali numerici per produrre l'indicazione finale.

        Gli input devono essere caricati tramite :meth:`input_segnali`. Ad ogni
        invocazione i pesi vengono ricalcolati e il punteggio aggregato è usato
        per decidere se comprare, vendere o restare in posizione.

        Returns:
            str: ``"buy"``, ``"sell"`` oppure ``"hold"``.
        """
        if not self._input:
            raise ValueError("Nessun segnale di input fornito")

        if not all(isinstance(v, (int, float)) for v in self._input):
            raise TypeError("I segnali devono essere valori numerici")

        # Calcola i pesi a partire dagli input correnti
        self.calcola_pesi(self._input)

        score = sum(p * v for p, v in zip(self.pesi, self._input))

        if score > 0.3:
            return "buy"
        if score < -0.3:
            return "sell"
        return "hold"

    def backtest(self, giorni=30, num_indicatori=3):
        """Esegue un semplice backtest con dati di prezzo fittizi.

        Genera una serie di prezzi randomizzati e, per ciascun giorno,
        produce segnali casuali dai classificatori sottostanti che vengono
        combinati dalla Meta-Net. Il metodo confronta il rendimento, sia in
        valore assoluto sia in percentuale, con una strategia buy-and-hold sul
        medesimo periodo.

        Args:
            giorni (int): numero di giorni del backtest.
            num_indicatori (int): numero di classificatori sottostanti.
        """
        import random

        prezzi = [100.0]
        for _ in range(giorni):
            variazione = random.uniform(-0.02, 0.02)
            prezzi.append(prezzi[-1] * (1 + variazione))

        indicatori = [random.random() for _ in range(num_indicatori)]
        self.calcola_pesi(indicatori)

        segnali_meta = []
        posizione = False
        cassa = 0.0

        for prezzo in prezzi[1:]:
            raw_signals = random.choices(['buy', 'sell', 'hold'], k=num_indicatori)
            segnali_clf = {f'clf_{i}': s for i, s in enumerate(raw_signals)}
            self.input_segnali(segnali_clf)
            segnale = self.genera_segnale()
            segnali_meta.append(segnale)

            if segnale == 'buy' and not posizione:
                cassa -= prezzo
                posizione = True
            elif segnale == 'sell' and posizione:
                cassa += prezzo
                posizione = False

        if posizione:
            cassa += prezzi[-1]

        rendimento_bh = prezzi[-1] - prezzi[0]
        perc_meta = cassa / prezzi[0] * 100
        perc_bh = rendimento_bh / prezzi[0] * 100

        print("Segnali generati:", segnali_meta)
        print(
            f"Rendimento Meta-Net: {cassa:.2f} ({perc_meta:.2f}% )"
        )
        print(
            f"Rendimento Buy&Hold: {rendimento_bh:.2f} ({perc_bh:.2f}% )"
        )
