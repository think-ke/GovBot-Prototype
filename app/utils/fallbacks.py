"""
Standardized fallback and escalation messages for multilingual support.
"""
from typing import Optional


def get_no_answer_message(language: Optional[str] = None) -> str:
    """Return a standardized no-answer message in the desired language.

    Supported language codes:
    - 'sw' or 'kiswahili': Kiswahili
    - 'sheng': Sheng (fallbacks to Kiswahili with a clarification request)
    - default: English
    """
    lang = (language or "").strip().lower()
    if lang in {"sw", "kiswahili"}:
        return (
            "Samahani, siwezi kupata taarifa husika katika vyanzo vyetu rasmi kwa sasa. "
            "Jaribu kuuliza kwa maneno tofauti au bainisha taasisi ya serikali unayomaanisha. "
            "Ikiwa tatizo litaendelea, unaweza kuwasiliana na afisa wa msaada wa eCitizen."
        )
    if lang == "sheng":
        return (
            "Pole, sijaona info inayofit kwa swali lako kwa sasa. "
            "Tafadhali jaribu kuuliza kwa Kiswahili au eleza idara ya serikali unataka. "
            "Ukitaka msaada wa binadamu, taja tu ‘agent’."
        )
    # default English
    return (
        "Sorry, I couldn’t find a reliable answer from our official sources. "
        "Please try rephrasing or specify the relevant government agency. "
        "If you need human help, say ‘agent’."
    )


def get_out_of_scope_message(bot_name: str = "GovBot", language: Optional[str] = None) -> str:
    """Return a standardized out-of-scope message.
    """
    lang = (language or "").strip().lower()
    if lang in {"sw", "kiswahili"}:
        return (
            f"Mimi ni {bot_name}, na nimesanifiwa kusaidia masuala ya huduma za serikali na miundombinu ya kidijitali. "
            "Siwezi kusaidia mada zisizo za serikali. Unaweza kuuliza swali kuhusu huduma za serikali?"
        )
    if lang == "sheng":
        return (
            f"Mimi ni {bot_name}. Niko kwa mambo ya huduma za serikali pekee. "
            "Uliza swali la government tafadhali."
        )
    return (
        f"I’m {bot_name}. I’m specialized in government services and digital public infrastructure. "
        "I can’t help with unrelated topics. Please ask about government services."
    )


def get_escalation_note(language: Optional[str] = None) -> str:
    """Return a short escalation note for unresolved cases."""
    lang = (language or "").strip().lower()
    if lang in {"sw", "kiswahili"}:
        return "Ukihitaji msaada wa binadamu, sema ‘agent’ au wasiliana kupitia eCitizen."
    if lang == "sheng":
        return "Ukitaka kuongea na mtu, sema ‘agent’ ama tumia eCitizen."
    return "If you need human assistance, say ‘agent’ or use eCitizen support."


def get_pii_warning(language: Optional[str] = None) -> str:
    """Return a standardized PII safety warning message."""
    lang = (language or "").strip().lower()
    if lang in {"sw", "kiswahili"}:
        return (
            "Tafadhali usishiriki taarifa nyeti kama nambari ya kitambulisho, nambari ya simu, barua pepe, au taarifa za kifedha. "
            "Nitaendeleza mazungumzo bila kuhifadhi au kurudia PII.")
    if lang == "sheng":
        return (
            "Usiweke details zako kama ID, namba ya simu, email, au mambo ya pesa hapa. "
            "Tutaendelea bila kuhifadhi au kurudia hizo details.")
    return (
        "Please don’t share sensitive personal details like ID numbers, phone numbers, emails, or financial info. "
        "I’ll continue without storing or repeating PII.")
