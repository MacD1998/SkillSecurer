"""
Riparazione del JSON prodotto dagli LLM.
========================================
Gli agenti (red, blue, judge) chiedono tutti una risposta in JSON e incontrano
tutti lo stesso guasto: il modello mette dentro una stringa del codice con
backslash che JSON non ammette. Qui vive la correzione condivisa.

Ogni agente mantiene invece il PROPRIO recupero per-campo (red_agent._recover_fields,
judge_agent._recover_fields): recuperano schemi diversi — injection_text/line_num
contro executed/evidence/notes — e unificarli produrrebbe un'astrazione finta.
"""
import re

# Scansione a due alternative, in quest'ordine:
#   1. una escape JSON VALIDA (\" \\ \/ \b \f \n \r \t \uXXXX) → consumata INTERA
#   2. un backslash isolato qualsiasi                          → da raddoppiare
#
# L'ordine e la consumazione atomica sono il punto. La versione precedente usava
# un lookahead negativo — re.sub(r'\\(?!["\\/bfnrtu])', ...) — che corrompeva i
# backslash già escapati correttamente: su `\\` il primo backslash non matcha
# (il lookahead vede il secondo), ma poi la scansione avanza di UNA posizione e
# il SECONDO backslash matcha (seguito da spazio) e viene raddoppiato. Risultato
# `\\\`, che rompe json.loads su un input che era valido in quel punto. Qui
# l'alternativa 1 consuma entrambi i caratteri, quindi il secondo non viene mai
# riesaminato.
_ESCAPE_SCAN = re.compile(r'\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4})|\\')


def sanitize_escapes(s: str) -> str:
    r"""Raddoppia i backslash isolati che non fanno parte di una escape JSON valida.

    Serve perché gli LLM inseriscono nelle stringhe codice con backslash grezzi —
    regex (``\d``, ``\.``), path Windows (``C:\Users``) — che fanno fallire
    json.loads con "Invalid \escape". Raddoppiandoli il valore diventa JSON
    valido e, una volta parsato, torna al testo originale.

    Un backslash invalido viene riparato:

        >>> sanitize_escapes(r'{"re": "\d+"}')
        '{"re": "\\\\d+"}'

    Una escape legittima resta intatta, quindi una stringa già corretta non viene
    alterata — backslash già raddoppiato compreso:

        >>> sanitize_escapes(r'{"s": "riga\ndopo"}')
        '{"s": "riga\\ndopo"}'
        >>> sanitize_escapes(r'{"s": "backslash \\ vero"}')
        '{"s": "backslash \\\\ vero"}'

    ATTENZIONE (limite intrinseco, non aggirabile qui): un path Windows come
    ``C:\temp`` contiene ``\t``, che è una escape JSON *valida*. Viene quindi
    preservato e json.loads lo interpreta come TAB, non come i due caratteri
    letterali. Lo stesso vale per ``\n \r \b \f`` e per ``\uXXXX``. La riparazione
    può solo salvare i backslash che JSON rifiuterebbe del tutto; dove la sequenza
    è ambigua, vince la lettura JSON.
    """
    # NB: con una FUNZIONE di sostituzione re.sub non interpreta le escape nel
    # valore restituito (a differenza di un template stringa). Qui servono due
    # backslash letterali, quindi r'\\' — non r'\\\\', che ne produrrebbe quattro.
    return _ESCAPE_SCAN.sub(
        lambda m: m.group(0) if len(m.group(0)) > 1 else r'\\', s)
